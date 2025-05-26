"""
Gemelo Digital de Tráfico Urbano para Sant Adrià del Besòs
Proyecto de Máster en Ciudades Inteligentes

Este script implementa una aplicación Streamlit que:
1. Obtiene datos de incidentes de tráfico en tiempo real de TomTom API
2. Visualiza los incidentes en un mapa interactivo con Folium
3. Calcula y muestra rutas optimizadas considerando el tráfico con OpenRouteService
4. Proporciona análisis básicos sobre los datos de tráfico

Autor: [Tu Nombre]
Fecha: [Fecha]
"""

import streamlit as st
import pandas as pd
import time
from datetime import datetime, timedelta
import os
from streamlit_folium import folium_static

# Importar módulos propios
from config.settings import (
    TOMTOM_API_KEY, ORS_API_KEY, MUNICIPALITY_NAME, CITY_CENTER, 
    PREDEFINED_LOCATIONS, CACHE_DIR
)
from modules.traffic_api import get_traffic_incidents, generate_mock_traffic_data
from modules.route_api import calculate_optimized_route, generate_mock_route_data
from modules.visualization import create_base_map, add_incidents_to_map, add_route_to_map
from modules.analysis import generate_incident_summary, plot_incidents_by_type, analyze_route_impact
from utils.helpers import ensure_directory_exists, format_time_difference, format_distance

# Configuración inicial
st.set_page_config(
    page_title=f"Gemelo Digital de Tráfico - {MUNICIPALITY_NAME}",
    page_icon="🚦",
    layout="wide"
)

# Asegurar que existe el directorio de caché
ensure_directory_exists(CACHE_DIR)

# Funciones de la aplicación
def load_api_keys():
    """Carga las claves de API, primero desde las variables de entorno, luego desde el config"""
    tomtom_key = os.environ.get("TOMTOM_API_KEY", TOMTOM_API_KEY)
    ors_key = os.environ.get("ORS_API_KEY", ORS_API_KEY)
    
    return tomtom_key, ors_key

def main():
    """Función principal que ejecuta la aplicación Streamlit"""
    
    # Título y descripción
    st.title(f"🚦 Gemelo Digital de Tráfico Urbano")
    st.subheader(MUNICIPALITY_NAME)
    
    # Cargar claves de API
    tomtom_key, ors_key = load_api_keys()
    
    # Verificar si estamos en modo demo (sin claves de API reales)
    demo_mode = (tomtom_key == "YOUR_TOMTOM_API_KEY" or ors_key == "YOUR_ORS_API_KEY")
    
    if demo_mode:
        st.warning("⚠️ Ejecutando en modo demostración con datos simulados. Para datos reales, configura las claves de API en config/settings.py o como variables de entorno.")
    
    # Sidebar con configuraciones
    st.sidebar.title("Configuración")
    
    # Selección de tiempo
    time_option = st.sidebar.radio(
        "Selecciona el momento para visualizar:",
        ["Tiempo real", "Seleccionar hora específica"]
    )
    
    if time_option == "Tiempo real":
        selected_time = datetime.now()
        st.sidebar.info(f"Mostrando datos para: {selected_time.strftime('%d/%m/%Y %H:%M')}")
    else:
        today = datetime.now().date()
        selected_date = st.sidebar.date_input("Fecha", today)
        selected_hour = st.sidebar.slider("Hora", 0, 23, datetime.now().hour)
        selected_minute = st.sidebar.slider("Minuto", 0, 59, (datetime.now().minute // 5) * 5, step=5)
        selected_time = datetime.combine(selected_date, datetime.min.time()) + timedelta(hours=selected_hour, minutes=selected_minute)
        st.sidebar.info(f"Mostrando datos para: {selected_time.strftime('%d/%m/%Y %H:%M')}")
    
    # Claves de API (si no estamos en modo demo)
    if not demo_mode:
        with st.sidebar.expander("Configuración de APIs"):
            tomtom_key = st.text_input("Clave de API TomTom", tomtom_key)
            ors_key = st.text_input("Clave de API OpenRouteService", ors_key)
    
    # Calculador de rutas
    st.sidebar.subheader("Calculador de Rutas")
    route_start = st.sidebar.selectbox(
        "Punto de inicio:",
        list(PREDEFINED_LOCATIONS.keys()) + ["Personalizado"]
    )
    
    # Entrada personalizada para el punto de inicio si se selecciona
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
    
    # Entrada personalizada para el punto de destino si se selecciona
    if route_end == "Personalizado":
        end_lat = st.sidebar.number_input("Latitud destino", value=CITY_CENTER[0] + 0.01, format="%.4f")
        end_lon = st.sidebar.number_input("Longitud destino", value=CITY_CENTER[1] + 0.01, format="%.4f")
        end_coords = (end_lat, end_lon)
    else:
        end_coords = PREDEFINED_LOCATIONS[route_end]
    
    calculate_route = st.sidebar.button("Calcular Ruta Optimizada")
    
    # Pestañas principales
    tab1, tab2, tab3 = st.tabs(["Mapa de Incidentes", "Análisis de Datos", "Información del Proyecto"])

    with tab1:
        st.subheader("Mapa Interactivo de Tráfico")
        
        # Cargar datos de incidentes
        with st.spinner("Cargando datos de incidentes..."):
            if demo_mode:
                # Usar datos simulados en modo demo
                incidents_df = generate_mock_traffic_data()
                st.toast("Usando datos simulados", icon="ℹ️")
            else:
                # Intentar obtener datos reales de la API
                incidents_df = get_traffic_incidents(tomtom_key)
        
        # Mostrar mapa base
        m = create_base_map()
        
        # Añadir incidentes al mapa
        if not incidents_df.empty:
            m = add_incidents_to_map(m, incidents_df)
            st.success(f"✅ Se encontraron {len(incidents_df)} incidentes de tráfico en {MUNICIPALITY_NAME}")
        else:
            st.info(f"No se encontraron incidentes activos en {MUNICIPALITY_NAME}")
        
        # Calcular y añadir ruta si se solicita
        route_data = None
        current_route = None
    if calculate_route:  # Solo ejecutar este bloque si se presiona el botón
        with st.spinner("Calculando ruta optimizada..."):
            if demo_mode:
                # Simular datos de ruta en modo demo
                route_data = generate_mock_route_data(start_coords, end_coords)
                time.sleep(1)  # Simular tiempo de cálculo
            else:
                # Calcular ruta real con la API
                route_data = calculate_optimized_route(
                    ors_key, 
                    start_coords,
                    end_coords,
                    incidents_df
                )

        # Todo el procesamiento de ruta debe estar dentro de este bloque if calculate_route
        if route_data is None:
            # Si no se pudo obtener ninguna respuesta de la API
            st.error("❌ No se pudo calcular la ruta. Verifica las coordenadas y la disponibilidad de la API.")
            
        else:
            # Tenemos una respuesta de la API, pero podría no tener el formato esperado
            try:
                # Verificar que route_data tiene la estructura esperada
                if ('features' in route_data and route_data['features']) or ('routes' in route_data and route_data['routes']):
                    # Añadir ruta al mapa
                    m = add_route_to_map(m, route_data)
                    
                    # Extraer información de la ruta
                    try:
                        if 'features' in route_data:
                            # Formato antiguo o simulado
                            route_props = route_data['features'][0]['properties']
                            segments = route_props.get('segments', [{}])[0]
                        else:
                            # Formato de la API OpenRouteService v2
                            route = route_data['routes'][0]
                            summary = route['summary']
                            segments = {
                                'duration': summary.get('duration', 0),
                                'distance': summary.get('distance', 0)
                            }
                        
                        # Calcular valores
                        duration_minutes = round(segments.get('duration', 0) / 60, 1)
                        distance_km = round(segments.get('distance', 0), 2)
                        
                        # Mostrar información de la ruta
                        st.success(f"✅ Ruta calculada: {distance_km} km, {duration_minutes} minutos")
                        
                        # Definir la ruta actual para análisis de impacto
                        current_route = route_data
                    except Exception as e:
                        st.error(f"Error al procesar información detallada de la ruta: {e}")
                        # Usar información básica si no se pueden extraer detalles
                        st.success(f"✅ Ruta calculada correctamente")
                        current_route = route_data
                else:
                    st.warning("La respuesta de la API no tiene el formato esperado. Comprueba la configuración de OpenRouteService.")
                    st.info("Usando datos de ruta simulados como alternativa.")
                    
                    # Generar ruta simulada
                    mock_route = generate_mock_route_data(start_coords, end_coords)
                    m = add_route_to_map(m, mock_route)
                    
                    # Mostrar información básica
                    st.success(f"✅ Ruta simulada calculada")
                    
                    # Definir la ruta actual para análisis de impacto
                    current_route = mock_route

            except Exception as e:
                st.error(f"Error al procesar la ruta: {e}")
                st.info("Usando datos de ruta simulados como alternativa.")
                
                # Generar ruta simulada
                mock_route = generate_mock_route_data(start_coords, end_coords)
                m = add_route_to_map(m, mock_route)
                
                # Mostrar información básica
                st.success(f"✅ Ruta simulada calculada")
                
                # Definir la ruta actual para análisis de impacto
                current_route = mock_route
            
            # Análisis de impacto (dentro del bloque calculate_route, pero fuera del try-except)
            if current_route and incidents_df is not None and not incidents_df.empty:
                impact_analysis = analyze_route_impact(current_route, incidents_df)
                
                # Mostrar análisis de impacto si hay incidentes cerca
                if impact_analysis["affected_by_incidents"]:
                    impact_color = {
                        "Bajo": "green",
                        "Moderado": "orange",
                        "Alto": "red"
                    }.get(impact_analysis["severity"], "blue")
                    
                    st.warning(
                        f"⚠️ La ruta está afectada por {impact_analysis['total_incidents_nearby']} incidentes. "
                        f"Impacto: **:{impact_color}[{impact_analysis['severity']}]** "
                        f"(retraso estimado: {impact_analysis['estimated_delay']:.1f} minutos)"
                    )
        
        # Mostrar el mapa en Streamlit
        folium_static(m)
    
    with tab2:
        st.subheader("Análisis de Datos de Tráfico")
        
        if 'incidents_df' in locals() and not incidents_df.empty:
            # Generar resumen de incidentes
            summary = generate_incident_summary(incidents_df)
            
            # Estadísticas básicas en tarjetas
            col1 = st.columns(1)[0]
            with col1:
                st.metric("Total de incidentes", summary["total_incidents"])
            
            # Mostrar incidentes por tipo (si quieres)
            st.write("### Incidentes por tipo")
            for tipo, count in summary["by_type"].items():
                st.write(f"- {tipo}: {count}")
            
            # Gráfica
            st.subheader("Incidentes por tipo")
            fig = plot_incidents_by_type(incidents_df)
            st.pyplot(fig)
            
            # Tabla con detalles
            st.subheader("Detalles de incidentes")
            display_cols = ['tipo']
            st.dataframe(incidents_df[display_cols])
            
            # Explicación de campos
            with st.expander("Explicación de los campos"):
                st.markdown("""
                **tipo**: Categoría principal del incidente.
                - **CONGESTION**: Tráfico denso o atasco.
                - **ACCIDENT**: Accidente o incidente que afecta la circulación.
                - **CONSTRUCTION**: Obras o trabajos en la vía.
                - **LANE_RESTRICTION**: Restricción de carriles.
                - **CLOSURES**: Cierre completo de vía.
                """)
        else:
            st.info("Carga los datos en la pestaña 'Mapa de Incidentes' para ver el análisis.")

    
    with tab3:
        st.subheader("Sobre el Proyecto")
        
        st.markdown("""
        ### Gemelo Digital de Tráfico Urbano
        
        Este proyecto implementa un gemelo digital para visualizar y analizar datos de tráfico urbano en tiempo real en Sant Adrià del Besòs, integrando APIs públicas de datos y proporcionando una visualización interactiva.
        
        #### Objetivos
        
        - Visualizar incidentes de tráfico en tiempo real
        - Calcular rutas optimizadas considerando las condiciones de tráfico
        - Analizar el impacto de incidentes en la movilidad urbana
        - Proporcionar una herramienta útil para la toma de decisiones en gestión de tráfico
        
        #### Tecnologías utilizadas
        
        - **Python**: Lenguaje principal de desarrollo
        - **Streamlit**: Framework para la interfaz de usuario
        - **Folium**: Visualización de mapas interactivos
        - **Pandas**: Análisis y manipulación de datos
        - **TomTom API**: Datos de incidentes de tráfico en tiempo real
        - **OpenRouteService**: Cálculo de rutas optimizadas
        
        #### Características
        
        - Visualización geoespacial de incidentes en tiempo real
        - Cálculo de rutas considerando incidentes activos
        - Análisis estadístico de datos de tráfico
        - Interfaz interactiva para exploración de datos
        
        #### Aplicaciones
        
        - **Ciudadanos**: Planificación de rutas óptimas
        - **Gestores municipales**: Monitorización y gestión de incidentes
        - **Urbanistas**: Análisis de patrones de tráfico para mejora de infraestructuras
        - **Servicios de emergencia**: Planificación de rutas prioritarias
        
        #### Desarrollado por
        
        [Tu Nombre] - Proyecto de Máster en Ciudades Inteligentes
        """)
        
        # Mostrar información de las APIs
        with st.expander("APIs utilizadas"):
            st.markdown("""
            #### TomTom Traffic Incidents API
            
            API para obtener datos de incidentes de tráfico en tiempo real.
            
            - Documentación: [TomTom Traffic API](https://developer.tomtom.com/traffic-api/documentation/traffic-incidents/incident-details)
- Endpoints utilizados:
                - `/traffic/services/4/incidentDetails`: Obtiene detalles de incidentes en un área
            - Características clave:
                - Información en tiempo real
                - Clasificación detallada de incidentes
                - Datos de severidad y duración
                - Coordenadas precisas para mapeo
            
            #### OpenRouteService API
            
            API para calcular rutas optimizadas considerando diversos factores.
            
            - Documentación: [OpenRouteService API](https://openrouteservice.org/dev/#/api-docs)
            - Endpoints utilizados:
                - `/v2/directions/driving-car`: Cálculo de rutas para vehículos
            - Características clave:
                - Soporte para evitar áreas específicas
                - Instrucciones detalladas paso a paso
                - Estimación precisa de tiempos
                - Soporte para múltiples perfiles de transporte
            """)

if __name__ == "__main__":
    main()