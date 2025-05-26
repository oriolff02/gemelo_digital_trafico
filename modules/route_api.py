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
    st.write(f"Inicio: {start_coords}, Fin: {end_coords}")
    st.write(f"Coordenadas para ORS: {coordinates}")
    
    # Configurar parámetros de la solicitud
    params = {
        "coordinates": coordinates,
        "instructions": "true",
        "preference": "fastest",
        "units": "km",
        "language": "es",
        "geometry": "true"
    }
    
    # Si hay incidentes, añadir áreas a evitar
    if incidents_df is not None and not incidents_df.empty:
        # Código para añadir áreas a evitar (dejar como estaba)
        pass
    
    try:
        st.write(f"URL: {ORS_DIRECTIONS_ENDPOINT}")
        st.write(f"Parámetros: {json.dumps(params, indent=2)}")
        
        response = requests.post(ORS_DIRECTIONS_ENDPOINT, json=params, headers=headers)
        st.write(f"Código de respuesta: {response.status_code}")
        
        response.raise_for_status()
        
        route_data = response.json()
        st.write(f"Claves de respuesta: {list(route_data.keys())}")
        
        return route_data
    
    except requests.exceptions.RequestException as e:
        st.error(f"Error al calcular la ruta: {e}")
        return None

def generate_mock_route_data(start_coords, end_coords):
    """
    Genera datos simulados de ruta para desarrollo o cuando la API no está disponible.
    
    Args:
        start_coords (tuple): Coordenadas de inicio (lat, lon)
        end_coords (tuple): Coordenadas de destino (lat, lon)
        
    Returns:
        dict: Datos simulados de ruta en formato GeoJSON
    """
    # Convertir a formato [lon, lat]
    start = [start_coords[1], start_coords[0]]
    end = [end_coords[1], end_coords[0]]
    
    # Generar puntos intermedios simples para simular una ruta
    # En un caso real, estos puntos vendrían de la API
    intermediate_points = []
    
    # Calcular puntos intermedios simples (interpolación lineal)
    steps = 15  # Número de puntos intermedios
    for i in range(1, steps):
        fraction = i / steps
        lon = start[0] + (end[0] - start[0]) * fraction
        lat = start[1] + (end[1] - start[1]) * fraction
        intermediate_points.append([lon, lat])
    
    # Generar todos los puntos de la ruta
    route_points = [start] + intermediate_points + [end]
    
    # Crear objeto GeoJSON simulado
    route_data = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": route_points
                },
                "properties": {
                    "segments": [
                        {
                            "distance": 1.2,  # km
                            "duration": 420,  # segundos
                            "steps": [
                                {
                                    "instruction": "Sal hacia el oeste",
                                    "distance": 0.3,
                                    "duration": 90
                                },
                                {
                                    "instruction": "Gira a la derecha",
                                    "distance": 0.4,
                                    "duration": 120
                                },
                                {
                                    "instruction": "Continúa recto",
                                    "distance": 0.5,
                                    "duration": 180
                                },
                                {
                                    "instruction": "Has llegado a tu destino",
                                    "distance": 0,
                                    "duration": 0
                                }
                            ]
                        }
                    ],
                    "summary": {
                        "distance": 1.2,
                        "duration": 420
                    }
                }
            }
        ]
    }
    
    return route_data