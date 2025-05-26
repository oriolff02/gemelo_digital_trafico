"""
Servicio de geocoding para determinar distrito y barrio a partir de coordenadas.
"""

import requests
import json
import os
from functools import lru_cache
import logging
from shapely.geometry import Point, shape
from modules.accident_predictor import DISTRICT_NAME_TO_CODE, NEIGHBORHOOD_NAME_TO_CODE

class GeocodingService:
    """
    Servicio para obtener información geográfica de coordenadas.
    Puede usar OpenStreetMap Nominatim o archivos GeoJSON locales.
    """

    def __init__(self, use_online=False):
        """
        Inicializa el servicio de geocoding.

        Args:
            use_online (bool): Si usar servicios online o datos locales
        """
        self.use_online = use_online
        self.cache = {}

        # Si tienes archivos GeoJSON de distritos/barrios, cárgalos aquí
        self.districts_geojson = None
        self.neighborhoods_geojson = None

        # Intentar cargar datos locales si existen
        self._load_local_data()

    def _load_local_data(self):
        """Carga archivos GeoJSON locales si están disponibles"""
        try:
            districts_file = "data/barcelona_districts.geojson"
            neighborhoods_file = "data/barcelona_neighborhoods.geojson"

            if os.path.exists(districts_file):
                with open(districts_file, 'r', encoding='utf-8') as f:
                    self.districts_geojson = json.load(f)
                    logging.info("Datos de distritos cargados")

            if os.path.exists(neighborhoods_file):
                with open(neighborhoods_file, 'r', encoding='utf-8') as f:
                    self.neighborhoods_geojson = json.load(f)
                    logging.info("Datos de barrios cargados")

        except Exception as e:
            logging.warning(f"No se pudieron cargar datos locales: {e}")

    @lru_cache(maxsize=1000)
    def reverse_geocode(self, lat, lon):
        """
        Obtiene información de ubicación a partir de coordenadas.

        Args:
            lat (float): Latitud
            lon (float): Longitud

        Returns:
            dict: Información de ubicación
        """
        # Primero intentar con cache
        cache_key = f"{lat:.6f},{lon:.6f}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        result = {
            'district': None,
            'district_code': None,
            'neighborhood': None,
            'neighborhood_code': None,
            'address': None
        }

        if self.use_online:
            # Usar Nominatim de OpenStreetMap
            try:
                url = f"https://nominatim.openstreetmap.org/reverse"
                params = {
                    'lat': lat,
                    'lon': lon,
                    'format': 'json',
                    'accept-language': 'ca,es',
                    'addressdetails': 1,
                    'extratags': 1
                }
                headers = {
                    'User-Agent': 'DigitalTwinTraffic/1.0'
                }

                response = requests.get(url, params=params, headers=headers, timeout=5)
                response.raise_for_status()

                data = response.json()
                address = data.get('address', {})

                # Extraer distrito y barrio
                district = (
                    address.get('city_district') or 
                    address.get('district') or
                    address.get('suburb')
                )

                neighborhood = (
                    address.get('neighbourhood') or
                    address.get('quarter') or
                    address.get('suburb')
                )

                result['district'] = district
                result['neighborhood'] = neighborhood
                result['address'] = data.get('display_name')

                # ------------------ Mapeo robusto con normalización ------------------
                def normalize_name(name):
                    return (
                        name.lower()
                        .replace("’", "'")
                        .replace("`", "'")
                        .replace("´", "'")
                        .replace(" - ", "-")
                        .replace("–", "-")
                        .strip()
                        if isinstance(name, str) else ""
                    )

                DISTRICT_NAME_TO_CODE_NORM = {normalize_name(k): v for k, v in DISTRICT_NAME_TO_CODE.items()}
                NEIGHBORHOOD_NAME_TO_CODE_NORM = {normalize_name(k): v for k, v in NEIGHBORHOOD_NAME_TO_CODE.items()}

                if district and isinstance(district, str):
                    result['district_code'] = DISTRICT_NAME_TO_CODE_NORM.get(normalize_name(district))
                if neighborhood and isinstance(neighborhood, str):
                    result['neighborhood_code'] = NEIGHBORHOOD_NAME_TO_CODE_NORM.get(normalize_name(neighborhood))
                # ---------------------------------------------------------------------

            except Exception as e:
                logging.warning(f"Error en geocoding online: {e}")
                # Fallback a método offline
                result = self._offline_geocode(lat, lon)
        else:
            # Usar método offline
            result = self._offline_geocode(lat, lon)

        # Guardar en cache
        self.cache[cache_key] = result
        return result

    def _offline_geocode(self, lat, lon):
        """
        Geocoding offline usando polígonos locales o aproximaciones.

        Args:
            lat (float): Latitud
            lon (float): Longitud

        Returns:
            dict: Información de ubicación
        """
        from modules.accident_predictor import DISTRICT_MAPPING, NEIGHBORHOOD_MAPPING

        # Si tenemos datos GeoJSON, usarlos
        if self.districts_geojson or self.neighborhoods_geojson:
            return self._geocode_with_geojson(lat, lon)

        # Si no, usar aproximaciones basadas en coordenadas
        district_code = None
        neighborhood_code = None

        if lat > 41.45:  # Zona norte
            if lon < 2.13:
                district_code = DISTRICT_MAPPING['Nou Barris']
                neighborhood_code = NEIGHBORHOOD_MAPPING.get('Canyelles', 48)
            else:
                district_code = DISTRICT_MAPPING['Sant Andreu']
                neighborhood_code = NEIGHBORHOOD_MAPPING.get('la Sagrera', 60)
        elif lat > 41.42:  # Zona norte-centro
            if lon < 2.14:
                district_code = DISTRICT_MAPPING['Horta-Guinardó']
                neighborhood_code = NEIGHBORHOOD_MAPPING.get('Horta', 42)
            elif lon < 2.16:
                district_code = DISTRICT_MAPPING['Gràcia']
                neighborhood_code = NEIGHBORHOOD_MAPPING.get('Vila de Gràcia', 30)
            else:
                district_code = DISTRICT_MAPPING['Sant Martí']
                neighborhood_code = NEIGHBORHOOD_MAPPING.get('el Clot', 64)
        elif lat > 41.40:  # Zona centro
            if lon < 2.13:
                district_code = DISTRICT_MAPPING['Sarrià-Sant Gervasi']
                neighborhood_code = NEIGHBORHOOD_MAPPING.get('Sarrià', 22)
            elif lon < 2.15:
                district_code = DISTRICT_MAPPING['Les Corts']
                neighborhood_code = NEIGHBORHOOD_MAPPING.get('les Corts', 18)
            elif lon < 2.17:
                district_code = DISTRICT_MAPPING['Eixample']
                neighborhood_code = NEIGHBORHOOD_MAPPING.get('la Dreta de l\'Eixample', 5)
            else:
                district_code = DISTRICT_MAPPING['Sant Martí']
                neighborhood_code = NEIGHBORHOOD_MAPPING.get('el Poblenou', 67)
        elif lat > 41.38:  # Zona centro-sur
            if lon < 2.16:
                district_code = DISTRICT_MAPPING['Sants-Montjuïc']
                neighborhood_code = NEIGHBORHOOD_MAPPING.get('Sants', 17)
            elif lon < 2.18:
                district_code = DISTRICT_MAPPING['Eixample']
                neighborhood_code = NEIGHBORHOOD_MAPPING.get('Sant Antoni', 8)
            else:
                district_code = DISTRICT_MAPPING['Ciutat Vella']
                neighborhood_code = NEIGHBORHOOD_MAPPING.get('el Raval', 1)
        else:  # Zona sur
            if lon < 2.15:
                district_code = DISTRICT_MAPPING['Sants-Montjuïc']
                neighborhood_code = NEIGHBORHOOD_MAPPING.get('el Poble Sec', 11)
            else:
                district_code = DISTRICT_MAPPING['Ciutat Vella']
                neighborhood_code = NEIGHBORHOOD_MAPPING.get('la Barceloneta', 3)

        # Obtener nombres a partir de códigos
        district_name = None
        neighborhood_name = None

        for name, code in DISTRICT_MAPPING.items():
            if code == district_code:
                district_name = name
                break

        for name, code in NEIGHBORHOOD_MAPPING.items():
            if code == neighborhood_code:
                neighborhood_name = name
                break

        return {
            'district': district_name,
            'district_code': district_code,
            'neighborhood': neighborhood_name,
            'neighborhood_code': neighborhood_code,
            'address': f"{neighborhood_name}, {district_name}, Barcelona" if neighborhood_name and district_name else "Barcelona"
        }

    def _geocode_with_geojson(self, lat, lon):
        """
        Geocoding usando archivos GeoJSON locales.

        Args:
            lat (float): Latitud
            lon (float): Longitud

        Returns:
            dict: Información de ubicación
        """

        point = Point(lon, lat)
        result = {
            'district': None,
            'district_code': None,
            'neighborhood': None,
            'neighborhood_code': None,
            'address': None
        }

        # Buscar en distritos
        if self.districts_geojson:
            for feature in self.districts_geojson.get('features', []):
                polygon = shape(feature['geometry'])
                if polygon.contains(point):
                    properties = feature.get('properties', {})
                    result['district'] = properties.get('name')
                    result['district_code'] = properties.get('code')
                    break

        # Buscar en barrios
        if self.neighborhoods_geojson:
            for feature in self.neighborhoods_geojson.get('features', []):
                polygon = shape(feature['geometry'])
                if polygon.contains(point):
                    properties = feature.get('properties', {})
                    result['neighborhood'] = properties.get('name')
                    result['neighborhood_code'] = properties.get('code')
                    break

        # Construir dirección
        parts = []
        if result['neighborhood']:
            parts.append(result['neighborhood'])
        if result['district']:
            parts.append(result['district'])
        parts.append('Barcelona')

        result['address'] = ', '.join(parts)

        return result
