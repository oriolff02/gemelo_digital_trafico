"""
Módulo para visualización de datos de tráfico.
Contiene funciones para crear mapas interactivos y visualizaciones.
"""

import folium
from folium.plugins import MarkerCluster, HeatMap
import pandas as pd
from config.settings import CITY_CENTER, INCIDENT_CATEGORIES, MUNICIPALITY_NAME
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

def add_incidents_to_map(m, incidents_df):
    """
    Añade incidentes de tráfico al mapa.
    
    Args:
        m (folium.Map): Mapa base
        incidents_df (DataFrame): DataFrame con incidentes
        
    Returns:
        folium.Map: Mapa con incidentes añadidos
    """
    if incidents_df.empty:
        return m
    
    # Crear un grupo de marcadores por cluster
    incidents_cluster = MarkerCluster(name="Incidentes de tráfico").add_to(m)
    
    # Añadir marcadores para cada incidente
    for _, incident in incidents_df.iterrows():
        if pd.notna(incident['latitud']) and pd.notna(incident['longitud']):
            # Determinar color según categoría
            category = incident['categoria']
            category_info = INCIDENT_CATEGORIES.get(category, INCIDENT_CATEGORIES['OTHER'])
            color = category_info['color']
            icon_name = category_info['icon']
            
            # Crear HTML para el popup con información detallada
            popup_html = f"""
            <div style="width: 250px">
                <h4>{incident['tipo']} - {category_info['name']}</h4>
                <b>Descripción:</b> {incident['descripcion']}<br>
                <b>Vías afectadas:</b> {incident['vias_afectadas']}<br>
                <b>Retraso:</b> {int(incident['retraso_segundos']/60)} minutos<br>
                <b>Longitud:</b> {incident['longitud_metros']/1000:.2f} km<br>
                <b>Inicio:</b> {incident['hora_inicio'].strftime('%H:%M') if not pd.isna(incident['hora_inicio']) else 'N/A'}<br>
                <b>Fin estimado:</b> {incident['hora_fin'].strftime('%H:%M') if not pd.isna(incident['hora_fin']) else 'N/A'}<br>
            </div>
            """
            
            # Añadir marcador al cluster
            folium.Marker(
                location=[incident['latitud'], incident['longitud']],
                popup=folium.Popup(popup_html, max_width=300),
                icon=folium.Icon(color=color, icon=icon_name),
                tooltip=f"{incident['tipo']}: {incident['descripcion'][:30]}..."
            ).add_to(incidents_cluster)
            
            # Dibujar la geometría del incidente (si hay múltiples puntos)
            if 'coordenadas' in incident and len(incident['coordenadas']) > 1:
                coordinates = [(lat, lon) for lat, lon in incident['coordenadas']]
                folium.PolyLine(
                    coordinates,
                    color=color,
                    weight=5,
                    opacity=0.7,
                    tooltip=incident['descripcion'][:50]
                ).add_to(m)
    
    # Añadir mapa de calor si hay suficientes datos
    if len(incidents_df) >= 3:
        heat_data = [[row['latitud'], row['longitud']] for _, row in incidents_df.iterrows() 
                     if pd.notna(row['latitud']) and pd.notna(row['longitud'])]
        
        HeatMap(heat_data, radius=15, blur=10, name="Concentración de incidentes").add_to(m)
    
    # Añadir controles de capas
    #folium.LayerControl().add_to(m)
    
    return m

def add_route_to_map(m, route_data, color='blue', name='Ruta optimizada'):
    """
    Añade una ruta calculada al mapa existente.
    
    Args:
        m (folium.Map): Mapa base
        route_data (dict): Datos de la ruta de OpenRouteService
        color (str): Color de la ruta
        name (str): Nombre de la capa de la ruta
        
    Returns:
        folium.Map: Mapa con la ruta añadida
    """
    import logging
    
    try:
        # Detectar formato de respuesta
        if 'features' in route_data:
            # Formato antiguo o simulado
            route_geometry = route_data['features'][0]['geometry']['coordinates']
            route_props = route_data['features'][0]['properties']
            segments = route_props.get('segments', [{}])[0]
            
            # Convertir coordenadas de [lon, lat] a [lat, lon] para Folium
            route_points = [[lat, lon] for lon, lat in route_geometry]
            
        elif 'routes' in route_data:
            # Formato de la API OpenRouteService v2
            route = route_data['routes'][0]
            
            # Extraer la geometría que puede estar en formato codificado
            if 'geometry' in route:
                geometry = route['geometry']
                
                # Si la geometría es una cadena, es un polyline codificado
                if isinstance(geometry, str):
                    try:
                        import polyline
                        # Decodificar el polyline (formato Google, no GeoJSON)
                        decoded_points = polyline.decode(geometry)
                        # Los puntos ya vienen en formato [lat, lon]
                        route_points = decoded_points
                        logging.info(f"Ruta decodificada: {len(route_points)} puntos")
                    except ImportError:
                        logging.error("Se requiere la biblioteca 'polyline' para decodificar la geometría")
                        
                        # Plan B: Usar extremos del bbox para una línea recta
                        bbox = route_data.get('bbox', [])
                        if len(bbox) >= 4:
                            route_points = [
                                [bbox[1], bbox[0]],  # [lat, lon] del punto mínimo
                                [bbox[3], bbox[2]]   # [lat, lon] del punto máximo
                            ]
                        else:
                            return m  # No podemos mostrar la ruta
                
                # Si la geometría es un diccionario con coordenadas, en formato GeoJSON
                elif isinstance(geometry, dict) and 'coordinates' in geometry:
                    # Convertir coordenadas de [lon, lat] a [lat, lon] para Folium
                    route_points = [[lat, lon] for lon, lat in geometry['coordinates']]
                else:
                    logging.warning(f"Formato de geometría desconocido: {type(geometry)}")
                    return m
            else:
                logging.warning("No se encontró la geometría en la ruta")
                return m
            
            # Extraer información de segmentos
            if 'segments' in route and route['segments']:
                segments = route['segments'][0]
            else:
                segments = {
                    'duration': route['summary'].get('duration', 0),
                    'distance': route['summary'].get('distance', 0),
                    'steps': []
                }
        else:
            logging.warning("Formato de datos de ruta no reconocido")
            return m
        
        # Crear capa para la ruta
        route_layer = folium.FeatureGroup(name=name)
        
        # Mostrar detalles de la ruta para debug
        logging.info(f"Puntos de ruta: {route_points[:2]}...{route_points[-2:]} (total: {len(route_points)})")
        
        # Calcular tiempo y distancia
        duration_minutes = round(segments.get('duration', 0) / 60, 1)
        distance_km = round(segments.get('distance', 0), 2)
        

        # Añadir línea de la ruta al mapa
        folium.PolyLine(
            route_points,
            color=color,
            weight=5,
            opacity=0.7,
            tooltip=f"{name}: {distance_km} km, {duration_minutes} min"
        ).add_to(route_layer)
        
        # Añadir marcadores para inicio y fin
        if len(route_points) > 1:
            # Inicio
            folium.Marker(
                route_points[0],
                icon=folium.Icon(color='green', icon='play'),
                tooltip='Inicio'
            ).add_to(route_layer)
            
            # Fin
            folium.Marker(
                route_points[-1],
                icon=folium.Icon(color='red', icon='stop'),
                tooltip='Destino'
            ).add_to(route_layer)
            
            # Añadir popup con resumen en el punto medio
            mid_point_idx = len(route_points) // 2
            mid_point = route_points[mid_point_idx]
            
            # Extraer y formar instrucciones
            steps = segments.get('steps', [])
            instructions_html = ""
            
            for step in steps:
                instruction = step.get('instruction', '')
                distance = round(step.get('distance', 0), 2)
                duration = round(step.get('duration', 0) / 60, 1)
                
                if instruction:
                    instructions_html += f"<li>{instruction} ({distance} km, {duration} min)</li>"
            
            # Popup HTML
            popup_html = f"""
            <div style="width: 300px">
                <h3>Resumen de la ruta</h3>
                <b>Distancia total:</b> {distance_km} km<br>
                <b>Tiempo estimado:</b> {duration_minutes} minutos<br>
                <hr>
                <h4>Instrucciones:</h4>
                <ol>
                    {instructions_html}
                </ol>
            </div>
            """
            
            folium.Popup(popup_html, max_width=350).add_to(
                folium.Marker(
                    mid_point,
                    icon=folium.Icon(color=color, icon='info-sign')
                ).add_to(route_layer)
            )
        
        # Añadir capa al mapa
        route_layer.add_to(m)
        
    except Exception as e:
        import traceback
        logging.error(f"Error al añadir ruta al mapa: {e}")
        logging.error(traceback.format_exc())
    
    return m