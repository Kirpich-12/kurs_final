import os
import webbrowser
import pandas as pd
import folium
from folium.plugins import HeatMap
import numpy as np
from folium.plugins import MarkerCluster
from parser import Parser



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

    def load(self):
        ...
    
    def


    def __del__(self):
        print('Goodbye')