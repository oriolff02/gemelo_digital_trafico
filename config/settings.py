"""
Configuraciones para el Gemelo Digital de Tráfico Urbano.
Contiene constantes, configuraciones y valores predeterminados.
"""

# Configuración de APIs (usar variables de entorno en producción)
ORS_API_KEY = "5b3ce3597851110001cf6248c5f5de61991b4c0ba5448d48d832b32d"  # Reemplazar con tu clave o usar environ

# Endpoints de TomTom

# Endpoints de OpenRouteService
ORS_DIRECTIONS_ENDPOINT = "https://api.openrouteservice.org/v2/directions/driving-car"

MUNICIPALITY_NAME = "Barcelona"
CITY_CENTER = [41.3874, 2.1686]
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
    "Torre Glòries": (41.4033, 2.1896),
    "Diagonal Mar": (41.4106, 2.2186),
    "Forum": (41.4097, 2.2293),
    "Hospital de Sant Pau": (41.4122, 2.1740),
    "Universitat de Barcelona": (41.3868, 2.1651),
    "Passeig de Gràcia": (41.3917, 2.1650),
    "Parc de la Ciutadella": (41.3887, 2.1901),
    "El Born": (41.3846, 2.1837),
    "La Rambla": (41.3809, 2.1730),
    "Gràcia": (41.4030, 2.1561),
    "Clot": (41.4102, 2.1873),
    "Sant Andreu": (41.4361, 2.1894),
    "Nou Barris": (41.4416, 2.1777),
    "Les Corts": (41.3859, 2.1357),
    "Sarrià": (41.4001, 2.1218),
    "Horta": (41.4300, 2.1672),
    "Poble-sec": (41.3734, 2.1613),
    "Poble Nou": (41.4031, 2.1999),
    "Vallcarca": (41.4142, 2.1481),
    "Sant Gervasi": (41.3992, 2.1392),
    "El Raval": (41.3800, 2.1699),
    "Zona Universitaria": (41.3818, 2.1202),
    "Glòries": (41.4035, 2.1884),
    "Sants": (41.3801, 2.1400),
    "Tres Torres": (41.3991, 2.1303),
    "Sant Martí": (41.4098, 2.2037),
    "La Sagrera": (41.4214, 2.1867),
    "La Vila Olímpica": (41.3909, 2.1992),
    "Trinitat Vella": (41.4410, 2.1975),
    "Bon Pastor": (41.4365, 2.1980),
    "Vall d'Hebron": (41.4338, 2.1486),
    "Pedralbes": (41.3914, 2.1161)
}

CACHE_DIR = ".cache"