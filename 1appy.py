import streamlit as st
import folium
from folium import plugins
from streamlit_folium import st_folium
import time
import pandas as pd
from datetime import date
import urllib.parse
import requests
import base64
import streamlit.components.v1 as components
from twilio.rest import Client

# --- 1. CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Enjambre VRA | Plataforma Integral", page_icon="🚁", layout="wide")

# --- FUNCIÓN PARA CARGAR IMAGEN DE FONDO ---
def cargar_imagen_base64(ruta_imagen):
    try:
        with open(ruta_imagen, "rb") as archivo:
            return base64.b64encode(archivo.read()).decode()
    except FileNotFoundError:
        return None

st.markdown("""
    <style>
    .sensor-verde { background-color: #d4edda; color: #155724; padding: 15px; border-radius: 8px; border-left: 5px solid #28a745; text-align: center; margin-bottom: 10px;}
    .sensor-amarillo { background-color: #fff3cd; color: #856404; padding: 15px; border-radius: 8px; border-left: 5px solid #ffc107; text-align: center; margin-bottom: 10px;}
    .sensor-rojo { background-color: #f8d7da; color: #721c24; padding: 15px; border-radius: 8px; border-left: 5px solid #dc3545; text-align: center; font-weight: bold; margin-bottom: 10px;}
    .horario-auto { background-color: #e2e3e5; color: #383d41; padding: 10px; border-radius: 5px; border-left: 5px solid #6c757d; margin-bottom: 5px;}
    </style>
""", unsafe_allow_html=True)

# --- DISEÑO VISUAL: FONDO AGRÍCOLA ANIMADO ---
fondo_base64 = cargar_imagen_base64("assets/fondo_campo.jpg")

if fondo_base64:
    fondo_css = f"""
    background-image:
        linear-gradient(
            rgba(0, 25, 10, 0.72),
            rgba(0, 40, 18, 0.84)
        ),
        url("data:image/jpg;base64,{fondo_base64}");
    background-size: 115%;
    background-position: center;
    background-attachment: fixed;
    animation: moverFondoCampo 28s ease-in-out infinite alternate;
    """
else:
    fondo_css = """
    background:
        radial-gradient(circle at top left, rgba(34,197,94,0.35), transparent 35%),
        radial-gradient(circle at bottom right, rgba(132,204,22,0.25), transparent 35%),
        linear-gradient(135deg, #052e16 0%, #064e3b 45%, #022c22 100%);
    """

st.markdown(f"""
<style>

/* Ocultar elementos visuales de Streamlit */
#MainMenu {{
    visibility: hidden;
}}

footer {{
    visibility: hidden;
}}

header {{
    visibility: hidden;
}}

/* Fondo principal agrícola con movimiento */
.stApp {{
    {fondo_css}
    color: white;
}}

/* Animación suave del fondo */
@keyframes moverFondoCampo {{
    0% {{
        background-position: center center;
        background-size: 115%;
    }}
    50% {{
        background-position: center top;
        background-size: 122%;
    }}
    100% {{
        background-position: center bottom;
        background-size: 118%;
    }}
}}

/* Partículas verdes suaves */
.stApp::before {{
    content: "";
    position: fixed;
    top: 0;
    left: 0;
    width: 200%;
    height: 200%;
    pointer-events: none;
    z-index: 0;
    background-image:
        radial-gradient(circle, rgba(134, 239, 172, 0.20) 2px, transparent 3px),
        radial-gradient(circle, rgba(187, 247, 208, 0.14) 1px, transparent 3px),
        radial-gradient(circle, rgba(34, 197, 94, 0.12) 2px, transparent 4px);
    background-size: 120px 120px, 180px 180px, 250px 250px;
    animation: particulasCampo 35s linear infinite;
}}

@keyframes particulasCampo {{
    0% {{
        transform: translate(0, 0);
    }}
    100% {{
        transform: translate(-250px, -350px);
    }}
}}

/* Contenido por encima del fondo */
.block-container {{
    position: relative;
    z-index: 2;
    padding-top: 2rem;
    padding-bottom: 2rem;
}}

/* Formularios con efecto vidrio */
[data-testid="stForm"] {{
    background: rgba(0, 45, 20, 0.58);
    padding: 28px;
    border-radius: 24px;
    border: 1px solid rgba(187, 247, 208, 0.28);
    backdrop-filter: blur(14px);
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.38);
}}

/* Métricas tipo tarjeta */
[data-testid="stMetric"] {{
    background: rgba(0, 45, 20, 0.42);
    padding: 18px;
    border-radius: 18px;
    border: 1px solid rgba(187, 247, 208, 0.20);
    box-shadow: 0 12px 35px rgba(0, 0, 0, 0.24);
}}

/* Tabs */
button[data-baseweb="tab"] {{
    background: rgba(0, 45, 20, 0.42);
    border-radius: 14px;
    color: white;
    margin-right: 8px;
    border: 1px solid rgba(187, 247, 208, 0.18);
}}

button[data-baseweb="tab"]:hover {{
    background: rgba(34, 197, 94, 0.25);
}}

/* Títulos y texto */
h1, h2, h3, h4, p, label, span {{
    color: white;
}}

/* Inputs */
.stTextInput input,
.stNumberInput input,
.stSelectbox div,
.stMultiSelect div {{
    border-radius: 12px;
}}

/* Botones Streamlit */
.stButton > button {{
    border-radius: 14px;
    font-weight: 700;
    border: none;
    background: linear-gradient(135deg, #22c55e, #15803d);
    color: white;
    box-shadow: 0 8px 25px rgba(34, 197, 94, 0.25);
}}

.stButton > button:hover {{
    background: linear-gradient(135deg, #16a34a, #166534);
    color: white;
    transform: scale(1.01);
}}

/* Dataframes y alertas */
[data-testid="stDataFrame"],
[data-testid="stAlert"] {{
    border-radius: 18px;
}}

/* Sidebar */
section[data-testid="stSidebar"] {{
    background: rgba(2, 44, 34, 0.94);
    border-right: 1px solid rgba(187, 247, 208, 0.20);
}}

</style>
""", unsafe_allow_html=True)

# --- HOJAS ANIMADAS ---
st.markdown("""
<style>

.hojas-animadas {
    position: fixed;
    inset: 0;
    pointer-events: none;
    z-index: 1;
    overflow: hidden;
}

.hoja {
    position: absolute;
    top: -10%;
    font-size: 24px;
    opacity: 0.45;
    animation: caerHojas 16s linear infinite;
}

.hoja:nth-child(1) { left: 5%; animation-delay: 0s; }
.hoja:nth-child(2) { left: 18%; animation-delay: 3s; }
.hoja:nth-child(3) { left: 33%; animation-delay: 6s; }
.hoja:nth-child(4) { left: 50%; animation-delay: 1s; }
.hoja:nth-child(5) { left: 66%; animation-delay: 4s; }
.hoja:nth-child(6) { left: 82%; animation-delay: 8s; }
.hoja:nth-child(7) { left: 92%; animation-delay: 11s; }

@keyframes caerHojas {
    0% {
        transform: translateY(-10vh) translateX(0) rotate(0deg);
    }
    50% {
        transform: translateY(55vh) translateX(35px) rotate(180deg);
    }
    100% {
        transform: translateY(120vh) translateX(-25px) rotate(360deg);
    }
}

</style>

<div class="hojas-animadas">
    <div class="hoja">🌿</div>
    <div class="hoja">🍃</div>
    <div class="hoja">🌱</div>
    <div class="hoja">🍃</div>
    <div class="hoja">🌿</div>
    <div class="hoja">🌱</div>
    <div class="hoja">🍃</div>
</div>
""", unsafe_allow_html=True)

# --- CURSOR PERSONALIZADO: HORMIGA ANIMADA ---
def activar_cursor_hormiga():
    components.html(
        """
        <script>
        const doc = window.parent.document;

        if (!doc.getElementById("cursor-hormiga-style")) {
            const style = doc.createElement("style");
            style.id = "cursor-hormiga-style";
            style.innerHTML = `
                body, body * {
                    cursor: none !important;
                }

                #cursor-hormiga {
                    position: fixed;
                    width: 46px;
                    height: 34px;
                    pointer-events: none;
                    z-index: 999999999;
                    transform: translate(-50%, -50%);
                    transition: transform 0.04s linear;
                }

                .ant-body {
                    position: absolute;
                    width: 19px;
                    height: 13px;
                    background: #1a1a1a;
                    border-radius: 50%;
                    left: 13px;
                    top: 10px;
                    box-shadow:
                        -11px 1px 0 #1a1a1a,
                        10px 0px 0 #1a1a1a;
                }

                .ant-head {
                    position: absolute;
                    width: 13px;
                    height: 13px;
                    background: #0f0f0f;
                    border-radius: 50%;
                    left: 32px;
                    top: 10px;
                }

                .ant-eye {
                    position: absolute;
                    width: 3px;
                    height: 3px;
                    background: #ffffff;
                    border-radius: 50%;
                    left: 39px;
                    top: 13px;
                }

                .ant-leg {
                    position: absolute;
                    width: 18px;
                    height: 3px;
                    background: #0f0f0f;
                    border-radius: 999px;
                    transform-origin: center;
                    animation: moverPata 0.24s infinite alternate ease-in-out;
                }

                .leg1 { left: 5px; top: 7px; transform: rotate(-35deg); animation-delay: 0s; }
                .leg2 { left: 9px; top: 17px; transform: rotate(0deg); animation-delay: 0.08s; }
                .leg3 { left: 5px; top: 27px; transform: rotate(35deg); animation-delay: 0.16s; }

                .leg4 { left: 24px; top: 7px; transform: rotate(35deg); animation-delay: 0.16s; }
                .leg5 { left: 21px; top: 17px; transform: rotate(0deg); animation-delay: 0.08s; }
                .leg6 { left: 24px; top: 27px; transform: rotate(-35deg); animation-delay: 0s; }

                .ant-antenna {
                    position: absolute;
                    width: 14px;
                    height: 2px;
                    background: #0f0f0f;
                    border-radius: 999px;
                    left: 40px;
                    top: 9px;
                    transform-origin: left center;
                }

                .antenna1 {
                    transform: rotate(-35deg);
                    animation: moverAntena1 0.45s infinite alternate ease-in-out;
                }

                .antenna2 {
                    top: 21px;
                    transform: rotate(35deg);
                    animation: moverAntena2 0.45s infinite alternate ease-in-out;
                }

                @keyframes moverPata {
                    0% {
                        transform: rotate(-25deg) translateX(0px);
                    }
                    100% {
                        transform: rotate(25deg) translateX(2px);
                    }
                }

                @keyframes moverAntena1 {
                    0% {
                        transform: rotate(-25deg);
                    }
                    100% {
                        transform: rotate(-52deg);
                    }
                }

                @keyframes moverAntena2 {
                    0% {
                        transform: rotate(25deg);
                    }
                    100% {
                        transform: rotate(52deg);
                    }
                }
            `;
            doc.head.appendChild(style);
        }

        if (!doc.getElementById("cursor-hormiga")) {
            const ant = doc.createElement("div");
            ant.id = "cursor-hormiga";
            ant.innerHTML = `
                <div class="ant-leg leg1"></div>
                <div class="ant-leg leg2"></div>
                <div class="ant-leg leg3"></div>
                <div class="ant-leg leg4"></div>
                <div class="ant-leg leg5"></div>
                <div class="ant-leg leg6"></div>
                <div class="ant-body"></div>
                <div class="ant-head"></div>
                <div class="ant-eye"></div>
                <div class="ant-antenna antenna1"></div>
                <div class="ant-antenna antenna2"></div>
            `;
            doc.body.appendChild(ant);
        }

        const ant = doc.getElementById("cursor-hormiga");

        doc.addEventListener("mousemove", function(e) {
            ant.style.left = e.clientX + "px";
            ant.style.top = e.clientY + "px";
        });

        doc.addEventListener("mousedown", function() {
            ant.style.transform = "translate(-50%, -50%) scale(0.82)";
        });

        doc.addEventListener("mouseup", function() {
            ant.style.transform = "translate(-50%, -50%) scale(1)";
        });
        </script>
        """,
        height=0,
        width=0
    )

activar_cursor_hormiga()

# --- MEMORIA DEL SISTEMA ---
if 'paso' not in st.session_state: st.session_state.paso = 'login'
if 'usuario' not in st.session_state: st.session_state.usuario = {}
if 'parcela_area' not in st.session_state: st.session_state.parcela_area = 0
if 'cultivos_asignados' not in st.session_state: st.session_state.cultivos_asignados = {}
if 'registro_diario' not in st.session_state: st.session_state.registro_diario = []
if 'poligono_coords' not in st.session_state: st.session_state.poligono_coords = None
if 'centro_mapa' not in st.session_state: st.session_state.centro_mapa = [-33.456, -70.650]
if 'mapa_buscador_inicial' not in st.session_state: st.session_state.mapa_buscador_inicial = [-33.456, -70.650]
if 'clima_real' not in st.session_state: st.session_state.clima_real = {"temp": 0, "hum": 0, "viento": 0}
if 'total_litros_hoy' not in st.session_state: st.session_state.total_litros_hoy = 0

DB_CULTIVOS = ["Cerezas", "Uva Vinífera", "Paltos", "Nogales", "Maíz", "Trigo", "Arándanos"]

# --- 🚀 FUNCIÓN DE TWILIO ---
def enviar_whatsapp_twilio(mensaje, telefono_destino):
    try:
        required_secrets = ["TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "TWILIO_PHONE"]
        faltantes = [secret for secret in required_secrets if secret not in st.secrets]

        if faltantes:
            return False, f"Faltan secrets en Streamlit Cloud: {', '.join(faltantes)}"

        account_sid = st.secrets["TWILIO_ACCOUNT_SID"]
        auth_token = st.secrets["TWILIO_AUTH_TOKEN"]
        twilio_phone = st.secrets["TWILIO_PHONE"]

        client = Client(account_sid, auth_token)
        message = client.messages.create(body=mensaje, from_=twilio_phone, to=f"whatsapp:+{telefono_destino}")
        return True, message.sid
    except Exception as e:
        return False, str(e)

# --- OTRAS FUNCIONES ---
def buscar_ubicacion(direccion):
    try:
        url = f"https://nominatim.openstreetmap.org/search?q={urllib.parse.quote(direccion)}&format=json&limit=1"
        headers = {'User-Agent': 'EnjambreVRADemo/1.0'}
        response = requests.get(url, headers=headers).json()
        if response: return [float(response[0]['lat']), float(response[0]['lon'])]
    except: pass
    return None

def obtener_clima_real(lat, lon):
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&hourly=relative_humidity_2m"
        respuesta = requests.get(url).json()
        temp = respuesta["current_weather"]["temperature"]
        viento = respuesta["current_weather"]["windspeed"]
        humedad = respuesta["hourly"]["relative_humidity_2m"][0]
        return {"temp": temp, "hum": humedad, "viento": viento}
    except: return {"temp": 13.8, "hum": 73, "viento": 1.7}

def calcular_ruta_patron(coords_zona, patron, lat_base, lon_base):
    if not coords_zona: return []
    c_lat = sum(p[0] for p in coords_zona) / len(coords_zona)
    c_lon = sum(p[1] for p in coords_zona) / len(coords_zona)
    ruta = [[lat_base, lon_base], [c_lat, c_lon]] 
    if patron == "Perimetral (Bordes)":
        ruta.extend(coords_zona)
        ruta.append(coords_zona[0]) 
    elif patron == "Zig-Zag (Cobertura Total)":
        lats = [p[0] for p in coords_zona]
        max_lat, min_lat = max(lats), min(lats)
        paso_lat = (max_lat - min_lat) / 6 
        poly = coords_zona + [coords_zona[0]]
        for i in range(1, 6):
            lat_actual = max_lat - (i * paso_lat)
            intersecciones = []
            for j in range(len(poly)-1):
                p1, p2 = poly[j], poly[j+1]
                if (p1[0] <= lat_actual < p2[0]) or (p2[0] <= lat_actual < p1[0]):
                    if p2[0] != p1[0]: 
                        lon_int = p1[1] + (lat_actual - p1[0]) * (p2[1] - p1[1]) / (p2[0] - p1[0])
                        intersecciones.append(lon_int)
            intersecciones.sort()
            if len(intersecciones) >= 2:
                lon_start, lon_end = intersecciones[0], intersecciones[-1]
                if i % 2 == 0: ruta.extend([[lat_actual, lon_start], [lat_actual, lon_end]])
                else: ruta.extend([[lat_actual, lon_end], [lat_actual, lon_start]])
    elif patron == "Espiral (Foco Central)":
        for i in range(1, 6):
            r = (0.0008 / 5) * i
            ruta.extend([[c_lat + r, c_lon], [c_lat, c_lon + r], [c_lat - r, c_lon], [c_lat, c_lon - r]])
    ruta.append([lat_base, lon_base])
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
            telefono = st.text_input("Teléfono WhatsApp (Ej: 56912345678)")
            submit = st.form_submit_button("Ingresar al Sistema", type="primary", use_container_width=True)
            
            if submit and nombre and telefono:
                tel_limpio = ''.join(filter(str.isdigit, telefono))
                st.session_state.usuario = {'nombre': nombre, 'telefono': tel_limpio}
                st.session_state.paso = 'onboarding_mapa'
                st.rerun()

# ==========================================
# FASE 2: MAPA INTELIGENTE (POR COORDENADAS)
# ==========================================
elif st.session_state.paso == 'onboarding_mapa':
    st.header(f"Bienvenido {st.session_state.usuario.get('nombre', '')} - Delimitación Satelital")
    
    st.write("🔍 **Paso 1:** Ingrese las coordenadas (Latitud y Longitud) de su terreno para acercar el satélite.")
    col_lat, col_lon, col_btn = st.columns([2, 2, 1])
    
    with col_lat:
        lat_busqueda = st.number_input("Latitud:", value=-33.45600, format="%.5f")
    with col_lon:
        lon_busqueda = st.number_input("Longitud:", value=-70.65000, format="%.5f")
    with col_btn:
        st.write("")
        if st.button("Ir a Coordenadas", type="primary", use_container_width=True):
            st.session_state.mapa_buscador_inicial = [lat_busqueda, lon_busqueda]
            st.rerun()

    st.write("📍 **Paso 2:** Utilice la herramienta de polígono ⬠ para dibujar las fronteras de su parcela.")
    
    mapa_dibujo = folium.Map(location=st.session_state.mapa_buscador_inicial, zoom_start=15, tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}", attr="Esri")
    draw = plugins.Draw(export=True, position='topleft', draw_options={'polyline':False, 'marker':False, 'circle':False})
    draw.add_to(mapa_dibujo)
    mapa_data = st_folium(mapa_dibujo, width=1000, height=400, key="dibujo_inicial")
    
    st.write("📏 **Paso 3:** Ingrese el área total de la zona (Límite máximo).")
    area_ingresada = st.number_input("Área total del predio (m²):", min_value=100, max_value=1000000, value=5000, step=100)
    
    if st.button("Confirmar Terreno y Continuar ➡️", type="primary"):
        st.session_state.parcela_area = area_ingresada
        lat_clima, lon_clima = st.session_state.mapa_buscador_inicial[0], st.session_state.mapa_buscador_inicial[1]
        
        if mapa_data and mapa_data.get("all_drawings"):
            dibujo = mapa_data["all_drawings"][0]
            st.session_state.poligono_coords = dibujo["geometry"]["coordinates"][0]
            coords_formateadas = [[p[1], p[0]] for p in st.session_state.poligono_coords]
            pts_unicos = coords_formateadas[:-1] if coords_formateadas[0] == coords_formateadas[-1] else coords_formateadas
            st.session_state.centro_mapa = [sum(p[0] for p in pts_unicos) / len(pts_unicos), sum(p[1] for p in pts_unicos) / len(pts_unicos)]
            lon_clima, lat_clima = st.session_state.poligono_coords[0][0], st.session_state.poligono_coords[0][1]
            
        st.session_state.clima_real = obtener_clima_real(lat_clima, lon_clima)
        st.session_state.paso = 'onboarding_cultivos'
        st.rerun()

# ==========================================
# FASE 3: CULTIVOS
# ==========================================
elif st.session_state.paso == 'onboarding_cultivos':
    st.header("🌾 Distribución de Plantaciones")
    st.write(f"Usted cuenta con un límite total de **{st.session_state.parcela_area} m²** registrados.")
    cultivos_seleccionados = st.multiselect("Seleccione cultivos presentes:", DB_CULTIVOS)
    
    if cultivos_seleccionados:
        area_asignada_total = 0
        asignaciones = {}
        for cultivo in cultivos_seleccionados:
            m2 = st.number_input(f"Asignar m² para {cultivo}:", min_value=0, max_value=st.session_state.parcela_area, value=0, step=100)
            asignaciones[cultivo] = m2
            area_asignada_total += m2
        
        st.progress(min(area_asignada_total / st.session_state.parcela_area, 1.0))
        st.write(f"Espacio utilizado: **{area_asignada_total} m²** de **{st.session_state.parcela_area} m²**")
        
        if area_asignada_total > st.session_state.parcela_area:
            st.error("❌ ERROR: Has superado el límite de tu parcela.")
        elif area_asignada_total == 0:
            st.warning("⚠️ Debes asignar al menos 1 metro cuadrado para continuar.")
        else:
            if st.button("✅ Confirmar y Acceder al Sistema", type="primary"):
                st.session_state.cultivos_asignados = asignaciones
                st.session_state.paso = 'dashboard'
                st.rerun()

# ==========================================
# FASE 4: DASHBOARD PRINCIPAL
# ==========================================
elif st.session_state.paso == 'dashboard':
    st.title(f"📊 Dashboard Enjambre VRA | Admin: {st.session_state.usuario.get('nombre', '')}")
    
    zonas_dict = {}
    if st.session_state.poligono_coords:
        coords_formateadas = [[p[1], p[0]] for p in st.session_state.poligono_coords]
        pts = coords_formateadas[:-1] if coords_formateadas[0] == coords_formateadas[-1] else coords_formateadas
        n = len(pts)
        zonas_dict["Toda la Parcela"] = coords_formateadas
        
        if n >= 3:
            c_lat, c_lon = st.session_state.centro_mapa
            centroide = [c_lat, c_lon]
            t1, t2 = n // 3, 2 * (n // 3)
            zonas_dict["Zona Óptima (Verde)"] = [centroide] + pts[0:t1+1] + [centroide]
            zonas_dict["Zona Media (Amarilla)"] = [centroide] + pts[t1:t2+1] + [centroide]
            zonas_dict["Zona Crítica (Roja)"] = [centroide] + pts[t2:] + [pts[0], centroide]

    with st.sidebar:
        st.header("🕒 Cronograma Operativo")
        st.markdown('<div class="horario-auto">💧 <b>05:30 AM</b> - Riego General</div>', unsafe_allow_html=True)
        st.markdown('<div class="horario-auto">🧪 <b>08:00 AM</b> - Aplicación Vitaminas</div>', unsafe_allow_html=True)
        st.markdown('<div class="horario-auto">🛡️ <b>06:00 PM</b> - Control Antiplagas</div>', unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["🌱 1. Sensores y Suelo", "🚁 2. Logística Dron", "📈 3. Reporte Diario y WhatsApp"])
    
    # ---------------- PESTAÑA 1: SENSORES ----------------
    with tab1:
        clima_cols = st.columns(4)
        temp_real, hum_real, viento_real = st.session_state.clima_real["temp"], st.session_state.clima_real["hum"], st.session_state.clima_real["viento"]
        
        clima_cols[0].metric("Temp. Zona Seleccionada", f"{temp_real}°C", "↑ Sensory Data")
        clima_cols[1].metric("Humedad Ambiental", f"{hum_real}%", "↑ IoT")
        clima_cols[2].metric("Velocidad de Viento", f"{viento_real} km/h", "↑ Drone Safe" if viento_real < 25 else "↓ Riesgo Vuelo")
        clima_cols[3].metric("Radiación / Evaporación", "Alta" if temp_real > 26 else "Normal", "↓ Riesgo Foliar" if temp_real > 26 else "↑ Óptimo")
        st.markdown("---")
        
        nombres_cultivos = list(st.session_state.cultivos_asignados.keys())
        zonas_cols = st.columns(3)
        if len(nombres_cultivos) > 0:
            with zonas_cols[0]: st.markdown(f'<div class="sensor-verde"><b>Sector A: {nombres_cultivos[0]}</b><br>Área: {st.session_state.cultivos_asignados[nombres_cultivos[0]]} m²<br>Humedad Suelo: 68%<br>Estado: Óptimo</div>', unsafe_allow_html=True)
        if len(nombres_cultivos) > 1:
            with zonas_cols[1]: st.markdown(f'<div class="sensor-amarillo"><b>Sector B: {nombres_cultivos[1]}</b><br>Área: {st.session_state.cultivos_asignados[nombres_cultivos[1]]} m²<br>Humedad Suelo: 45%<br>Estado: Estrés leve</div>', unsafe_allow_html=True)
        with zonas_cols[2]:
            st.markdown(f'<div class="sensor-rojo"><b>🚨 Zona de Riesgo</b><br>Humedad Suelo: {"22%" if hum_real > 40 else "15% (CRÍTICO)"}<br>Alerta hídrica<br>Requiere Atención</div>', unsafe_allow_html=True)

    # ---------------- PESTAÑA 2: DRON SILENCIOSO ----------------
    with tab2:
        st.header("Centro de Mando Logístico VRA")
        col_ctrl, col_map = st.columns([1, 2])
        ruta_calculada, color_ruta = [], "cyan"
        
        with col_ctrl:
            hora_actual = st.slider("Reloj:", 0, 23, 14, format="%d:00 hrs")
            tipo_mision = st.radio("Acción a ejecutar:", ["Riego de Emergencia", "Nutrición (Proteínas)", "Tratamiento (Anti-plagas)"])
            zona_objetivo = st.selectbox("Sector Objetivo de Vuelo (Focalizado):", list(zonas_dict.keys()) if zonas_dict else ["Toda la Parcela"])
            patron_vuelo = st.selectbox("Patrón de Despliegue Táctico:", ["Zig-Zag (Cobertura Total)", "Espiral (Foco Central)", "Perimetral (Bordes)"])
            
            es_riesgoso = (tipo_mision == "Riego de Emergencia" and 10 <= hora_actual <= 18)
            boton_deshabilitado = es_riesgoso and not st.checkbox("Declaro entender los riesgos y autorizo.") 
            
            if st.button("🚀 Forzar Despliegue Focalizado", type="primary", disabled=boton_deshabilitado, use_container_width=True):
                area_vuelo = st.session_state.parcela_area if zona_objetivo == "Toda la Parcela" else st.session_state.parcela_area / 3
                litros_usados = round(area_vuelo * 0.5, 1) if tipo_mision == "Riego de Emergencia" else 0
                st.session_state.total_litros_hoy += litros_usados
                color_ruta = "cyan" if tipo_mision == "Riego de Emergencia" else ("orange" if tipo_mision == "Nutrición (Proteínas)" else "red")
                
                ruta_calculada = calcular_ruta_patron(zonas_dict.get(zona_objetivo, []), patron_vuelo, st.session_state.centro_mapa[0], st.session_state.centro_mapa[1])
                
                with st.spinner(f"Calculando trayectoria para {zona_objetivo}..."):
                    time.sleep(2)
                    st.success(f"✅ Dron en vuelo silencioso. Objetivo: {zona_objetivo}")
                    if litros_usados > 0: st.info(f"💧 Agua calculada: {litros_usados} L. (Ahorro validado)")
                    
                    st.session_state.registro_diario.append({
                        "Hora": f"{hora_actual}:00", "Misión": tipo_mision, "Objetivo": zona_objetivo,
                        "Agua Usada": f"{litros_usados} L", "Estado": "Completado"
                    })
        
        with col_map:
            st.markdown("**Monitor de Vuelo: Tratamiento Focalizado (Spot Spraying)**")
            mapa_dron = folium.Map(location=st.session_state.centro_mapa, zoom_start=15, tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}", attr="Esri", zoom_control=False, scrollWheelZoom=False, dragging=False, touchZoom=False, doubleClickZoom=False)
            if "Zona Óptima (Verde)" in zonas_dict:
                folium.Polygon(locations=zonas_dict["Zona Óptima (Verde)"], color="green", fill=True, fill_color="green", fill_opacity=0.45).add_to(mapa_dron)
                folium.Polygon(locations=zonas_dict["Zona Media (Amarilla)"], color="yellow", fill=True, fill_color="yellow", fill_opacity=0.45).add_to(mapa_dron)
                folium.Polygon(locations=zonas_dict["Zona Crítica (Roja)"], color="red", fill=True, fill_color="red", fill_opacity=0.45).add_to(mapa_dron)
            elif "Toda la Parcela" in zonas_dict:
                folium.Polygon(locations=zonas_dict["Toda la Parcela"], color="gray", fill=True, fill_opacity=0.4).add_to(mapa_dron)
            if ruta_calculada:
                plugins.AntPath(locations=ruta_calculada, dash_array=[10, 20], delay=800, color=color_ruta, weight=5, pulse_color='white').add_to(mapa_dron)
            st_folium(mapa_dron, width=700, height=400, returned_objects=[])

    # ---------------- PESTAÑA 3: BITÁCORA Y REPORTE EJECUTIVO (SOLO TWILIO) ----------------
    with tab3:
        st.header("Bitácora de Monitoreo")
        if st.session_state.registro_diario:
            st.dataframe(pd.DataFrame(st.session_state.registro_diario), use_container_width=True)
        else: st.write("Aún no se han registrado operaciones hoy.")
            
        st.markdown("---")
        st.subheader("📲 Exportación de Reporte Oficial")
        st.write("Envíe el resumen gerencial directamente a WhatsApp vía Twilio API.")
        
        vuelos_riego = sum(1 for r in st.session_state.registro_diario if r["Misión"] == "Riego de Emergencia")
        vuelos_nutricion = sum(1 for r in st.session_state.registro_diario if r["Misión"] == "Nutrición (Proteínas)")
        vuelos_plagas = sum(1 for r in st.session_state.registro_diario if r["Misión"] == "Tratamiento (Anti-plagas)")
        
        cultivos_str = ', '.join(st.session_state.cultivos_asignados.keys()) if st.session_state.cultivos_asignados else 'Ninguno'
        alerta_zona = "Requiere Atención" if hum_real > 40 else "CRÍTICO - Alerta Hídrica"
        
        resumen_texto_profesional = f"""*📋 REPORTE EJECUTIVO - ENJAMBRE VRA* 🚁🌱
-----------------------------------
*👤 Gerente Agrícola:* {st.session_state.usuario.get('nombre', '')}
*📍 Área Total:* {st.session_state.parcela_area} m²
*🌾 Cultivos Activos:* {cultivos_str}

*☁️ CONDICIONES AGROCLIMÁTICAS*
🌡️ Temp: {temp_real}°C | 💧 Humedad: {hum_real}% | 💨 Viento: {viento_real} km/h

*📊 ESTADO DE SENSORES Y ZONAS*
🟢 Zona Óptima: Estable
🟡 Zona Media: Estrés Leve
🔴 Zona Crítica: {alerta_zona}

*🚀 OPERACIONES REALIZADAS HOY*
🚁 Total Vuelos Desplegados: {len(st.session_state.registro_diario)}
  • 💧 Riegos de Emergencia: {vuelos_riego}
  • 💊 Nutrición (Proteínas): {vuelos_nutricion}
  • 🛡️ Tratamiento (Antiplagas): {vuelos_plagas}

*📊 OPTIMIZACIÓN DE RECURSOS*
💧 Consumo Hídrico Total: {st.session_state.total_litros_hoy} Litros

_Generado automáticamente por Enjambre VRA._"""
        
        st.text_area("Previsualización del Mensaje:", value=resumen_texto_profesional, height=450, disabled=True)
        
        if st.button("🚀 Enviar Reporte Oficial por Twilio", type="primary", use_container_width=True):
            with st.spinner("Conectando con servidores de Twilio..."):
                exito, msj = enviar_whatsapp_twilio(resumen_texto_profesional, st.session_state.usuario.get('telefono', ''))
                if exito: 
                    st.success("✅ Mensaje enviado con éxito a tu celular vía API.")
                else: 
                    st.error(f"❌ Falló el envío. Revisa tus Secrets o Sandbox de Twilio: {msj}")
