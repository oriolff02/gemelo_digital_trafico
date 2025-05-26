"""
Módulo para predicción de accidentes usando modelo XGBoost entrenado.
"""

import joblib
import pandas as pd
import numpy as np
from datetime import datetime
import logging

# Mapeo de distritos de Barcelona a códigos numéricos
DISTRICT_MAPPING = {
    0: "Ciutat Vella",
    2: "Eixample",
    3: "Gràcia",
    4: "Horta-Guinardó",
    5: "Les Corts",
    6: "Nou Barris",
    7: "Sant Andreu",
    8: "Sant Martí",
    9: "Sants-Montjuïc",
    10: "Sarrià-Sant Gervasi"
}

# Mapeo de turnos
TURN_MAPPING = {
    'matí': 1,      # 6:00 - 14:00
    'tarda': 2,     # 14:00 - 22:00
    'nit': 3        # 22:00 - 6:00
}

# Mapeo de días de la semana
WEEKDAY_MAPPING = {
    'Dilluns': 1,
    'Dimarts': 2,
    'Dimecres': 3,
    'Dijous': 4,
    'Divendres': 5,
    'Dissabte': 6,
    'Diumenge': 7
}

# Mapeo de barrios a códigos (ejemplos principales)
NEIGHBORHOOD_MAPPING = {
    0: 'Baró de Viver',
    1: 'Can Baró',
    2: 'Can Peguera',
    3: 'Canyelles',
    4: 'Ciutat Meridiana',
    5: 'Desconegut',
    6: 'Diagonal Mar i el Front Marítim del Poblenou',
    7: 'Horta',
    8: 'Hostafrancs',
    9: 'Montbau',
    10: 'Navas',
    11: 'Pedralbes',
    12: 'Porta',
    13: 'Provençals del Poblenou',
    14: 'Sant Andreu',
    15: 'Sant Antoni',
    16: 'Sant Genís dels Agudells',
    17: 'Sant Gervasi - Galvany',
    18: 'Sant Gervasi - la Bonanova',
    19: 'Sant Martí de Provençals',
    20: 'Sant Pere, Santa Caterina i la Ribera',
    21: 'Sants',
    22: 'Sants - Badal',
    23: 'Sarrià',
    24: 'Torre Baró',
    25: 'Vallbona',
    26: 'Vallcarca i els Penitents',
    27: 'Vallvidrera, el Tibidabo i les Planes',
    28: 'Verdun',
    29: 'Vilapicina i la Torre Llobeta',
    30: 'el Baix Guinardó',
    31: 'el Barri Gòtic',
    32: 'el Besòs i el Maresme',
    33: 'el Bon Pastor',
    34: "el Camp d'en Grassot i Gràcia Nova",
    35: "el Camp de l'Arpa del Clot",
    36: 'el Carmel',
    37: 'el Clot',
    38: 'el Coll',
    39: 'el Congrés i els Indians',
    40: 'el Fort Pienc',
    41: 'el Guinardó',
    42: 'el Parc i la Llacuna del Poblenou',
    43: 'el Poble Sec',
    44: 'el Poble-sec',
    45: 'el Poblenou',
    46: 'el Putxet i el Farró',
    47: 'el Raval',
    48: 'el Turó de la Peira',
    49: "l'Antiga Esquerra de l'Eixample",
    50: 'la Barceloneta',
    51: 'la Bordeta',
    52: 'la Clota',
    53: "la Dreta de l'Eixample",
    54: "la Font d'en Fargues",
    55: 'la Font de la Guatlla',
    56: 'la Guineueta',
    57: 'la Marina de Port',
    58: 'la Marina del Prat Vermell',
    59: 'la Maternitat i Sant Ramon',
    60: 'la Nova Esquerra de l\'Eixample',
    61: 'la Prosperitat',
    62: 'la Sagrada Família',
    63: 'la Sagrera',
    64: 'la Salut',
    65: 'la Teixonera',
    66: 'la Trinitat Nova',
    67: 'la Trinitat Vella',
    68: "la Vall d'Hebron",
    69: 'la Verneda i la Pau',
    70: 'la Vila Olímpica del Poblenou',
    71: 'la Vila de Gràcia',
    72: 'les Corts',
    73: 'les Roquetes',
    74: 'les Tres Torres',
}

DISTRICT_NAME_TO_CODE = {v: k for k, v in DISTRICT_MAPPING.items()}
NEIGHBORHOOD_NAME_TO_CODE = {v: k for k, v in NEIGHBORHOOD_MAPPING.items()}

class AccidentPredictor:
    def __init__(self, model_path='xgboost_model_definitivo.pkl', use_geocoding=True):
        """
        Inicializa el predictor de accidentes.
        
        Args:
            model_path (str): Ruta al archivo del modelo entrenado
            use_geocoding (bool): Si usar servicio de geocoding para mejor precisión
        """
        try:
            self.model = joblib.load(model_path)
            logging.info(f"Modelo cargado correctamente desde {model_path}")
        except Exception as e:
            logging.error(f"Error al cargar el modelo: {e}")
            raise
        
        # Inicializar servicio de geocoding si está habilitado
        self.geocoding_service = None
        if use_geocoding:
            try:
                from modules.geocoding_service import GeocodingService
                self.geocoding_service = GeocodingService(use_online=False)
                logging.info("Servicio de geocoding inicializado")
            except Exception as e:
                logging.warning(f"No se pudo inicializar el servicio de geocoding: {e}")
                self.geocoding_service = None
    
    def get_turn_from_hour(self, hour):
        """
        Determina el turno basado en la hora.
        
        Args:
            hour (int): Hora del día (0-23)
            
        Returns:
            int: Código del turno
        """
        if 6 <= hour < 14:
            return TURN_MAPPING['matí']
        elif 14 <= hour < 22:
            return TURN_MAPPING['tarda']
        else:
            return TURN_MAPPING['nit']
    
    def get_district_from_coordinates(self, lat, lon):
        """
        Determina el distrito basado en las coordenadas.
        
        Args:
            lat (float): Latitud
            lon (float): Longitud
            
        Returns:
            int: Código del distrito
        """
        # Primero intentar con servicio de geocoding si está disponible
        if self.geocoding_service:
            try:
                location_info = self.geocoding_service.reverse_geocode(lat, lon)
                district_name = location_info.get('district')
                if district_name and district_name in DISTRICT_NAME_TO_CODE:
                    return DISTRICT_NAME_TO_CODE[district_name]
            except Exception as e:
                logging.warning(f"Error en geocoding, usando método de respaldo: {e}")
        
        # Implementación simplificada basada en rangos aproximados
        # En producción, usar geocoding reverso o polígonos reales
        
        if lat > 41.42 and lon < 2.15:
            return 6  # Nou Barris
        elif lat > 41.42 and lon > 2.15:
            return 7  # Sant Andreu
        elif lat > 41.40 and lon > 2.18:
            return 8  # Sant Martí
        elif lat > 41.40 and lon < 2.12:
            return 10  # Sarrià-Sant Gervasi
        elif lat < 41.37 and lon < 2.14:
            return 9  # Sants-Montjuïc
        elif 41.38 < lat < 41.40 and 2.16 < lon < 2.18:
            return 2  # Eixample
        elif lat < 41.38 and lon > 2.17:
            return 0  # Ciutat Vella
        else:
            return 2  # Eixample por defecto
    
    def get_neighborhood_from_coordinates(self, lat, lon):
        """
        Determina el barrio basado en las coordenadas.
        
        Args:
            lat (float): Latitud
            lon (float): Longitud
            
        Returns:
            int: Código del barrio
        """
        # Primero intentar con servicio de geocoding si está disponible
        if self.geocoding_service:
            try:
                location_info = self.geocoding_service.reverse_geocode(lat, lon)
                neighborhood_name = location_info.get('neighborhood')
                if neighborhood_name and neighborhood_name in NEIGHBORHOOD_NAME_TO_CODE:
                    return NEIGHBORHOOD_NAME_TO_CODE[neighborhood_name]
            except Exception as e:
                logging.warning(f"Error en geocoding, usando método de respaldo: {e}")
        
        # Implementación muy simplificada
        # En producción, usar geocoding reverso
        
        # Algunos ejemplos de barrios conocidos por coordenadas aproximadas
        if 41.403 < lat < 41.405 and 2.173 < lon < 2.175:
            return NEIGHBORHOOD_NAME_TO_CODE['la Sagrada Família']
        elif 41.386 < lat < 41.388 and 2.167 < lon < 2.170:
            return NEIGHBORHOOD_NAME_TO_CODE["la Dreta de l'Eixample"]
        elif 41.379 < lat < 41.382 and 2.188 < lon < 2.191:
            return NEIGHBORHOOD_NAME_TO_CODE['la Barceloneta']
        else:
            district = self.get_district_from_coordinates(lat, lon)
            if district == DISTRICT_NAME_TO_CODE['Eixample']:
                return NEIGHBORHOOD_NAME_TO_CODE["la Dreta de l'Eixample"]
            elif district == DISTRICT_NAME_TO_CODE['Ciutat Vella']:
                return NEIGHBORHOOD_NAME_TO_CODE["el Raval"]
            else:
                return 30  # el Baix Guinardó como default

    
    def predict_segment_risk(self, lat, lon, datetime_obj):
        """
        Predice el riesgo de accidente para un segmento específico.
        
        Args:
            lat (float): Latitud del segmento
            lon (float): Longitud del segmento
            datetime_obj (datetime): Fecha y hora para la predicción
            
        Returns:
            dict: Predicción y probabilidad de accidente
        """
        # Extraer características del datetime
        hour = datetime_obj.hour
        month = datetime_obj.month
        weekday = datetime_obj.weekday() + 1  # Python: 0=Monday, necesitamos 1=Lunes
        
        # Obtener características derivadas
        turn = self.get_turn_from_hour(hour)
        district = self.get_district_from_coordinates(lat, lon)
        neighborhood = self.get_neighborhood_from_coordinates(lat, lon)
        
        # Crear DataFrame con las características en el orden correcto
        features = pd.DataFrame({
            'Descripcio_torn_num': [turn],
            'Descripcio_dia_setmana_num': [weekday],
            'Codi_barri': [neighborhood],
        })
        
        # Hacer predicción
        prediction = self.model.predict(features)[0]
        probability = self.model.predict_proba(features)[0]
        
        return {
            'prediction': int(prediction),
            'probability_accident': float(probability[1]),  # Probabilidad de accidente
            'probability_safe': float(probability[0]),      # Probabilidad de no accidente
            'features': {
                'hour': hour,
                'month': month,
                'turn': turn,
                'district': district,
                'neighborhood': neighborhood,
                'weekday': weekday,
                'coordinates': (lat, lon)
            }
        }
    
    def analyze_route_safety(self, route_data, datetime_obj):
        """
        Analiza la seguridad de una ruta completa.
        
        Args:
            route_data (dict): Datos de la ruta de OpenRouteService
            datetime_obj (datetime): Fecha y hora para la predicción
            
        Returns:
            dict: Análisis completo de seguridad de la ruta
        """
        segment_risks = []
        
        try:
            # Extraer geometría según el formato
            if 'features' in route_data:
                # Formato antiguo o simulado
                route_geometry = route_data['features'][0]['geometry']['coordinates']
                # Convertir de [lon, lat] a [lat, lon]
                route_points = [(lat, lon) for lon, lat in route_geometry]
            elif 'routes' in route_data:
                # Formato API ORS v2
                route = route_data['routes'][0]
                if 'geometry' in route:
                    geometry = route['geometry']
                    if isinstance(geometry, str):
                        # Geometría codificada - necesitaría decodificación
                        # Por simplicidad, usar puntos de inicio y fin
                        bbox = route_data.get('bbox', [])
                        if len(bbox) >= 4:
                            route_points = [
                                (bbox[1], bbox[0]),  # Inicio
                                (bbox[3], bbox[2])   # Fin
                            ]
                        else:
                            return None
                    elif isinstance(geometry, dict) and 'coordinates' in geometry:
                        route_points = [(lat, lon) for lon, lat in geometry['coordinates']]
                    else:
                        return None
            else:
                return None
            
            # Analizar cada segmento de la ruta
            # Tomar muestras cada cierto número de puntos para no sobrecargar
            sample_interval = max(1, len(route_points) // 20)  # Máximo 20 muestras
            
            for i in range(0, len(route_points), sample_interval):
                lat, lon = route_points[i]
                risk = self.predict_segment_risk(lat, lon, datetime_obj)
                segment_risks.append(risk)
            
            # Calcular métricas agregadas
            if segment_risks:
                avg_risk = np.mean([r['probability_accident'] for r in segment_risks])
                max_risk = max([r['probability_accident'] for r in segment_risks])
                high_risk_segments = sum(1 for r in segment_risks if r['prediction'] == 1)
                
                # Clasificar el nivel de seguridad
                if avg_risk < 0.2:
                    safety_level = "Muy segura"
                elif avg_risk < 0.4:
                    safety_level = "Segura"
                elif avg_risk < 0.6:
                    safety_level = "Riesgo moderado"
                elif avg_risk < 0.8:
                    safety_level = "Riesgo alto"
                else:
                    safety_level = "Riesgo muy alto"
                
                return {
                    'average_risk': avg_risk,
                    'max_risk': max_risk,
                    'total_segments': len(segment_risks),
                    'high_risk_segments': high_risk_segments,
                    'safety_level': safety_level,
                    'segment_details': segment_risks
                }
            
        except Exception as e:
            logging.error(f"Error al analizar la seguridad de la ruta: {e}")
            return None
        
        return None