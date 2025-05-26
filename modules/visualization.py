"""
Módulo para visualización de datos de tráfico.
Contiene funciones para crear mapas interactivos y visualizaciones.
"""

import folium
from folium.plugins import MarkerCluster, HeatMap
import pandas as pd
from config.settings import CITY_CENTER, MUNICIPALITY_NAME
import streamlit as st


def create_base_map(center=CITY_CENTER, zoom_start=15, width=1000, height=600):
    """
    Crea un mapa base para visualizar datos.
    
    Args:
        center (list): Coordenadas centrales [lat, lon]
        zoom_start (int): Nivel de zoom inicial
        width (int): Ancho del mapa en píxeles
        height (int): Alto del mapa en píxeles
        
    Returns:
        folium.Map: Mapa base
    """
    m = folium.Map(
        location=center,
        zoom_start=zoom_start,
        tiles="CartoDB positron",
        attr='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        width=width,
        height=height
    )
    
    # Añadir título
    title_html = f'''
        <div style="position: fixed; 
                    top: 10px; left: 50px; width: 300px; height: 30px; 
                    background-color: white; border-radius: 5px;
                    border: 2px solid grey; z-index:9999; padding: 6px; 
                    font-size: 14px; font-weight: bold; text-align: center;">
            Gemelo Digital de Tráfico: {MUNICIPALITY_NAME}
        </div>
    '''
    m.get_root().html.add_child(folium.Element(title_html))
    
    return m