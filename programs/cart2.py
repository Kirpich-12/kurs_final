import os
import webbrowser
import pandas as pd
import folium
from folium.plugins import HeatMap
import numpy as np
from folium.plugins import MarkerCluster
from parser import Parser
from enum import StrEnum
from dataclasses import dataclass




class CartType(StrEnum):
    U

class CourseCart:
    def __init__(self,
                 csv_file:str,
                 action_type:str,
                 cart_type:str
                 ):
        self.csv_file = csv_file
        self.action_type = action_type
        self.cart_type = cart_type
        self.CITY_NAME = "Минск"
        self.START_ZOOM = 12

    def load_or_parse(self):
        """Загружаем CSV, если он есть — иначе парсим"""
        if os.path.exists(self.csv_file):
            print(f"[INFO] Загружаем данные из {self.csv_file}")
            df = pd.read_csv(self.csv_file)
        else:
            print("[INFO] CSV нет — выполняем парсинг")
            par = Parser(True)
            data = par.get_usd()  # ans = [address, sell, buy, (lat, lon)]

            df = pd.DataFrame([
                {
                    "address": rec[0],
                    "bank_name":rec[1],
                    "sell_course": float(rec[2]),
                    "buy_course": float(rec[3]),
                    "lat": float(rec[4][0]),
                    "lon": float(rec[4][1])
                }
                for rec in data
            ])

            df.to_csv(CSV_FILE, index=False, encoding="utf-8")
            print(f"[INFO] Сохранено в {CSV_FILE}")

        return df 


    def __del__(self):
        print('Goodbye')