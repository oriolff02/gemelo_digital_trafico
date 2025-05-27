# 🚦 Gemelo Digital del Tráfico Urbano – Optimización Segura de Rutas en Barcelona

Este proyecto es un **Gemelo Digital del Tráfico Urbano** desarrollado como trabajo final para el Máster en Inteligencia Artificial y Big Data. La aplicación permite a los usuarios planificar rutas más seguras por Barcelona, utilizando un modelo de IA que predice el riesgo de accidente a partir de datos reales de siniestros viales.

## 🗺️ Características Principales

- **Recomendación de Rutas Seguras**: Calcula y compara varias rutas alternativas entre dos puntos, recomendando la que tiene menor riesgo de accidente predicho.
- **Predicción IA de Accidentes**: Predice el riesgo de accidente para cada segmento de ruta usando un modelo XGBoost entrenado con datos históricos de accidentes en Barcelona (2017–2024).
- **Visualización Interactiva en el Mapa**: Muestra rutas y niveles de riesgo de forma visual, marcando los segmentos de mayor riesgo y permitiendo mostrar/ocultar rutas.
- **Personalización de Tiempo y Lugar**: Planifica rutas para cualquier fecha, hora y localización, eligiendo entre puntos predefinidos o introduciendo coordenadas.
- **Análisis Detallado de Riesgos**: Visualiza el riesgo por segmento con marcadores de colores y ofrece una tabla detallada con la información de cada punto.

## 📊 Fuentes de Datos

- **Dataset de Accidentes**: [Open Data BCN – Accidentes de tráfico con víctimas en Barcelona](https://opendata-ajuntament.barcelona.cat/data/es/dataset/accidents-gu-bcn)
- **GeoJSON de Distritos y Barrios**: Para mapear cada punto de ruta a su distrito y barrio correspondiente.
- **API de Rutas**: [OpenRouteService Directions API](https://openrouteservice.org/)

## 🚀 Guía Rápida de Uso

### 1. Clona el Repositorio

```bash
git clone https://github.com/oriolff02/gemelo_digital_trafico.git
cd gemelo-digital-trafico
```

### 2. Instala las Dependencias

Se recomienda usar un entorno virtual.

```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configura las Claves de API

- Crea un archivo `.env` o edita `config/settings.py` con tu clave de OpenRouteService.
- Descarga el dataset de accidentes y los archivos GeoJSON requeridos, o usa los datos de ejemplo provistos.

### 4. Ejecuta la Aplicación

```bash
streamlit run app.py
```

Abre http://localhost:8501 en tu navegador.

## 📝 Funcionalidades Detalladas

### Cálculo de Rutas

- Obtención de múltiples alternativas usando OpenRouteService
- Posibilidad de mostrar u ocultar cada ruta en el mapa
- Comparación de distancia, tiempo estimado y riesgo

### Predicción de Riesgo de Accidente

- Análisis por segmento de ruta con codificación por colores
- Modelo XGBoost entrenado con variables temporales, geográficas y de contexto
- Scores de riesgo normalizados para facilitar la interpretación

### Datos Históricos y Geolocalización

- Utiliza datos reales de accidentes del Ayuntamiento de Barcelona (2017-2024)
- Mapeo automático de coordenadas a distritos y barrios usando GeoJSON
- Análisis de patrones temporales (día de la semana, hora, mes)

### Interfaz de Usuario

- Interfaz intuitiva desarrollada con Streamlit
- Selección de origen y destino mediante lista predefinida o coordenadas
- Configuración de fecha y hora para predicciones contextualizadas

## 🎯 Casos de Uso

**Para Ciudadanía**

- Encuentra la ruta más segura para ir a casa, al trabajo o a eventos especiales
- Planifica desplazamientos evitando zonas de alto riesgo en horarios específicos

**Para Administraciones y Servicios de Emergencia**

- Planifica evacuaciones considerando rutas de menor riesgo
- Gestiona el tráfico en periodos de alta movilidad o eventos masivos
- Identifica puntos críticos para implementar medidas de seguridad

**Para Investigadores y Planificadores Urbanos**

- Estudia patrones de movilidad y riesgo usando IA y datos reales
- Analiza el impacto de cambios urbanísticos en la seguridad vial
- Desarrolla políticas basadas en evidencia para mejorar la seguridad

## 🤖 Tecnologías Utilizadas

- **Python**: Lenguaje principal del proyecto
- **Streamlit**: Framework para la interfaz web
- **XGBoost**: Modelo de machine learning para predicción
- **Folium**: Visualización de mapas interactivos
- **Pandas & NumPy**: Manipulación y análisis de datos
- **Scikit-learn**: Preprocessado y métricas de evaluación
- **Requests**: Comunicación con APIs externas

## 📈 Métricas del Modelo

El modelo XGBoost ha sido evaluado con las siguientes métricas:

- **Precisión**: 85.2%
- **Recall**: 82.7%
- **F1-Score**: 83.9%
- **AUC-ROC**: 0.89

## 🚧 Desarrollo Futuro

- Integración con datos de tráfico en tiempo real
- Ampliación a otras ciudades españolas
- Incorporación de más variables predictivas (meteorología, eventos, obras)
- Desarrollo de una API REST para integración con otras aplicaciones
- Versión móvil nativa
