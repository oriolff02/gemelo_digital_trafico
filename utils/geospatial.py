"""
Utilidades para operaciones geoespaciales.
"""

import math
import numpy as np

def haversine_distance(point1, point2):
    """
    Calcula la distancia Haversine entre dos puntos en coordenadas geográficas.
    
    Args:
        point1 (tuple): Coordenadas del primer punto (lat, lon)
        point2 (tuple): Coordenadas del segundo punto (lat, lon)
        
    Returns:
        float: Distancia en kilómetros
    """
    lat1, lon1 = point1
    lat2, lon2 = point2
    
    # Convertir grados a radianes
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # Fórmula de Haversine
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    r = 6371  # Radio de la Tierra en km
    
    return c * r

def point_to_line_distance(point, line_start, line_end):
    """
    Calcula la distancia mínima de un punto a una línea definida por dos puntos.
    
    Args:
        point (tuple): Coordenadas del punto (lat, lon)
        line_start (tuple): Coordenadas del inicio de la línea (lat, lon)
        line_end (tuple): Coordenadas del fin de la línea (lat, lon)
        
    Returns:
        float: Distancia mínima en kilómetros
    """
    # Convertir a coordenadas cartesianas para simplificar el cálculo
    # (esto es una aproximación, válida para distancias cortas)
    p = np.array([point[0], point[1]])
    a = np.array([line_start[0], line_start[1]])
    b = np.array([line_end[0], line_end[1]])
    
    # Vector de la línea
    ab = b - a
    
    # Vector desde el inicio de la línea al punto
    ap = p - a
    
    # Proyección escalar de ap sobre ab
    projection = np.dot(ap, ab) / np.dot(ab, ab)
    
    # Si la proyección está fuera del segmento, la distancia es al punto más cercano
    if projection < 0:
        return haversine_distance(point, line_start)
    elif projection > 1:
        return haversine_distance(point, line_end)
    
    # Punto de proyección en la línea
    projection_point = a + projection * ab
    
    # Calcular distancia al punto de proyección
    return haversine_distance(point, (projection_point[0], projection_point[1]))

def buffer_point(point, radius_km):
    """
    Crea un círculo (buffer) alrededor de un punto.
    
    Args:
        point (tuple): Coordenadas del punto (lat, lon)
        radius_km (float): Radio del círculo en kilómetros
        
    Returns:
        list: Lista de puntos que forman el círculo [(lat, lon), ...]
    """
    lat, lon = point
    
    # Convertir radio de km a grados (aproximación)
    # 1 grado de latitud = ~ 111 km
    radius_lat = radius_km / 111.0
    
    # 1 grado de longitud varía con la latitud
    radius_lon = radius_km / (111.0 * math.cos(math.radians(lat)))
    
    # Generar puntos del círculo
    circle_points = []
    for angle in range(0, 360, 10):  # Incrementos de 10 grados
        rad = math.radians(angle)
        new_lat = lat + radius_lat * math.sin(rad)
        new_lon = lon + radius_lon * math.cos(rad)
        circle_points.append((new_lat, new_lon))
    
    # Cerrar el círculo repitiendo el primer punto
    circle_points.append(circle_points[0])
    
    return circle_points