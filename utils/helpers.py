"""
Utilidades generales para el Gemelo Digital de Tráfico.
"""

import os
import json
from datetime import datetime

def ensure_directory_exists(directory):
    """
    Asegura que un directorio existe, creándolo si es necesario.
    
    Args:
        directory (str): Ruta al directorio
    """
    if not os.path.exists(directory):
        os.makedirs(directory)

def format_time_difference(seconds):
    """
    Formatea una diferencia de tiempo en segundos de forma legible.
    
    Args:
        seconds (float): Segundos a formatear
        
    Returns:
        str: Representación legible
    """
    if seconds < 60:
        return f"{seconds:.0f} segundos"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f} minutos"
    else:
        hours = seconds / 3600
        return f"{hours:.1f} horas"

def format_distance(meters):
    """
    Formatea una distancia en metros de forma legible.
    
    Args:
        meters (float): Metros a formatear
        
    Returns:
        str: Representación legible
    """
    if meters < 1000:
        return f"{meters:.0f} metros"
    else:
        km = meters / 1000
        return f"{km:.2f} km"

def save_to_json(data, filename):
    """
    Guarda datos en un archivo JSON.
    
    Args:
        data: Datos a guardar
        filename (str): Nombre del archivo
    """
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"Error guardando JSON: {e}")
        return False

def load_from_json(filename):
    """
    Carga datos desde un archivo JSON.
    
    Args:
        filename (str): Nombre del archivo
        
    Returns:
        dict: Datos cargados o None si hay error
    """
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error cargando JSON: {e}")
        return None

def get_current_timestamp():
    """
    Obtiene un timestamp formateado para el momento actual.
    
    Returns:
        str: Timestamp en formato YYYY-MM-DD_HH-MM-SS
    """
    return datetime.now().strftime('%Y-%m-%d_%H-%M-%S')