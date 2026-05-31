"""
Interactive map of exchange points with heatmap and colored markers

Usage:
    from cart2 import ExchangeMap
    
    map_builder = ExchangeMap("branches.csv")
    map_builder.build()
    map_builder.save_and_open("generated_heatmap.html")
"""

import os
import json
import webbrowser
import pandas as pd
import folium
from folium.plugins import HeatMap
from folium.plugins import MarkerCluster


class DataLoader:
    """Handles data loading from branches CSV"""
    
    def __init__(self, csv_file: str):
        self.csv_file = csv_file
    
    def load(self) -> pd.DataFrame:
        """Load and process CSV data"""
        if not os.path.exists(self.csv_file):
            raise FileNotFoundError(f"CSV file not found: {self.csv_file}")
        
        print(f"[INFO] Loading data from {self.csv_file}")
        df = pd.read_csv(self.csv_file)
        
        return self._process_data(df)
    
    def _process_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Parse coordinates and exchange rates from CSV"""
        processed = []
        
        for _, row in df.iterrows():
            try:
                lat, lon = map(float, row['coords'].split(','))
                rates = json.loads(row['exchange_rates'])
                
                buy_rate = None
                sell_rate = None
                for rate_obj in rates:
                    if rate_obj['curr_from'] == 'usd' and rate_obj['curr_to'] == 'byn':
                        buy_rate = float(rate_obj['rate'])
                    elif rate_obj['curr_from'] == 'byn' and rate_obj['curr_to'] == 'usd':
                        sell_rate = float(rate_obj['rate'])
                
                if buy_rate is None or sell_rate is None:
                    continue
                
                processed.append({
                    'address': row['address'],
                    'bank_name': row['bank_org'],
                    'buy_course': buy_rate,
                    'sell_course': sell_rate,
                    'lat': lat,
                    'lon': lon
                })
            except Exception as e:
                print(f"[WARNING] Skipped row: {e}")
                continue
        
        result_df = pd.DataFrame(processed)
        print(f"[INFO] Processed {len(result_df)} locations")
        return result_df


class DataProcessor:
    """Handles data transformations and calculations"""
    
    @staticmethod
    def compute_weight(df: pd.DataFrame) -> pd.DataFrame:
        """Calculate weight: lower rate = higher influence"""
        df_copy = df.copy()
        df_copy["weight_raw"] = 1 / df_copy["buy_course"]

        min_w, max_w = df_copy["weight_raw"].min(), df_copy["weight_raw"].max()
        df_copy["weight"] = (df_copy["weight_raw"] - min_w) / (max_w - min_w + 1e-6)
        df_copy["weight"] = df_copy["weight"] ** 2.5

        return df_copy
    
    @staticmethod
    def get_color(course: float, min_c: float, max_c: float) -> str:
        """Return color based on rate: green = best, red = worst"""
        norm = (course - min_c) / (max_c - min_c + 1e-6)
        norm = norm ** 2

        if norm < 0.33:
            return "green"
        elif norm < 0.66:
            return "orange"
        return "red"


class MapBuilder:
    """Builds folium map with all layers"""
    
    def __init__(self, center: tuple, zoom: int):
        self.center = center
        self.zoom = zoom
        self.map = folium.Map(location=center, zoom_start=zoom)
    
    def add_heatmap(self, df: pd.DataFrame) -> "MapBuilder":
        """Add heatmap layer"""
        heat_data = df[["lat", "lon", "weight"]].values.tolist()
        HeatMap(
            heat_data,
            radius=15,
            blur=12,
            min_opacity=0.25,
            max_zoom=17
        ).add_to(self.map)
        return self
    
    def add_markers(self, df: pd.DataFrame) -> "MapBuilder":
        """Add clustered markers with rate-based colors"""
        cluster = MarkerCluster(
            disableClusteringAtZoom=15,
            spiderfyOnMaxZoom=True,
            zoomToBoundsOnClick=True,
            showCoverageOnHover=False
        ).add_to(self.map)

        min_c = df["buy_course"].min()
        max_c = df["buy_course"].max()

        for _, row in df.iterrows():
            color = DataProcessor.get_color(row["buy_course"], min_c, max_c)
            popup = self._create_popup(row)

            folium.CircleMarker(
                location=[row["lat"], row["lon"]],
                radius=8,
                color=color,
                fill=True,
                fill_opacity=0.88,
                weight=2,
                popup=folium.Popup(popup, max_width=300),
            ).add_to(cluster)
        
        return self
    
    def add_best_rate_marker(self, df: pd.DataFrame) -> "MapBuilder":
        """Add star marker for best rate"""
        best = df.loc[df["buy_course"].idxmin()]
        popup = f"🔥 <b>BEST RATE</b><br><b>{best['bank_name']}</b><br>{best['buy_course']}<br>{best['address']}"

        folium.Marker(
            location=[best["lat"], best["lon"]],
            icon=folium.Icon(color="green", icon="star", prefix="fa"),
            popup=popup
        ).add_to(self.map)
        
        return self
    
    def save(self, filename: str) -> str:
        """Save map to HTML file"""
        self.map.save(filename)
        print(f"[OK] Map saved: {filename}")
        return filename
    
    @staticmethod
    def _create_popup(row) -> str:
        """Create popup HTML for a marker"""
        return f"""
        <b>{row['bank_name']}</b><br>
        <b>{row['address']}</b><br>
            Buy rate: {row['buy_course']}<br>
            Sell rate: {row['sell_course']}<br>
        """


class ExchangeMap:
    """Main class for creating interactive exchange rate map"""
    
    def __init__(self, csv_file: str = "branches.csv", 
                 city_center: tuple = (53.904, 27.5616), 
                 zoom: int = 12):
        self.csv_file = csv_file
        self.city_center = city_center
        self.zoom = zoom
        self.df = None
        
        self.data_loader = DataLoader(csv_file)
        self.map_builder = MapBuilder(city_center, zoom)
    
    def build(self) -> "ExchangeMap":
        """Build complete map with all layers"""
        self.df = self.data_loader.load()
        self.df = DataProcessor.compute_weight(self.df)
        
        print(self.df.head())
        
        self.map_builder.add_heatmap(self.df)
        self.map_builder.add_markers(self.df)
        self.map_builder.add_best_rate_marker(self.df)
        
        return self
    
    def save_and_open(self, filename: str = "generated_heatmap.html") -> None:
        """Save map and open in browser"""
        filepath = self.map_builder.save(filename)
        
        try:
            webbrowser.open('file://' + os.path.realpath(filepath))
        except Exception as e:
            print(f"[WARNING] Could not open browser: {e}")


if __name__ == "__main__":
    map_builder = ExchangeMap(r"C:\System\Codelab\PyLab\kurs_final\kurs_final\programs\branches.csv")
    map_builder.build()
    map_builder.save_and_open()