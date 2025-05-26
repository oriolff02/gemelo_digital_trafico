"""
Gemelo Digital de Tráfico Urbano para Barcelona
Optimización de rutas según riesgo de accidente predicho por IA (XGBoost)
"""

import streamlit as st
import pandas as pd
import time
from datetime import datetime, timedelta
from streamlit_folium import folium_static
import folium

# Importar módulos propios
from config.settings import (
    ORS_API_KEY, MUNICIPALITY_NAME, CITY_CENTER,
    PREDEFINED_LOCATIONS, CACHE_DIR
)
from modules.route_api import calculate_optimized_route
from modules.visualization import create_base_map
from utils.helpers import ensure_directory_exists

# --- IA Predictiva
from modules.accident_predictor import AccidentPredictor

# Configuración inicial
st.set_page_config(
    page_title=f"Gemelo Digital de Tráfico - {MUNICIPALITY_NAME}",
    page_icon="🚦",
    layout="wide"
)

ensure_directory_exists(CACHE_DIR)

# --- Cargar modelo predictor de accidentes (XGBoost)
@st.cache_resource(show_spinner="Cargando modelo IA...")
def load_predictor():
    return AccidentPredictor(model_path="xgboost_model_definitivo.pkl")

predictor = load_predictor()

def add_route_to_map(m, route_data, color='blue', name="Ruta"):
    """
    Añade la ruta al mapa folium.
    route_data puede estar en formato GeoJSON o dict de ORS.
    """
    # Extraer lista de puntos [(lat, lon)]
    if 'features' in route_data:
        coords = route_data['features'][0]['geometry']['coordinates']
        points = [(lat, lon) for lon, lat in coords]
    elif 'routes' in route_data:
        import polyline
        geometry = route_data['routes'][0]['geometry']
        if isinstance(geometry, str):
            points = polyline.decode(geometry)
        elif isinstance(geometry, dict):
            points = [(lat, lon) for lon, lat in geometry['coordinates']]
        else:
            points = []
    else:
        points = []

    if points:
        folium.PolyLine(points, color=color, weight=6, opacity=0.7, tooltip=name).add_to(m)
    return m

# --- Función para analizar el riesgo de una ruta
def analizar_riesgo_ruta(route_data, fecha_hora):
    # Extraer puntos de la ruta
    if 'features' in route_data:
        # GeoJSON
        coords = route_data['features'][0]['geometry']['coordinates']
        points = [(lat, lon) for lon, lat in coords]
    elif 'routes' in route_data:
        # ORS v2 (puede estar codificado)
        import polyline
        geometry = route_data['routes'][0]['geometry']
        if isinstance(geometry, str):
            points = polyline.decode(geometry)
        elif isinstance(geometry, dict):
            points = [(lat, lon) for lon, lat in geometry['coordinates']]
        else:
            points = []
    else:
        points = []

    # Para cada punto de la ruta, predecir riesgo
    riesgos = []
    detalles = []
    for lat, lon in points:
        pred = predictor.predict_segment_risk(lat, lon, fecha_hora)
        riesgos.append(pred['probability_accident'])
        detalles.append({
            'probabilidad': pred['probability_accident'],
            'coords': (lat, lon),
            'detalles': pred
        })
    # Calcula el riesgo medio de la ruta
    riesgo_medio = sum(riesgos) / len(riesgos) if riesgos else 0
    return riesgo_medio, detalles

# --- Sidebar: selección de origen y destino
st.sidebar.title("Configuración de Ruta")
route_start = st.sidebar.selectbox(
    "Punto de inicio:",
    list(PREDEFINED_LOCATIONS.keys()) + ["Personalizado"]
)
if route_start == "Personalizado":
    start_lat = st.sidebar.number_input("Latitud inicio", value=CITY_CENTER[0], format="%.4f")
    start_lon = st.sidebar.number_input("Longitud inicio", value=CITY_CENTER[1], format="%.4f")
    start_coords = (start_lat, start_lon)
else:
    start_coords = PREDEFINED_LOCATIONS[route_start]

route_end = st.sidebar.selectbox(
    "Punto de destino:",
    list(PREDEFINED_LOCATIONS.keys()) + ["Personalizado"],
    index=1 if len(PREDEFINED_LOCATIONS) > 1 else 0
)
if route_end == "Personalizado":
    end_lat = st.sidebar.number_input("Latitud destino", value=CITY_CENTER[0]+0.01, format="%.4f")
    end_lon = st.sidebar.number_input("Longitud destino", value=CITY_CENTER[1]+0.01, format="%.4f")
    end_coords = (end_lat, end_lon)
else:
    end_coords = PREDEFINED_LOCATIONS[route_end]

# Selección de fecha/hora del viaje
st.sidebar.subheader("Fecha y hora del viaje")
time_option = st.sidebar.radio(
    "¿Cuándo vas a viajar?",
    ["Ahora", "Elegir fecha/hora"]
)
if time_option == "Ahora":
    selected_time = datetime.now()
else:
    today = datetime.now().date()
    selected_date = st.sidebar.date_input("Fecha", today)
    selected_hour = st.sidebar.slider("Hora", 0, 23, datetime.now().hour)
    selected_minute = st.sidebar.slider("Minuto", 0, 59, (datetime.now().minute // 5) * 5, step=5)
    selected_time = datetime.combine(selected_date, datetime.min.time()) + timedelta(hours=selected_hour, minutes=selected_minute)

# Botón para calcular rutas
st.sidebar.markdown("---")
calcular = st.sidebar.button("Calcular rutas y recomendar la más segura 🚦")

# ---- Página principal
st.title("🚦 Gemelo Digital de Tráfico Urbano")
st.subheader(f"Rutas más seguras según predicción de accidentes ({MUNICIPALITY_NAME})")

# --- Visualización del mapa y la ruta recomendada
m = create_base_map()

if calcular:
    with st.spinner("Calculando rutas y riesgos de accidente..."):
        # 1. Calcula rutas alternativas
        response = calculate_optimized_route(ORS_API_KEY, start_coords, end_coords)
        rutas = []
        if response and 'routes' in response:
            for route in response['routes']:
                route_data = {
                    'routes': [route],
                    'bbox': response.get('bbox', [])
                }
                rutas.append(route_data)
        elif response:
            rutas.append(response)

        # 2. Analiza el riesgo de cada ruta
        resumen_rutas = []
        for idx, ruta in enumerate(rutas):
            riesgo, detalles = analizar_riesgo_ruta(ruta, selected_time)
            resumen_rutas.append({
                "indice": idx,
                "ruta": ruta,
                "riesgo_medio": riesgo,
                "detalles": detalles
            })

        # 3. Guarda resultados en session_state para que los checkboxes funcionen al recargar
        st.session_state['rutas'] = rutas
        st.session_state['resumen_rutas'] = resumen_rutas
        st.session_state['selected_time'] = selected_time

# ------- Mostrar las rutas si existen en session_state (esto va FUERA del if calcular, en la parte principal) -------
if 'rutas' in st.session_state and 'resumen_rutas' in st.session_state:
    rutas = st.session_state['rutas']
    resumen_rutas = st.session_state['resumen_rutas']
    selected_time = st.session_state['selected_time']

    ruta_segura = min(resumen_rutas, key=lambda r: r['riesgo_medio'])
    riesgo_pct = ruta_segura['riesgo_medio'] * 100

    st.success(f"Ruta recomendada: riesgo promedio de accidente: {riesgo_pct:.2f}%")
    st.info(f"Se analizaron {len(resumen_rutas)} rutas alternativas")

    ruta_mostrar = []
    st.markdown("#### Mostrar/Ocultar rutas alternativas:")
    for idx, ruta_info in enumerate(resumen_rutas):
        default = (ruta_info == ruta_segura)
        label = f"Ruta {idx+1} - {'RECOMENDADA ' if ruta_info == ruta_segura else ''}(Riesgo: {ruta_info['riesgo_medio']*100:.1f}%)"
        mostrar = st.checkbox(label, value=default, key=f"show_route_{idx}")
        ruta_mostrar.append(mostrar)

    m = create_base_map()
    colors = ['green', 'blue', 'orange', 'red', 'purple']
    for idx, ruta_info in enumerate(resumen_rutas):
        if not ruta_mostrar[idx]:
            continue
        color = 'green' if ruta_info == ruta_segura else colors[idx % len(colors)]
        name = f"Ruta {idx + 1} - RECOMENDADA" if ruta_info == ruta_segura else f"Ruta {idx + 1}"
        m = add_route_to_map(m, ruta_info['ruta'], color=color, name=name)
        # Añadir círculos de riesgo solo para la recomendada
        from folium import CircleMarker
        for det in ruta_info['detalles']:
                lat, lon = det['coords']
                riesgo = det['probabilidad']
                color_circle = (
                    'green' if riesgo < 0.2 else
                    'orange' if riesgo < 0.5 else
                    'red'
                )
                CircleMarker(
                    location=[lat, lon],
                    radius=4,
                    color=color_circle,
                    fill=True,
                    fill_color=color_circle,
                    fill_opacity=0.7
                ).add_to(m)
    folium_static(m)

    # Tabla de riesgos de la recomendada (solo si está seleccionada)
    if ruta_mostrar[resumen_rutas.index(ruta_segura)]:
        st.markdown("### Detalle del riesgo por segmento de la ruta recomendada:")
        df_detalle = pd.DataFrame([
            {
                "Latitud": lat,
                "Longitud": lon,
                "Probabilidad_accidente": riesgo
            }
            for (lat, lon), riesgo in [(d['coords'], d['probabilidad']) for d in ruta_segura['detalles']]
        ])
        st.dataframe(df_detalle)
else:
    st.info("Configura la ruta en la barra lateral y pulsa *Calcular rutas y recomendar la más segura*.")


