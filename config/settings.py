"""
Configuraciones para el Gemelo Digital de Tráfico Urbano.
Contiene constantes, configuraciones y valores predeterminados.
"""

# Constantes para Barcelona (en lugar de Sant Adrià del Besòs)
MUNICIPALITY_NAME = "Barcelona"
CITY_CENTER = [41.3874, 2.1686]  # [latitud, longitud] - Plaza Catalunya
BBOX = "2.0770,41.3201,2.2299,41.4682"  # [minLon,minLat,maxLon,maxLat] - Cubre toda Barcelona

# Configuración de APIs (usar variables de entorno en producción)
TOMTOM_API_KEY = "7gvBs3RZ4QYQlePvsYtgkOv1cKowSsm4"  # Reemplazar con tu clave o usar environ
ORS_API_KEY = "5b3ce3597851110001cf6248c5f5de61991b4c0ba5448d48d832b32d"  # Reemplazar con tu clave o usar environ

# Endpoints de TomTom
TOMTOM_INCIDENTS_ENDPOINT = "https://api.tomtom.com/traffic/services/5/incidentDetails"

# Endpoints de OpenRouteService
ORS_DIRECTIONS_ENDPOINT = "https://api.openrouteservice.org/v2/directions/driving-car"

# Configuración de caché
CACHE_TTL = 300  # Tiempo de vida de la caché en segundos (5 minutos)
CACHE_DIR = ".cache"

# Lugares predefinidos en Barcelona (para el selector de rutas)
PREDEFINED_LOCATIONS = {
    "Plaza Catalunya": (41.3874, 2.1686),
    "Sagrada Familia": (41.4036, 2.1744),
    "Park Güell": (41.4145, 2.1527),
    "Barceloneta": (41.3804, 2.1896),
    "Camp Nou": (41.3809, 2.1206),
    "Montjuïc": (41.3641, 2.1580),
    "Hospital Clínic": (41.3892, 2.1507),
    "Estación de Sants": (41.3795, 2.1401),
    "Aeropuerto El Prat": (41.2974, 2.0833),
    "Torre Glòries": (41.4033, 2.1896)
}

# Categorías de incidentes para visualización
INCIDENT_CATEGORIES = {
    'ACCIDENT': {'name': 'Accidente', 'color': 'red', 'icon': 'car-crash'},
    'CONGESTION': {'name': 'Congestión', 'color': 'orange', 'icon': 'traffic-cone'},
    'CONSTRUCTION': {'name': 'Obras', 'color': 'yellow', 'icon': 'tools'},
    'CLOSURES': {'name': 'Cierre', 'color': 'black', 'icon': 'road-closed'},
    'LANE_RESTRICTION': {'name': 'Restricción de carril', 'color': 'purple', 'icon': 'lanes'},
    'WEATHER': {'name': 'Clima', 'color': 'blue', 'icon': 'cloud-rain'},
    'OTHER': {'name': 'Otro', 'color': 'gray', 'icon': 'info-sign'}
}

# Mapa de iconCategory numérico a categoría textual
ICON_CATEGORY_MAP = {
    1: "ACCIDENT",
    2: "CONGESTION", 
    3: "CONSTRUCTION",
    4: "CLOSURES",
    5: "LANE_RESTRICTION",
    6: "OTHER",
    7: "WEATHER"
}