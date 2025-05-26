"""
Módulo para interactuar con APIs de tráfico.
Contiene funciones para obtener y procesar datos de incidentes de tráfico.
"""

import requests
import pandas as pd
import json
import os
import time
from datetime import datetime, timedelta
import streamlit as st
from config.settings import TOMTOM_INCIDENTS_ENDPOINT, CACHE_DIR, CACHE_TTL, BBOX

def get_traffic_incidents(api_key, bbox=BBOX, use_cache=True):
    """
    Obtiene incidentes de tráfico para Sant Adrià del Besòs desde TomTom API.
    
    Args:
        api_key (str): Clave de API de TomTom
        bbox (str): Bounding box para delimitar el área (formato: minLon,minLat,maxLon,maxLat)
        use_cache (bool): Si se debe usar datos en caché cuando estén disponibles
        
    Returns:
        DataFrame: Datos de incidentes procesados
    """
    # Comprobar si existe caché y si podemos usarla
    os.makedirs(CACHE_DIR, exist_ok=True)
    cache_file = f"{CACHE_DIR}/incidents_cache.json"
    
    if use_cache and os.path.exists(cache_file):
        try:
            with open(cache_file, "r") as f:
                cache_data = json.load(f)
                # Verificar si el caché es reciente (menos de CACHE_TTL segundos)
                if time.time() - cache_data.get("timestamp", 0) < CACHE_TTL:
                    st.toast("Usando datos en caché", icon="ℹ️")
                    # Reconstruir DataFrame desde caché
                    df = pd.DataFrame(cache_data["incidents"])
                    # Convertir fechas de nuevo
                    if 'hora_inicio' in df.columns and not df.empty:
                        df['hora_inicio'] = pd.to_datetime(df['hora_inicio'], format='ISO8601')
                    if 'hora_fin' in df.columns and not df.empty:
                        df['hora_fin'] = pd.to_datetime(df['hora_fin'], format='ISO8601')
                    return df
        except (json.JSONDecodeError, KeyError) as e:
            st.warning(f"Problema con el caché, realizando nueva petición: {e}")
            pass  # Si hay problemas con el caché, seguimos y hacemos la petición real
    
    # Parámetros para la petición a la API de TomTom
    params = {
        "bbox": bbox,
        "key": api_key,
        "language": "es-ES",
        "timeValidityFilter": "present"
    }
    
    try:
        response = requests.get(TOMTOM_INCIDENTS_ENDPOINT, params=params)
        response.raise_for_status()
        
        data = response.json()
        
        if 'incidents' not in data:
            st.warning("No se encontraron incidentes en la zona.")
            return pd.DataFrame()
        
        # Convertir a DataFrame para facilitar el análisis
        # En modules/traffic_api.py, actualiza el procesamiento de datos:

        # Convertir a DataFrame para facilitar el análisis
        # Convertir a DataFrame para facilitar el análisis
        category_map = {
            0: "Desconocido",
            1: "Accidente",
            2: "Niebla",
            3: "Condiciones peligrosas",
            4: "Lluvia",
            5: "Hielo",
            6: "Congestión",
            7: "Carril cerrado",
            8: "Vía cerrada",
            9: "Obras",
            10: "Viento",
            11: "Inundación",
            14: "Vehículo averiado"
        }

        incidents = []
        for incident in data['incidents']:
            properties = incident.get('properties', {})
            category_num = properties.get('iconCategory', 0)
            tipo = category_map.get(category_num, f"Desconocido ({category_num})")
            geometry = incident.get('geometry', {})
            coordinates = []
            if geometry.get('type') == 'LineString':
                coordinates = [(coord[1], coord[0]) for coord in geometry.get('coordinates', [])]
            if not coordinates:
                continue

            incidents.append({
                'tipo': tipo,
                'categoria': tipo,
                'coordenadas': coordinates,
                'latitud': coordinates[0][0] if coordinates else None,
                'longitud': coordinates[0][1] if coordinates else None
            })

        df = pd.DataFrame(incidents)
        
        # Guardar en caché para futuras consultas
        # Guardar en caché para futuras consultas
        try:
            # Convertir el DataFrame a un diccionario, pero convertir fechas a cadenas ISO
            incidents_dict = []
            for record in df.to_dict(orient='records'):
                # Crear una copia del registro para no modificar el original
                record_copy = record.copy()
                
                # Convertir objetos Timestamp a cadenas
                if 'hora_inicio' in record_copy and record_copy['hora_inicio'] is not None:
                    if isinstance(record_copy['hora_inicio'], (pd.Timestamp, datetime)):
                        record_copy['hora_inicio'] = record_copy['hora_inicio'].isoformat()
                
                if 'hora_fin' in record_copy and record_copy['hora_fin'] is not None:
                    if isinstance(record_copy['hora_fin'], (pd.Timestamp, datetime)):
                        record_copy['hora_fin'] = record_copy['hora_fin'].isoformat()
                
                # Convertir las coordenadas a formato serializable
                if 'coordenadas' in record_copy and record_copy['coordenadas'] is not None:
                    record_copy['coordenadas'] = [[float(lat), float(lon)] for lat, lon in record_copy['coordenadas']]
                
                incidents_dict.append(record_copy)
            
            cache_data = {
                "timestamp": time.time(),
                "incidents": incidents_dict
            }
            
            with open(cache_file, "w") as f:
                json.dump(cache_data, f)
                
        except Exception as e:
            st.warning(f"No se pudo guardar la caché: {e}")
        
        return df
    
    except requests.exceptions.RequestException as e:
        st.error(f"Error al obtener datos de TomTom: {e}")
        return pd.DataFrame()

def generate_mock_traffic_data():
    """
    Genera datos simulados de tráfico para desarrollo o cuando la API no está disponible.
    
    Returns:
        DataFrame: Datos simulados de incidentes de tráfico
    """
    now = datetime.now()
    
    # Datos de ejemplo para simular incidentes de tráfico
    incidents = [
        {
            'tipo': 'CONGESTION',
            'categoria': 'CONGESTION',
            'descripcion': 'Congestión en hora punta',
            'vias_afectadas': 'C-31',
            'retraso_segundos': 320,
            'longitud_metros': 800,
            'hora_inicio': now - pd.Timedelta(hours=1),
            'hora_fin': now + pd.Timedelta(hours=2),
            'latitud': 41.4252,
            'longitud': 2.2245,
            'coordenadas': [(41.4252, 2.2245), (41.4255, 2.2250), (41.4260, 2.2255)]
        },
        {
            'tipo': 'ACCIDENT',
            'categoria': 'ACCIDENT',
            'descripcion': 'Accidente con 2 vehículos',
            'vias_afectadas': 'Av. Catalunya',
            'retraso_segundos': 600,
            'longitud_metros': 300,
            'hora_inicio': now - pd.Timedelta(minutes=30),
            'hora_fin': now + pd.Timedelta(hours=1),
            'latitud': 41.4261,
            'longitud': 2.2200,
            'coordenadas': [(41.4261, 2.2200), (41.4265, 2.2205)]
        },
        {
            'tipo': 'CONSTRUCTION',
            'categoria': 'CONSTRUCTION',
            'descripcion': 'Obras en la calzada',
            'vias_afectadas': 'C/ Eduard Maristany',
            'retraso_segundos': 450,
            'longitud_metros': 500,
            'hora_inicio': now - pd.Timedelta(days=2),
            'hora_fin': now + pd.Timedelta(days=5),
            'latitud': 41.4207,
            'longitud': 2.2270,
            'coordenadas': [(41.4207, 2.2270), (41.4210, 2.2275), (41.4215, 2.2280)]
        },
        {
            'tipo': 'LANE_RESTRICTION',
            'categoria': 'LANE_RESTRICTION',
            'descripcion': 'Carril cerrado por mantenimiento',
            'vias_afectadas': 'Av. Pi i Margall',
            'retraso_segundos': 180,
            'longitud_metros': 200,
            'hora_inicio': now - pd.Timedelta(hours=4),
            'hora_fin': now + pd.Timedelta(hours=8),
            'latitud': 41.4183,
            'longitud': 2.2348,
            'coordenadas': [(41.4183, 2.2348), (41.4186, 2.2350)]
        },
        {
            'tipo': 'WEATHER',
            'categoria': 'WEATHER',
            'descripcion': 'Pavimento deslizante por lluvia',
            'vias_afectadas': 'Ronda Litoral',
            'retraso_segundos': 150,
            'longitud_metros': 1200,
            'hora_inicio': now - pd.Timedelta(minutes=90),
            'hora_fin': now + pd.Timedelta(hours=3),
            'latitud': 41.4195,
            'longitud': 2.2300,
            'coordenadas': [(41.4195, 2.2300), (41.4200, 2.2310), (41.4205, 2.2320)]
        }
    ]
    
    return pd.DataFrame(incidents)