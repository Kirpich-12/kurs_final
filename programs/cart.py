"""
heatmap_usd.py — интерактивная карта точек обмена c heatmap и цветными маркерами

Запуск:
    python heatmap_usd.py

После запуска:
    откройте generated_heatmap.html
"""

import os
import webbrowser
import pandas as pd
import folium
from folium.plugins import HeatMap
import numpy as np
from folium.plugins import MarkerCluster


# ----------- НАСТРОЙКИ -------------

CITY_NAME = "Минск"
CITY_CENTER = (53.904, 27.5616)
START_ZOOM = 12

CSV_FILE = "usd_rates.csv"

# --- Импорт парсера твоего сайта ---
from parser import Parser


# ----------- ФУНКЦИИ -------------

def load_or_parse():
    """Загружаем CSV, если он есть — иначе парсим"""
    if os.path.exists(CSV_FILE):
        print(f"[INFO] Загружаем данные из {CSV_FILE}")
        df = pd.read_csv(CSV_FILE)
    else:
        print("[INFO] CSV нет — выполняем парсинг")
        par = Parser('https://myfin.by/currency/usd', True)
        data = par.get_usd()  # ans = [address, sell, buy, (lat, lon)]

        df = pd.DataFrame([
            {
                "address": rec[0],
                "sell_course": float(rec[1]),
                "buy_course": float(rec[2]),
                "lat": float(rec[3][0]),
                "lon": float(rec[3][1])
            }
            for rec in data
        ])

        df.to_csv(CSV_FILE, index=False, encoding="utf-8")
        print(f"[INFO] Сохранено в {CSV_FILE}")

    return df


def compute_weight(df):
    """Вес: чем ниже курс — тем больше влияние"""
    df["weight_raw"] = 1 / df["sell_course"]

    # нормализация 0..1 + усиление разницы (gamma)
    min_w, max_w = df["weight_raw"].min(), df["weight_raw"].max()
    df["weight"] = (df["weight_raw"] - min_w) / (max_w - min_w + 1e-6)
    df["weight"] = df["weight"] ** 2.5  # усиливаем даже маленькие отличия

    return df


def get_color(course, min_c, max_c):
    """Зелёный = лучший курс, красный = худший"""
    norm = (course - min_c) / (max_c - min_c + 1e-6)

    # gamma — чтобы 0.05 разница была видна
    norm = norm ** 2

    if norm < 0.33:
        return "green"
    elif norm < 0.66:
        return "orange"
    return "red"


# ----------- ОСНОВНОЙ КОД -------------

df = load_or_parse()
df = compute_weight(df)

print(df.head())

m = folium.Map(location=CITY_CENTER, zoom_start=START_ZOOM)

# --- Heatmap ---
heat_data = df[["lat", "lon", "weight"]].values.tolist()

HeatMap(
    heat_data,
    radius=15,
    blur=12,
    min_opacity=0.25,
    max_zoom=17
).add_to(m)

# --- Маркеры ---
min_c = df["sell_course"].min()
max_c = df["sell_course"].max()

cluster = MarkerCluster(
    disableClusteringAtZoom=15,   # при приближении точки снова будут раздельно
    spiderfyOnMaxZoom=True,
    zoomToBoundsOnClick=True,
    showCoverageOnHover=False
).add_to(m)

min_c = df["sell_course"].min()
max_c = df["sell_course"].max()

for _, row in df.iterrows():
    color = get_color(row["sell_course"], min_c, max_c)

    popup = f"""
    <b>{row['address']}</b><br>
    ✅ Покупка: {row['buy_course']}<br>
    💲 Продажа: <b>{row['sell_course']}</b><br>
    """

    folium.CircleMarker(
        location=[row["lat"], row["lon"]],
        radius=8,
        color=color,
        fill=True,
        fill_opacity=0.88,
        weight=2,
        popup=folium.Popup(popup, max_width=300),
    ).add_to(cluster)


# --- Лучший курс (звезда) ---
best = df.loc[df["sell_course"].idxmin()]

folium.Marker(
    location=[best["lat"], best["lon"]],
    icon=folium.Icon(color="green", icon="star", prefix="fa"),
    popup=f"🔥 <b>ЛУЧШИЙ КУРС</b><br>{best['sell_course']}<br>{best['address']}"
).add_to(m)

# --- Сохраняем ---
OUT = "generated_heatmap.html"
m.save(OUT)
print(f"[OK] Карта сохранена: {OUT}")

try:
    webbrowser.open('file://' + os.path.realpath(OUT))
except:
    pass
