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
    # Ciutat Vella
    'el Raval': 1,
    'el Barri Gòtic': 2,
    'la Barceloneta': 3,
    'Sant Pere, Santa Caterina i la Ribera': 4,
    
    # Eixample
    'la Dreta de l\'Eixample': 5,
    'l\'Antiga Esquerra de l\'Eixample': 6,
    'la Nova Esquerra de l\'Eixample': 7,
    'Sant Antoni': 8,
    'la Sagrada Família': 9,
    'el Fort Pienc': 10,
    
    # Sants-Montjuïc
    'el Poble Sec': 11,
    'la Marina del Prat Vermell': 12,
    'la Marina de Port': 13,
    'la Font de la Guatlla': 14,
    'Hostafrancs': 15,
    'la Bordeta': 16,
    'Sants': 17,
    
    # Les Corts
    'les Corts': 18,
    'la Maternitat i Sant Ramon': 19,
    'Pedralbes': 20,
    
    # Sarrià-Sant Gervasi
    'Vallvidrera, el Tibidabo i les Planes': 21,
    'Sarrià': 22,
    'les Tres Torres': 23,
    'Sant Gervasi - la Bonanova': 24,
    'Sant Gervasi - Galvany': 25,
    'el Putxet i el Farró': 26,
    
    # Gràcia
    'Vallcarca i els Penitents': 27,
    'el Coll': 28,
    'la Salut': 29,
    'Vila de Gràcia': 30,
    'el Camp d\'en Grassot i Gràcia Nova': 31,
    
    # Horta-Guinardó
    'el Baix Guinardó': 32,
    'Can Baró': 33,
    'el Guinardó': 34,
    'la Font d\'en Fargues': 35,
    'el Carmel': 36,
    'la Teixonera': 37,
    'Sant Genís dels Agudells': 38,
    'Montbau': 39,
    'la Vall d\'Hebron': 40,
    'la Clota': 41,
    'Horta': 42,
    
    # Nou Barris
    'Vilapicina i la Torre Llobeta': 43,
    'Porta': 44,
    'el Turó de la Peira': 45,
    'Can Peguera': 46,
    'la Guineueta': 47,
    'Canyelles': 48,
    'les Roquetes': 49,
    'Verdun': 50,
    'la Prosperitat': 51,
    'la Trinitat Nova': 52,
    'Torre Baró': 53,
    'Ciutat Meridiana': 54,
    'Vallbona': 55,
    
    # Sant Andreu
    'la Trinitat Vella': 56,
    'Baró de Viver': 57,
    'el Bon Pastor': 58,
    'Sant Andreu': 59,
    'la Sagrera': 60,
    'el Congrés i els Indians': 61,
    'Navas': 62,
    
    # Sant Martí
    'el Camp de l\'Arpa del Clot': 63,
    'el Clot': 64,
    'el Parc i la Llacuna del Poblenou': 65,
    'la Vila Olímpica del Poblenou': 66,
    'el Poblenou': 67,
    'Diagonal Mar i el Front Marítim del Poblenou': 68,
    'el Besòs i el Maresme': 69,
    'Provençals del Poblenou': 70,
    'Sant Martí de Provençals': 71,
    'la Verneda i la Pau': 72
}

class AccidentPredictor:
    def __init__(self, model_path='xgboost_model_balanceado.pkl'):
        """
        Inicializa el predictor de accidentes.
        
        Args:
            model_path (str): Ruta al archivo del modelo entrenado
        """
        try:
            self.model = joblib.load(model_path)
            logging.info(f"Modelo cargado correctamente desde {model_path}")
        except Exception as e:
            logging.error(f"Error al cargar el modelo: {e}")
            raise
    
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
        
        Esta es una implementación simplificada. En producción, deberías usar
        un servicio de geocoding reverso o tener polígonos de distritos.
        
        Args:
            lat (float): Latitud
            lon (float): Longitud
            
        Returns:
            int: Código del distrito
        """
        # Implementación simplificada basada en rangos aproximados
        # En producción, usar geocoding reverso o polígonos reales
        
        if lat > 41.42 and lon < 2.15:
            return DISTRICT_MAPPING['Nou Barris']
        elif lat > 41.42 and lon > 2.15:
            return DISTRICT_MAPPING['Sant Andreu']
        elif lat > 41.40 and lon > 2.18:
            return DISTRICT_MAPPING['Sant Martí']
        elif lat > 41.40 and lon < 2.12:
            return DISTRICT_MAPPING['Sarrià-Sant Gervasi']
        elif lat < 41.37 and lon < 2.14:
            return DISTRICT_MAPPING['Sants-Montjuïc']
        elif 41.38 < lat < 41.40 and 2.16 < lon < 2.18:
            return DISTRICT_MAPPING['Eixample']
        elif lat < 41.38 and lon > 2.17:
            return DISTRICT_MAPPING['Ciutat Vella']
        else:
            return DISTRICT_MAPPING['Eixample']  # Por defecto
    
    def get_neighborhood_from_coordinates(self, lat, lon):
        """
        Determina el barrio basado en las coordenadas.
        
        Esta es una implementación simplificada. En producción, deberías usar
        un servicio de geocoding reverso.
        
        Args:
            lat (float): Latitud
            lon (float): Longitud
            
        Returns:
            int: Código del barrio
        """
        # Implementación muy simplificada
        # En producción, usar geocoding reverso
        
        # Algunos ejemplos de barrios conocidos por coordenadas aproximadas
        if 41.403 < lat < 41.405 and 2.173 < lon < 2.175:
            return NEIGHBORHOOD_MAPPING['la Sagrada Família']
        elif 41.386 < lat < 41.388 and 2.167 < lon < 2.170:
            return NEIGHBORHOOD_MAPPING['la Dreta de l\'Eixample']
        elif 41.379 < lat < 41.382 and 2.188 < lon < 2.191:
            return NEIGHBORHOOD_MAPPING['la Barceloneta']
        else:
            # Por defecto, devolver un barrio basado en el distrito
            district = self.get_district_from_coordinates(lat, lon)
            # Devolver el primer barrio del distrito
            if district == DISTRICT_MAPPING['Eixample']:
                return NEIGHBORHOOD_MAPPING['la Dreta de l\'Eixample']
            elif district == DISTRICT_MAPPING['Ciutat Vella']:
                return NEIGHBORHOOD_MAPPING['el Raval']
            else:
                return 30  # Vila de Gràcia como default
    
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
            'Hora_dia': [hour],
            'Mes_any': [month],
            'Descripcio_torn_num': [turn],
            'Nom_districte_num': [district],
            'Descripcio_dia_setmana_num': [weekday],
            'Codi_barri': [neighborhood]
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