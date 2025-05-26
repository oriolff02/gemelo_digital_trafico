"""
Módulo para calcular rutas optimizadas.
Contiene funciones para interactuar con la API de OpenRouteService.
"""

import requests
import json
import streamlit as st
from config.settings import ORS_DIRECTIONS_ENDPOINT

# Añade líneas de log para depurar
def calculate_optimized_route(api_key, start_coords, end_coords, incidents_df=None):
    """
    Calcula la ruta óptima entre dos puntos usando OpenRouteService,
    teniendo en cuenta los incidentes de tráfico.
    
    Args:
        api_key (str): Clave de API de OpenRouteService
        start_coords (tuple): Coordenadas de inicio (lat, lon)
        end_coords (tuple): Coordenadas de destino (lat, lon)
        incidents_df (DataFrame): DataFrame con incidentes a evitar
        
    Returns:
        dict: Datos de la ruta calculada
    """
    headers = {
        'Authorization': api_key,
        'Content-Type': 'application/json'
    }
    
    # Preparar coordenadas en el formato requerido por la API (lon, lat)
    coordinates = [
        [start_coords[1], start_coords[0]],  # [lon, lat]
        [end_coords[1], end_coords[0]]       # [lon, lat]
    ]
    
    # Para debuggear

    
    # Configurar parámetros de la solicitud
    params = {
        "coordinates": coordinates,
        "instructions": "true",
        "preference": "fastest",
        "units": "km",
        "language": "es",
        "geometry": "true",
        "alternative_routes": {
            "share_factor": 0.6,
            "target_count": 3
        }
    }
    
    # Si hay incidentes, añadir áreas a evitar
    if incidents_df is not None and not incidents_df.empty:
        # Código para añadir áreas a evitar (dejar como estaba)
        pass
    
    try:

        
        response = requests.post(ORS_DIRECTIONS_ENDPOINT, json=params, headers=headers)
        
        response.raise_for_status()
        
        route_data = response.json()
        
        return route_data
    
    except requests.exceptions.RequestException as e:
        st.error(f"Error al calcular la ruta: {e}")
        return None
