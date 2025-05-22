import streamlit as st
import folium
from streamlit_folium import folium_static

# Centro y dos puntos cualquiera
map_center = [41.4252, 2.2245]
m = folium.Map(location=map_center, zoom_start=15)

# Línea entre dos puntos de Sant Adrià
folium.PolyLine(
    [[41.4252, 2.2245], [41.4261, 2.22]],
    color='red', weight=8, opacity=0.8, tooltip="Test line"
).add_to(m)

folium.Marker([41.4252, 2.2245], tooltip="Start").add_to(m)
folium.Marker([41.4261, 2.22], tooltip="End").add_to(m)

folium_static(m)
