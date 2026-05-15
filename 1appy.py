import streamlit as st
import folium
from folium import plugins
from streamlit_folium import st_folium
import time
import pandas as pd
from datetime import date
import urllib.parse
import requests
import math
from twilio.rest import Client

# --- 1. CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Enjambre VRA | Plataforma Integral", page_icon="🚁", layout="wide")

st.markdown("""
    <style>
    .sensor-verde { background-color: #d4edda; color: #155724; padding: 15px; border-radius: 8px; border-left: 5px solid #28a745; text-align: center; margin-bottom: 10px;}
    .sensor-amarillo { background-color: #fff3cd; color: #856404; padding: 15px; border-radius: 8px; border-left: 5px solid #ffc107; text-align: center; margin-bottom: 10px;}
    .sensor-rojo { background-color: #f8d7da; color: #721c24; padding: 15px; border-radius: 8px; border-left: 5px solid #dc3545; text-align: center; font-weight: bold; margin-bottom: 10px;}
    .whatsapp-btn { background-color: #25D366; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block; text-align: center; width: 100%;}
    .whatsapp-btn:hover { background-color: #128C7E; color: white;}
    .horario-auto { background-color: #e2e3e5; color: #383d41; padding: 10px; border-radius: 5px; border-left: 5px solid #6c757d; margin-bottom: 5px;}
    </style>
""", unsafe_allow_html=True)

# --- MEMORIA DEL SISTEMA ---
if 'paso' not in st.session_state: st.session_state.paso = 'login'
if 'usuario' not in st.session_state: st.session_state.usuario = {}
if 'parcela_area' not in st.session_state: st.session_state.parcela_area = 0
if 'cultivos_asignados' not in st.session_state: st.session_state.cultivos_asignados = {}
if 'registro_diario' not in st.session_state: st.session_state.registro_diario = []
if 'poligono_coords' not in st.session_state: st.session_state.poligono_coords = None
if 'centro_mapa' not in st.session_state: st.session_state.centro_mapa = [-33.456, -70.650]
if 'clima_real' not in st.session_state: st.session_state.clima_real = {"temp": 0, "hum": 0, "viento": 0}
if 'total_litros_hoy' not in st.session_state: st.session_state.total_litros_hoy = 0

DB_CULTIVOS = ["Cerezas", "Uva Vinífera", "Paltos", "Nogales", "Maíz", "Trigo", "Arándanos"]

# --- FUNCIONES DE APOYO ---
def obtener_clima_real(lat, lon):
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&hourly=relative_humidity_2m"
        respuesta = requests.get(url, timeout=5).json()
        temp = respuesta["current_weather"]["temperature"]
        viento = respuesta["current_weather"]["windspeed"]
        humedad = respuesta["hourly"]["relative_humidity_2m"][0]
        return {"temp": temp, "hum": humedad, "viento": viento}
    except:
        return {"temp": 13.8, "hum": 73, "viento": 1.7}

def enviar_whatsapp_twilio(mensaje_texto, destino):
    try:
        # Extracción segura desde st.secrets
        account_sid = st.secrets["TWILIO_ACCOUNT_SID"]
        auth_token = st.secrets["TWILIO_AUTH_TOKEN"]
        remitente_twilio = st.secrets["TWILIO_PHONE"] 
        
        client = Client(account_sid, auth_token)
        message = client.messages.create(
            from_=remitente_twilio,
            body=mensaje_texto,
            to=f'whatsapp:+{destino}'
        )
        return True, message.sid
    except Exception as e:
        return False, str(e)

def calcular_ruta_patron(coords_poligono, patron, lat_centro, lon_centro):
    if not coords_poligono: return []
    ruta = [[lat_centro, lon_centro]] 
    coords_formateadas = [[p[1], p[0]] for p in coords_poligono]
    
    if patron == "Perimetral (Bordes)":
        ruta.extend(coords_formateadas)
        ruta.append(coords_formateadas[0]) 
    elif patron == "Zig-Zag (Cobertura Total)":
        lats = [p[0] for p in coords_formateadas]; lons = [p[1] for p in coords_formateadas]
        min_lat, max_lat, min_lon, max_lon = min(lats), max(lats), min(lons), max(lons)
        paso_lat = (max_lat - min_lat) / 4
        for i in range(5):
            lat_actual = max_lat - (i * paso_lat)
            ruta.append([lat_actual, min_lon if i % 2 == 0 else max_lon])
            ruta.append([lat_actual, max_lon if i % 2 == 0 else min_lon])
    elif patron == "Espiral (Foco Central)":
        radio_max = 0.001
        for i in range(1, 6):
            r = (radio_max / 5) * i
            ruta.extend([[lat_centro + r, lon_centro], [lat_centro, lon_centro + r], [lat_centro - r, lon_centro], [lat_centro, lon_centro - r]])
    ruta.append([lat_centro, lon_centro]) 
    return ruta

# --- FASE 1: REGISTRO ---
if st.session_state.paso == 'login':
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("🌱 Enjambre VRA")
        with st.form("registro_form"):
            nombre = st.text_input("Nombre Completo")
            email = st.text_input("Correo Electrónico")
            telefono = st.text_input("Teléfono (Ej: 56912345678)")
            submit = st.form_submit_button("Ingresar", type="primary", use_container_width=True)
            if submit and nombre and email and telefono:
                st.session_state.usuario = {'nombre': nombre, 'email': email, 'telefono': ''.join(filter(str.isdigit, telefono))}
                st.session_state.paso = 'onboarding_mapa'
                st.rerun()

# --- FASE 2: MAPA ---
elif st.session_state.paso == 'onboarding_mapa':
    st.header("📍 Delimitación Satelital")
    mapa_dibujo = folium.Map(location=[-33.456, -70.650], zoom_start=15, tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}", attr="Esri")
    draw = plugins.Draw(export=True, position='topleft', draw_options={'polyline':False, 'marker':False, 'circle':False})
    draw.add_to(mapa_dibujo)
    mapa_data = st_folium(mapa_dibujo, width=1000, height=400)
    area_ingresada = st.number_input("Área predio (m²):", min_value=100, value=5000)
    if st.button("Confirmar Terreno ➡️", type="primary"):
        st.session_state.parcela_area = area_ingresada
        if mapa_data and mapa_data.get("all_drawings"):
            st.session_state.poligono_coords = mapa_data["all_drawings"][0]["geometry"]["coordinates"][0]
            cf = [[p[1], p[0]] for p in st.session_state.poligono_coords]
            st.session_state.centro_mapa = [sum(p[0] for p in cf)/len(cf), sum(p[1] for p in cf)/len(cf)]
            st.session_state.clima_real = obtener_clima_real(cf[0][0], cf[0][1])
        st.session_state.paso = 'onboarding_cultivos'; st.rerun()

# --- FASE 3: CULTIVOS ---
elif st.session_state.paso == 'onboarding_cultivos':
    st.header("🌾 Distribución")
    cultivos_sel = st.multiselect("Cultivos:", DB_CULTIVOS)
    if cultivos_sel:
        asignaciones = {}
        for c in cultivos_sel: asignaciones[c] = st.number_input(f"m² para {c}:", step=100)
        if st.button("✅ Acceder", type="primary"):
            st.session_state.cultivos_asignados = asignaciones
            st.session_state.paso = 'dashboard'; st.rerun()

# --- FASE 4: DASHBOARD ---
elif st.session_state.paso == 'dashboard':
    st.title(f"📊 Admin: {st.session_state.usuario['nombre']}")
    tab1, tab2, tab3 = st.tabs(["🌱 Sensores", "🚁 Logística", "📈 Reporte"])
    
    with tab1:
        st.metric("Temp Zona", f"{st.session_state.clima_real['temp']}°C")
        st.write(st.session_state.cultivos_asignados)

    with tab2:
        col_ctrl, col_map = st.columns([1, 2])
        ruta_calc = []
        with col_ctrl:
            tipo = st.radio("Misión:", ["Riego", "Nutrición", "Antiplagas"])
            patron = st.selectbox("Patrón:", ["Zig-Zag (Cobertura Total)", "Espiral (Foco Central)", "Perimetral (Bordes)"])
            if st.button("🚀 Despliegue", type="primary"):
                ruta_calc = calcular_ruta_patron(st.session_state.poligono_coords, patron, st.session_state.centro_mapa[0], st.session_state.centro_mapa[1])
                st.session_state.registro_diario.append({"Hora": time.strftime("%H:%M"), "Misión": tipo, "Estado": "OK"})
        with col_map:
            m = folium.Map(location=st.session_state.centro_mapa, zoom_start=18, tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}", attr="Esri", dragging=False)
            if ruta_calc: plugins.AntPath(locations=ruta_calc).add_to(m)
            st_folium(m, width=700, height=400)

    with tab3:
        st.subheader("📲 WhatsApp Automático")
        resumen = f"*REPORTE ENJAMBRE VRA*\nGerente: {st.session_state.usuario['nombre']}\nEstado: OPERACIÓN ESTABLE ✅"
        if st.button("🚀 Enviar vía Twilio", type="primary", use_container_width=True):
            with st.spinner("Enviando..."):
                ok, sid = enviar_whatsapp_twilio(resumen, st.session_state.usuario['telefono'])
                if ok: st.success(f"Enviado. ID: {sid}")
                else: st.error(f"Error: {sid}")
