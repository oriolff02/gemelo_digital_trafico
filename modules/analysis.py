"""
Módulo para análisis de datos de tráfico.
Contiene funciones para analizar y generar estadísticas de datos de tráfico.
"""

import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from config.settings import INCIDENT_CATEGORIES

def generate_incident_summary(incidents_df):
    """
    Genera un resumen de incidentes de tráfico.
    
    Args:
        incidents_df (DataFrame): DataFrame con incidentes
        
    Returns:
        dict: Diccionario con estadísticas de resumen
    """
    if incidents_df.empty:
        return {
            "total_incidents": 0,
            "by_type": {},
        }
    
    # Total de incidentes
    total_incidents = len(incidents_df)
    
    # Incidentes por tipo
    by_type = incidents_df['tipo'].value_counts().to_dict()
    
    return {
        "total_incidents": total_incidents,
        "by_type": by_type,
    }

def plot_incidents_by_type(incidents_df):
    """
    Crea una gráfica de barras de incidentes por tipo.
    
    Args:
        incidents_df (DataFrame): DataFrame con incidentes
        
    Returns:
        fig: Figura de matplotlib
    """
    if incidents_df.empty:
        # Crear figura vacía con mensaje
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.text(0.5, 0.5, "No hay datos disponibles", 
                ha='center', va='center', fontsize=14)
        ax.set_axis_off()
        return fig
    
    # Contar incidentes por tipo
    type_counts = incidents_df['tipo'].value_counts().reset_index()
    type_counts.columns = ['tipo', 'count']
    
    # Añadir colores según la categoría
    colors = [INCIDENT_CATEGORIES.get(t, {"color": "gray"})["color"] 
              for t in type_counts['tipo']]
    
    # Crear gráfico
    fig, ax = plt.subplots(figsize=(8, 4))
    bars = ax.bar(type_counts['tipo'], type_counts['count'], color=colors)
    
    # Añadir etiquetas
    ax.set_title('Incidentes por tipo')
    ax.set_xlabel('Tipo de incidente')
    ax.set_ylabel('Número de incidentes')
    
    # Añadir valores sobre las barras
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                f'{int(height)}', ha='center', va='bottom')
    
    plt.tight_layout()
    
    return fig

def analyze_route_impact(route_data, incidents_df):
    """
    Analiza el impacto de incidentes en una ruta calculada.
    
    Args:
        route_data (dict): Datos de la ruta calculada
        incidents_df (DataFrame): DataFrame con incidentes
        
    Returns:
        dict: Análisis de impacto de la ruta
    """
    if not route_data or 'features' not in route_data or incidents_df.empty:
        return {
            "affected_by_incidents": False,
            "total_incidents_nearby": 0,
        }
    
    # Extraer coordenadas de la ruta
    route_geometry = route_data['features'][0]['geometry']['coordinates']
    route_points = [(lat, lon) for lon, lat in route_geometry]
    
    # Función para calcular distancia entre puntos (en km, aproximada)
    def haversine_distance(point1, point2):
        from math import radians, cos, sin, asin, sqrt
        lat1, lon1 = point1
        lat2, lon2 = point2
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        r = 6371  # km
        return c * r
    
    # Encontrar incidentes cercanos a la ruta (<0.5 km)
    nearby_incidents = []
    threshold_distance = 0.5  # km
    for _, incident in incidents_df.iterrows():
        if pd.notna(incident['latitud']) and pd.notna(incident['longitud']):
            incident_point = (incident['latitud'], incident['longitud'])
            min_distance = min(
                haversine_distance(incident_point, route_point)
                for route_point in route_points
            )
            if min_distance < threshold_distance:
                nearby_incidents.append({
                    'tipo': incident['tipo'],
                })
    
    total_nearby = len(nearby_incidents)
    
    return {
        "affected_by_incidents": total_nearby > 0,
        "total_incidents_nearby": total_nearby,
        "incidents": nearby_incidents if total_nearby > 0 else [],
    }
