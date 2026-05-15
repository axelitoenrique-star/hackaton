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
from twilio.rest import Client  # <--- NUEVA IMPORTACIÓN

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

# NUEVA FUNCIÓN: ENVÍO TWILIO
def enviar_whatsapp_twilio(mensaje_texto, destino):
    # Solo estas 3 líneas para las credenciales:
    account_sid = st.secrets["TWILIO_ACCOUNT_SID"]
    auth_token = st.secrets["TWILIO_AUTH_TOKEN"]
    remitente_twilio = st.secrets["TWILIO_PHONE"] 
    
    try:
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
    if not coords_poligono:
        return []
    
    ruta = [[lat_centro, lon_centro]] 
    coords_formateadas = [[p[1], p[0]] for p in coords_poligono]
    
    if patron == "Perimetral (Bordes)":
        ruta.extend(coords_formateadas)
        ruta.append(coords_formateadas[0]) 
        
    elif patron == "Zig-Zag (Cobertura Total)":
        lats = [p[0] for p in coords_formateadas]
        lons = [p[1] for p in coords_formateadas]
        min_lat, max_lat = min(lats), max(lats)
        min_lon, max_lon = min(lons), max(lons)
        paso_lat = (max_lat - min_lat) / 4
        for i in range(5):
            lat_actual = max_lat - (i * paso_lat)
            if i % 2 == 0:
                ruta.append([lat_actual, min_lon])
                ruta.append([lat_actual, max_lon])
            else:
                ruta.append([lat_actual, max_lon])
                ruta.append([lat_actual, min_lon])
                
    elif patron == "Espiral (Foco Central)":
        radio_max = 0.001
        for i in range(1, 6):
            r = (radio_max / 5) * i
            ruta.extend([
                [lat_centro + r, lon_centro],
                [lat_centro, lon_centro + r],
                [lat_centro - r, lon_centro],
                [lat_centro, lon_centro - r]
            ])
            
    ruta.append([lat_centro, lon_centro]) 
    return ruta

# ==========================================
# FASE 1: REGISTRO
# ==========================================
if st.session_state.paso == 'login':
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("🌱 Enjambre VRA")
        st.subheader("Acceso Administrativo")
        with st.form("registro_form"):
            nombre = st.text_input("Nombre Completo")
            email = st.text_input("Correo Electrónico (Reportes)")
            telefono = st.text_input("Teléfono WhatsApp (Ej: 56912345678)")
            password = st.text_input("Contraseña", type="password")
            submit = st.form_submit_button("Ingresar al Sistema", type="primary", use_container_width=True)
            if submit and nombre and email and telefono:
                tel_limpio = ''.join(filter(str.isdigit, telefono))
                st.session_state.usuario = {'nombre': nombre, 'email': email, 'telefono': tel_limpio}
                st.session_state.paso = 'onboarding_mapa'
                st.rerun()

# ==========================================
# FASE 2: MAPA
# ==========================================
elif st.session_state.paso == 'onboarding_mapa':
    st.header(f"Bienvenido {st.session_state.usuario['nombre']} - Delimitación Satelital")
    st.write("📍 **Paso 1:** Utilice la herramienta de polígono ⬠ para dibujar su parcela real.")
    
    mapa_dibujo = folium.Map(location=[-33.456, -70.650], zoom_start=15, tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}", attr="Esri")
    draw = plugins.Draw(export=True, position='topleft', draw_options={'polyline':False, 'marker':False, 'circle':False})
    draw.add_to(mapa_dibujo)
    mapa_data = st_folium(mapa_dibujo, width=1000, height=400, key="dibujo_inicial")
    
    st.write("📍 **Paso 2:** Ingrese el área total de la zona.")
    area_ingresada = st.number_input("Área total del predio (m²):", min_value=100, max_value=1000000, value=5000, step=100)
    
    if st.button("Confirmar Terreno y Continuar ➡️", type="primary"):
        st.session_state.parcela_area = area_ingresada
        lat_clima, lon_clima = -33.456, -70.650 
        if mapa_data and mapa_data.get("all_drawings"):
            dibujo = mapa_data["all_drawings"][0]
            st.session_state.poligono_coords = dibujo["geometry"]["coordinates"][0]
            coords_formateadas = [[p[1], p[0]] for p in st.session_state.poligono_coords]
            promedio_lat = sum(p[0] for p in coords_formateadas) / len(coords_formateadas)
            promedio_lon = sum(p[1] for p in coords_formateadas) / len(coords_formateadas)
            st.session_state.centro_mapa = [promedio_lat, promedio_lon]
            lon_clima, lat_clima = st.session_state.poligono_coords[0][0], st.session_state.poligono_coords[0][1]
            
        st.session_state.clima_real = obtener_clima_real(lat_clima, lon_clima)
        st.session_state.paso = 'onboarding_cultivos'
        st.rerun()

# ==========================================
# FASE 3: CULTIVOS
# ==========================================
elif st.session_state.paso == 'onboarding_cultivos':
    st.header("🌾 Distribución de Plantaciones")
    st.write(f"Límite total: **{st.session_state.parcela_area} m²**.")
    cultivos_seleccionados = st.multiselect("Seleccione cultivos presentes:", DB_CULTIVOS)
    
    if cultivos_seleccionados:
        area_asignada_total = 0
        asignaciones = {}
        for cultivo in cultivos_seleccionados:
            m2 = st.number_input(f"Asignar m² para {cultivo}:", min_value=0, max_value=st.session_state.parcela_area, value=0, step=100)
            asignaciones[cultivo] = m2
            area_asignada_total += m2
        
        st.progress(min(area_asignada_total / st.session_state.parcela_area, 1.0))
        if area_asignada_total > st.session_state.parcela_area:
            st.error("❌ ERROR: Has superado el límite.")
        elif area_asignada_total == 0:
            st.warning("⚠️ Debes asignar área.")
        else:
            if st.button("✅ Confirmar y Acceder al Sistema", type="primary"):
                st.session_state.cultivos_asignados = asignaciones
                st.session_state.paso = 'dashboard'
                st.rerun()

# ==========================================
# FASE 4: DASHBOARD PRINCIPAL
# ==========================================
elif st.session_state.paso == 'dashboard':
    st.title(f"📊 Dashboard Enjambre VRA | Admin: {st.session_state.usuario['nombre']}")
    
    with st.sidebar:
        st.header("🕒 Cronograma Operativo")
        st.markdown('<div class="horario-auto">💧 05:30 AM - Riego</div>', unsafe_allow_html=True)
        st.markdown('<div class="horario-auto">🧪 08:00 AM - Vitaminas</div>', unsafe_allow_html=True)
        st.markdown('<div class="horario-auto">🛡️ 06:00 PM - Antiplagas</div>', unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["🌱 1. Sensores", "🚁 2. Logística Dron", "📈 3. Reporte"])
    
    with tab1:
        clima_cols = st.columns(4)
        tr, hr, vr = st.session_state.clima_real["temp"], st.session_state.clima_real["hum"], st.session_state.clima_real["viento"]
        clima_cols[0].metric("Temp", f"{tr}°C")
        clima_cols[1].metric("Humedad", f"{hr}%")
        clima_cols[2].metric("Viento", f"{vr} km/h")
        clima_cols[3].metric("Riesgo", "Alto" if tr > 26 else "Normal")
        
        st.markdown("---")
        nombres_cultivos = list(st.session_state.cultivos_asignados.keys())
        zonas = st.columns(3)
        if len(nombres_cultivos) > 0:
            with zonas[0]: st.markdown(f'<div class="sensor-verde"><b>Sector A: {nombres_cultivos[0]}</b><br>Humedad: 68%</div>', unsafe_allow_html=True)
        if len(nombres_cultivos) > 1:
            with zonas[1]: st.markdown(f'<div class="sensor-amarillo"><b>Sector B: {nombres_cultivos[1]}</b><br>Humedad: 45%</div>', unsafe_allow_html=True)
        with zonas[2]: st.markdown(f'<div class="sensor-rojo">🚨 Zona de Riesgo</div>', unsafe_allow_html=True)

    with tab2:
        st.header("Centro de Mando Logístico VRA")
        col_ctrl, col_map = st.columns([1, 2])
        ruta_calculada = []
        color_ruta = "cyan"
        
        with col_ctrl:
            hora_actual = st.slider("Reloj:", 0, 23, 14)
            tipo_mision = st.radio("Misión:", ["Riego de Emergencia", "Nutrición", "Tratamiento"])
            patron_vuelo = st.selectbox("Patrón:", ["Zig-Zag (Cobertura Total)", "Espiral (Foco Central)", "Perimetral (Bordes)"])
            
            es_riesgoso = (tipo_mision == "Riego de Emergencia" and 10 <= hora_actual <= 18)
            btn_off = False
            if es_riesgoso:
                st.error("⚠️ Riesgo foliar detectado.")
                if not st.checkbox("Autorizo"): btn_off = True 
            
            if st.button("🚀 Forzar Despliegue", type="primary", disabled=btn_off, use_container_width=True):
                litros = st.session_state.parcela_area * 0.5 if tipo_mision == "Riego de Emergencia" else 0
                st.session_state.total_litros_hoy += litros
                color_ruta = "cyan" if tipo_mision == "Riego de Emergencia" else "orange"
                ruta_calculada = calcular_ruta_patron(st.session_state.poligono_coords, patron_vuelo, st.session_state.centro_mapa[0], st.session_state.centro_mapa[1])
                with st.spinner("Transmitiendo..."):
                    time.sleep(1)
                    st.success(f"✅ Dron en vuelo: {patron_vuelo}")
                    st.session_state.registro_diario.append({"Hora": f"{hora_actual}:00", "Misión": tipo_mision, "Patrón": patron_vuelo, "Agua Usada": f"{litros} L", "Estado": "Completado"})
        
        with col_map:
            mapa_dron = folium.Map(location=st.session_state.centro_mapa, zoom_start=18, tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}", attr="Esri", zoom_control=False, scrollWheelZoom=False, dragging=False)
            if st.session_state.poligono_coords:
                cf = [[p[1], p[0]] for p in st.session_state.poligono_coords]
                folium.Polygon(locations=cf, color="gray", fill=True, fill_opacity=0.2).add_to(mapa_dron)
                mapa_dron.fit_bounds(cf)
            if ruta_calculada:
                plugins.AntPath(locations=ruta_calculada, color=color_ruta, weight=5).add_to(mapa_dron)
            st_folium(mapa_dron, width=700, height=400, returned_objects=[])

    with tab3:
        st.header("Bitácora y Exportación")
        if st.session_state.registro_diario:
            st.dataframe(pd.DataFrame(st.session_state.registro_diario), use_container_width=True)
        
        st.markdown("---")
        st.subheader("📲 Reporte Automático Profesional (Twilio)")
        resumen_texto = f"*REPORTE ENJAMBRE VRA* 🚁🌱\nGerente: {st.session_state.usuario['nombre']}\nÁrea: {st.session_state.parcela_area} m2\n💧 *Agua Utilizada Hoy: {st.session_state.total_litros_hoy} L*\nEstado: OPERACIÓN ESTABLE ✅"
        
        st.text_area("Vista previa del mensaje:", value=resumen_texto, height=120, disabled=True)
        
        # EL BOTÓN DE TWILIO AHORA ENVÍA SIN REDIRIGIR
        if st.button("🚀 Enviar Reporte Directo vía WhatsApp", type="primary", use_container_width=True):
            with st.spinner("Conectando con servidores de Twilio..."):
                exito, sid = enviar_whatsapp_twilio(resumen_texto, st.session_state.usuario['telefono'])
                if exito:
                    st.success(f"✅ Mensaje enviado exitosamente. ID: {sid}")
                else:
                    st.error(f"❌ Error al enviar mensaje: {sid}")
