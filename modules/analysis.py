"""
Módulo para análisis de datos de tráfico.
Contiene funciones para analizar y generar estadísticas de datos de tráfico.
"""

import pandas as pd
import numpy as np
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
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
            "avg_delay": 0,
            "affected_roads": []
        }
    
    # Total de incidentes
    total_incidents = len(incidents_df)
    
    # Incidentes por tipo
    by_type = incidents_df['tipo'].value_counts().to_dict()
    
    # Retraso promedio (en minutos)
    avg_delay = incidents_df['retraso_segundos'].mean() / 60
    
    # Vías afectadas
    affected_roads = []
    for roads in incidents_df['vias_afectadas'].dropna():
        affected_roads.extend([r.strip() for r in roads.split(',')])
    affected_roads = list(set([r for r in affected_roads if r]))
    
    # Retraso total (horas-persona)
    total_delay_hours = incidents_df['retraso_segundos'].sum() / 3600
    
    # Incidente más grave (mayor retraso)
    if not incidents_df.empty:
        most_severe = incidents_df.loc[incidents_df['retraso_segundos'].idxmax()]
        most_severe_info = {
            "tipo": most_severe['tipo'],
            "descripcion": most_severe['descripcion'],
            "retraso_minutos": most_severe['retraso_segundos'] / 60,
            "via": most_severe['vias_afectadas']
        }
    else:
        most_severe_info = None
    
    return {
        "total_incidents": total_incidents,
        "by_type": by_type,
        "avg_delay": avg_delay,
        "affected_roads": affected_roads,
        "total_delay_hours": total_delay_hours,
        "most_severe": most_severe_info
    }

def plot_incidents_by_category(incidents_df):
    """
    Crea una gráfica de barras de incidentes por categoría.
    
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
    
    # Contar incidentes por categoría
    category_counts = incidents_df['categoria'].value_counts().reset_index()
    category_counts.columns = ['categoria', 'count']
    
    # Añadir nombres legibles de categorías
    category_counts['nombre'] = category_counts['categoria'].apply(
        lambda x: INCIDENT_CATEGORIES.get(x, INCIDENT_CATEGORIES['OTHER'])['name']
    )
    
    # Añadir colores según la categoría
    colors = [INCIDENT_CATEGORIES.get(cat, INCIDENT_CATEGORIES['OTHER'])['color'] 
              for cat in category_counts['categoria']]
    
    # Crear gráfico
    fig, ax = plt.subplots(figsize=(8, 4))
    bars = ax.bar(category_counts['nombre'], category_counts['count'], color=colors)
    
    # Añadir etiquetas
    ax.set_title('Incidentes por categoría')
    ax.set_xlabel('Categoría')
    ax.set_ylabel('Número de incidentes')
    
    # Añadir valores sobre las barras
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                f'{int(height)}', ha='center', va='bottom')
    
    # Ajustar layout
    plt.tight_layout()
    
    return fig

def plot_delay_by_type(incidents_df):
    """
    Crea una gráfica de barras de retraso promedio por tipo de incidente.
    
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
    
    # Calcular retraso promedio por tipo (en minutos)
    delay_by_type = incidents_df.groupby('tipo')['retraso_segundos'].mean() / 60
    delay_by_type = delay_by_type.reset_index()
    delay_by_type.columns = ['tipo', 'retraso_promedio']
    
    # Crear gráfico
    fig, ax = plt.subplots(figsize=(8, 4))
    bars = ax.bar(delay_by_type['tipo'], delay_by_type['retraso_promedio'])
    
    # Añadir etiquetas
    ax.set_title('Retraso promedio por tipo de incidente')
    ax.set_xlabel('Tipo de incidente')
    ax.set_ylabel('Retraso promedio (minutos)')
    
    # Añadir valores sobre las barras
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                f'{height:.1f}', ha='center', va='bottom')
    
    # Ajustar layout
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
            "estimated_delay": 0,
            "severity": "Sin impacto"
        }
    
    # Extraer coordenadas de la ruta
    route_geometry = route_data['features'][0]['geometry']['coordinates']
    route_points = [(lat, lon) for lon, lat in route_geometry]
    
    # Función para calcular distancia entre puntos (en km, aproximada)
    def haversine_distance(point1, point2):
        """Calcula distancia entre dos puntos en coordenadas (lat, lon)"""
        from math import radians, cos, sin, asin, sqrt
        
        lat1, lon1 = point1
        lat2, lon2 = point2
        
        # Convertir grados a radianes
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        
        # Fórmula de Haversine
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        r = 6371  # Radio de la Tierra en km
        
        return c * r
    
    # Encontrar incidentes cercanos a la ruta (menos de 0.5 km)
    nearby_incidents = []
    threshold_distance = 0.5  # km
    
    for _, incident in incidents_df.iterrows():
        if pd.notna(incident['latitud']) and pd.notna(incident['longitud']):
            incident_point = (incident['latitud'], incident['longitud'])
            
            # Calcular distancia mínima a la ruta
            min_distance = float('inf')
            for route_point in route_points:
                distance = haversine_distance(incident_point, route_point)
                min_distance = min(min_distance, distance)
            
            # Si el incidente está suficientemente cerca, añadirlo
            if min_distance < threshold_distance:
                nearby_incidents.append({
                    'tipo': incident['tipo'],
                    'descripcion': incident['descripcion'],
                    'retraso_segundos': incident['retraso_segundos'],
                    'distancia_ruta_km': min_distance
                })
    
    # Calcular estadísticas
    total_nearby = len(nearby_incidents)
    
    if total_nearby > 0:
        # Estimar retraso adicional (simple, en minutos)
        estimated_delay = sum([inc['retraso_segundos'] for inc in nearby_incidents]) / 60
        
        # Determinar severidad del impacto
        if estimated_delay < 5:
            severity = "Bajo"
        elif estimated_delay < 15:
            severity = "Moderado"
        else:
            severity = "Alto"
        
        return {
            "affected_by_incidents": True,
            "total_incidents_nearby": total_nearby,
            "incidents": nearby_incidents,
            "estimated_delay": estimated_delay,
            "severity": severity
        }
    else:
        return {
            "affected_by_incidents": False,
            "total_incidents_nearby": 0,
            "estimated_delay": 0,
            "severity": "Sin impacto"
        }