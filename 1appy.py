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
from twilio.rest import Client


# ==========================================
# CONFIGURACIÓN DE LA PÁGINA
# ==========================================
st.set_page_config(
    page_title="Enjambre VRA | Real Ops",
    page_icon="🚁",
    layout="wide"
)


# ==========================================
# FUNCIÓN PARA CARGAR IMAGEN DE FONDO
# ==========================================
def cargar_imagen_base64(ruta_imagen):
    try:
        with open(ruta_imagen, "rb") as archivo:
            return base64.b64encode(archivo.read()).decode()
    except FileNotFoundError:
        return None


# ==========================================
# ESTILOS ORIGINALES
# ==========================================
st.markdown("""
    <style>
    .sensor-verde {
        background-color: #d4edda;
        color: #155724;
        padding: 15px;
        border-radius: 8px;
        border-left: 5px solid #28a745;
        text-align: center;
        margin-bottom: 10px;
    }

    .sensor-amarillo {
        background-color: #fff3cd;
        color: #856404;
        padding: 15px;
        border-radius: 8px;
        border-left: 5px solid #ffc107;
        text-align: center;
        margin-bottom: 10px;
    }

    .sensor-rojo {
        background-color: #f8d7da;
        color: #721c24;
        padding: 15px;
        border-radius: 8px;
        border-left: 5px solid #dc3545;
        text-align: center;
        font-weight: bold;
        margin-bottom: 10px;
    }

    .whatsapp-btn {
        background-color: #25D366;
        color: white;
        padding: 10px 20px;
        text-decoration: none;
        border-radius: 5px;
        font-weight: bold;
        display: inline-block;
        text-align: center;
        width: 100%;
    }

    .whatsapp-btn:hover {
        background-color: #128C7E;
        color: white;
    }

    .horario-auto {
        background-color: #e2e3e5;
        color: #383d41;
        padding: 10px;
        border-radius: 5px;
        border-left: 5px solid #6c757d;
        margin-bottom: 5px;
    }
    </style>
""", unsafe_allow_html=True)


# ==========================================
# DISEÑO VISUAL: FONDO AGRÍCOLA ANIMADO
# ==========================================
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


# ==========================================
# HOJAS ANIMADAS
# ==========================================
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


# ==========================================
# MEMORIA DEL SISTEMA
# ==========================================
if 'paso' not in st.session_state:
    st.session_state.paso = 'login'

if 'usuario' not in st.session_state:
    st.session_state.usuario = {}

if 'parcela_area' not in st.session_state:
    st.session_state.parcela_area = 0

if 'cultivos_asignados' not in st.session_state:
    st.session_state.cultivos_asignados = {}

if 'registro_diario' not in st.session_state:
    st.session_state.registro_diario = []

if 'poligono_coords' not in st.session_state:
    st.session_state.poligono_coords = None

if 'centro_mapa' not in st.session_state:
    st.session_state.centro_mapa = [-33.456, -70.650]

if 'mapa_buscador_inicial' not in st.session_state:
    st.session_state.mapa_buscador_inicial = [-33.456, -70.650]

if 'clima_real' not in st.session_state:
    st.session_state.clima_real = {"temp": 0, "hum": 0, "viento": 0}

if 'total_litros_hoy' not in st.session_state:
    st.session_state.total_litros_hoy = 0


DB_CULTIVOS = [
    "Cerezas",
    "Uva Vinífera",
    "Paltos",
    "Nogales",
    "Maíz",
    "Trigo",
    "Arándanos"
]


# ==========================================
# FUNCIÓN TWILIO WHATSAPP
# ==========================================
def enviar_whatsapp_twilio(mensaje, telefono_destino):
    try:
        required_secrets = [
            "TWILIO_ACCOUNT_SID",
            "TWILIO_AUTH_TOKEN",
            "TWILIO_PHONE"
        ]

        faltantes = [
            secret for secret in required_secrets
            if secret not in st.secrets
        ]

        if faltantes:
            return False, f"Faltan secrets en Streamlit Cloud: {', '.join(faltantes)}"

        account_sid = st.secrets["TWILIO_ACCOUNT_SID"]
        auth_token = st.secrets["TWILIO_AUTH_TOKEN"]
        twilio_phone = st.secrets["TWILIO_PHONE"]

        client = Client(account_sid, auth_token)

        message = client.messages.create(
            body=mensaje,
            from_=twilio_phone,
            to=f"whatsapp:+{telefono_destino}"
        )

        return True, message.sid

    except Exception as e:
        return False, str(e)


# ==========================================
# FUNCIONES INTELIGENTES
# ==========================================
def buscar_ubicacion(direccion):
    try:
        url = (
            "https://nominatim.openstreetmap.org/search?"
            f"q={urllib.parse.quote(direccion)}&format=json&limit=1"
        )

        headers = {
            'User-Agent': 'EnjambreVRADemo/1.0'
        }

        response = requests.get(url, headers=headers).json()

        if response:
            return [
                float(response[0]['lat']),
                float(response[0]['lon'])
            ]

    except:
        pass

    return None


def obtener_clima_real(lat, lon):
    try:
        url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={lat}&longitude={lon}"
            f"&current_weather=true"
            f"&hourly=relative_humidity_2m"
        )

        respuesta = requests.get(url).json()

        return {
            "temp": respuesta["current_weather"]["temperature"],
            "hum": respuesta["hourly"]["relative_humidity_2m"][0],
            "viento": respuesta["current_weather"]["windspeed"]
        }

    except:
        return {
            "temp": 13.8,
            "hum": 73,
            "viento": 1.7
        }


def calcular_ruta_patron(coords_zona, patron, lat_base, lon_base):
    if not coords_zona:
        return []

    c_lat = sum(p[0] for p in coords_zona) / len(coords_zona)
    c_lon = sum(p[1] for p in coords_zona) / len(coords_zona)

    ruta = [
        [lat_base, lon_base],
        [c_lat, c_lon]
    ]

    if patron == "Perimetral (Bordes)":
        ruta.extend(coords_zona)
        ruta.append(coords_zona[0])

    elif patron == "Zig-Zag (Cobertura Total)":
        lats = [p[0] for p in coords_zona]
        max_lat = max(lats)
        min_lat = min(lats)

        paso_lat = (max_lat - min_lat) / 6
        poly = coords_zona + [coords_zona[0]]

        for i in range(1, 6):
            lat_actual = max_lat - (i * paso_lat)
            intersecciones = []

            for j in range(len(poly) - 1):
                p1 = poly[j]
                p2 = poly[j + 1]

                if (p1[0] <= lat_actual < p2[0]) or (p2[0] <= lat_actual < p1[0]):
                    if p2[0] != p1[0]:
                        lon_interseccion = (
                            p1[1]
                            + (lat_actual - p1[0])
                            * (p2[1] - p1[1])
                            / (p2[0] - p1[0])
                        )
                        intersecciones.append(lon_interseccion)

            intersecciones.sort()

            if len(intersecciones) >= 2:
                if i % 2 == 0:
                    ruta.extend([
                        [lat_actual, intersecciones[0]],
                        [lat_actual, intersecciones[-1]]
                    ])
                else:
                    ruta.extend([
                        [lat_actual, intersecciones[-1]],
                        [lat_actual, intersecciones[0]]
                    ])

    elif patron == "Espiral (Foco Central)":
        for i in range(1, 6):
            r = (0.0008 / 5) * i

            ruta.extend([
                [c_lat + r, c_lon],
                [c_lat, c_lon + r],
                [c_lat - r, c_lon],
                [c_lat, c_lon - r]
            ])

    ruta.append([lat_base, lon_base])

    return ruta


# ==========================================
# FASE 1: REGISTRO
# ==========================================
if st.session_state.paso == 'login':
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.title("🌱 Enjambre VRA")
        st.subheader("Acceso Administrativo Real-Time")

        with st.form("registro_form"):
            nombre = st.text_input("Nombre Completo")
            email = st.text_input("Correo (Respaldo)")
            telefono = st.text_input("Teléfono WhatsApp (Ej: 56912345678)")
            password = st.text_input("Contraseña", type="password")

            submit = st.form_submit_button(
                "Ingresar",
                type="primary",
                use_container_width=True
            )

            if submit and nombre and telefono:
                st.session_state.usuario = {
                    'nombre': nombre,
                    'email': email,
                    'telefono': ''.join(filter(str.isdigit, telefono))
                }

                st.session_state.paso = 'onboarding_mapa'
                st.rerun()


# ==========================================
# FASE 2: MAPA
# ==========================================
elif st.session_state.paso == 'onboarding_mapa':
    st.header(f"Bienvenido {st.session_state.usuario['nombre']}")

    col_search, col_btn = st.columns([3, 1])

    with col_search:
        direccion_busqueda = st.text_input(
            "Buscar ubicación:",
            value="Quilicura, Chile"
        )

    with col_btn:
        st.write("")
        st.write("")

        if st.button("Buscar"):
            coords = buscar_ubicacion(direccion_busqueda)

            if coords:
                st.session_state.mapa_buscador_inicial = coords
                st.rerun()
            else:
                st.warning("No se encontró la ubicación. Intenta con otra dirección.")

    mapa_dibujo = folium.Map(
        location=st.session_state.mapa_buscador_inicial,
        zoom_start=15,
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri"
    )

    draw = plugins.Draw(
        export=True,
        position='topleft',
        draw_options={
            'polyline': False,
            'marker': False,
            'circle': False
        }
    )

    draw.add_to(mapa_dibujo)

    mapa_data = st_folium(
        mapa_dibujo,
        width=1000,
        height=400,
        key="dibujo_inicial"
    )

    area_ingresada = st.number_input(
        "Área m²:",
        min_value=100,
        value=5000
    )

    if st.button("Confirmar Parcela ➡️"):
        st.session_state.parcela_area = area_ingresada

        if mapa_data and mapa_data.get("all_drawings"):
            st.session_state.poligono_coords = (
                mapa_data["all_drawings"][0]["geometry"]["coordinates"][0]
            )

            pts = [
                [p[1], p[0]]
                for p in st.session_state.poligono_coords[:-1]
            ]

            if pts:
                st.session_state.centro_mapa = [
                    sum(p[0] for p in pts) / len(pts),
                    sum(p[1] for p in pts) / len(pts)
                ]
        else:
            st.warning(
                "No se detectó una parcela dibujada. "
                "Puedes continuar, pero no tendrás zonas focalizadas."
            )

        st.session_state.clima_real = obtener_clima_real(
            st.session_state.centro_mapa[0],
            st.session_state.centro_mapa[1]
        )

        st.session_state.paso = 'onboarding_cultivos'
        st.rerun()


# ==========================================
# FASE 3: CULTIVOS
# ==========================================
elif st.session_state.paso == 'onboarding_cultivos':
    st.header("🌾 Distribución")

    cultivos = st.multiselect(
        "Cultivos:",
        DB_CULTIVOS
    )

    if cultivos:
        suma = 0
        temp_dict = {}

        for c in cultivos:
            m = st.number_input(
                f"m² para {c}:",
                min_value=0,
                max_value=st.session_state.parcela_area
            )

            temp_dict[c] = m
            suma += m

        st.progress(
            min(suma / st.session_state.parcela_area, 1.0)
            if st.session_state.parcela_area > 0
            else 0
        )

        st.write(
            f"Área utilizada: **{suma} m²** de "
            f"**{st.session_state.parcela_area} m²**"
        )

        if suma > st.session_state.parcela_area:
            st.error("❌ Has superado el área total de la parcela.")

        elif suma == 0:
            st.warning("⚠️ Debes asignar al menos 1 m² para continuar.")

        else:
            if st.button("✅ Ir al Dashboard"):
                st.session_state.cultivos_asignados = temp_dict
                st.session_state.paso = 'dashboard'
                st.rerun()


# ==========================================
# FASE 4: DASHBOARD
# ==========================================
elif st.session_state.paso == 'dashboard':
    st.title(f"📊 Dashboard | Admin: {st.session_state.usuario['nombre']}")

    zonas_dict = {}

    if st.session_state.poligono_coords:
        pts = [
            [p[1], p[0]]
            for p in st.session_state.poligono_coords[:-1]
        ]

        if len(pts) >= 3:
            n = len(pts)
            centroide = st.session_state.centro_mapa
            t1 = n // 3
            t2 = 2 * (n // 3)

            zonas_dict = {
                "Toda la Parcela": pts,
                "Zona Óptima": [centroide] + pts[0:t1 + 1] + [centroide],
                "Zona Media": [centroide] + pts[t1:t2 + 1] + [centroide],
                "Zona Crítica": [centroide] + pts[t2:] + [pts[0], centroide]
            }

    tab1, tab2, tab3 = st.tabs([
        "🌱 IoT",
        "🚁 Dron",
        "📈 Bitácora"
    ])

    # ==========================================
    # TAB 1: IOT
    # ==========================================
    with tab1:
        st.header("Sensores Activos")

        clima = st.session_state.clima_real

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "Temperatura",
            f"{clima['temp']}°C"
        )

        c2.metric(
            "Humedad",
            f"{clima['hum']}%"
        )

        c3.metric(
            "Viento",
            f"{clima['viento']} km/h"
        )

        st.markdown("---")

        if st.session_state.cultivos_asignados:
            st.subheader("Cultivos registrados")

            cols = st.columns(3)
            cultivos_lista = list(st.session_state.cultivos_asignados.items())

            for i, (cultivo, area) in enumerate(cultivos_lista):
                with cols[i % 3]:
                    st.markdown(
                        f"""
                        <div class="sensor-verde">
                            <b>{cultivo}</b><br>
                            Área asignada: {area} m²<br>
                            Estado: Monitoreado
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

    # ==========================================
    # TAB 2: DRON
    # ==========================================
    with tab2:
        st.header("Mando Logístico")

        col_c, col_m = st.columns([1, 2])

        ruta_calculada = []
        color_ruta = "cyan"

        with col_c:
            hora = st.slider(
                "Reloj:",
                0,
                23,
                14
            )

            tipo = st.radio(
                "Misión:",
                [
                    "Riego",
                    "Proteínas",
                    "Antiplagas"
                ]
            )

            opciones_zona = list(zonas_dict.keys())

            if opciones_zona:
                zona_obj = st.selectbox(
                    "Objetivo:",
                    opciones_zona
                )
            else:
                st.warning(
                    "Primero debes dibujar y confirmar una parcela "
                    "para seleccionar una zona."
                )
                zona_obj = None

            patron_vuelo = st.selectbox(
                "Patrón:",
                [
                    "Zig-Zag (Cobertura Total)",
                    "Espiral (Foco Central)",
                    "Perimetral (Bordes)"
                ]
            )

            riesgo = (
                tipo == "Riego"
                and 10 <= hora <= 18
            )

            boton_des = False

            if riesgo:
                st.error("⚠️ Riesgo solar: riego en horario de alta radiación.")

                if not st.checkbox("Asumo riesgo solar"):
                    boton_des = True

            if st.button(
                "🚀 DESPLEGAR Y NOTIFICAR",
                type="primary",
                disabled=(boton_des or zona_obj is None),
                use_container_width=True
            ):
                if zona_obj == "Toda la Parcela":
                    area_v = st.session_state.parcela_area
                else:
                    area_v = st.session_state.parcela_area / 3

                litros = round(area_v * 0.5, 1) if tipo == "Riego" else 0

                st.session_state.total_litros_hoy += litros

                if tipo == "Riego":
                    color_ruta = "cyan"
                elif tipo == "Proteínas":
                    color_ruta = "orange"
                else:
                    color_ruta = "red"

                coords_objetivo = zonas_dict.get(zona_obj, [])

                ruta_calculada = calcular_ruta_patron(
                    coords_objetivo,
                    patron_vuelo,
                    st.session_state.centro_mapa[0],
                    st.session_state.centro_mapa[1]
                )

                with st.spinner("Conectando con satélite y despachando dron..."):
                    time.sleep(1.5)

                    st.success(f"✅ Dron en vuelo hacia {zona_obj}.")

                    msj_twilio = (
                        f"🚁 ALERTA ENJAMBRE VRA:\n"
                        f"Despliegue iniciado.\n"
                        f"Misión: {tipo}\n"
                        f"Objetivo: {zona_obj}\n"
                        f"Agua: {litros} L\n"
                        f"Hora: {hora}:00 hrs."
                    )

                    exito, resultado = enviar_whatsapp_twilio(
                        msj_twilio,
                        st.session_state.usuario['telefono']
                    )

                    estado_noti = "WhatsApp Enviado"

                    if exito:
                        st.toast(
                            f"📲 Alerta de WhatsApp enviada al "
                            f"+{st.session_state.usuario['telefono']}",
                            icon="🟢"
                        )
                    else:
                        st.error(f"Error de Twilio: {resultado}")
                        estado_noti = "Fallo Twilio"

                    st.session_state.registro_diario.append({
                        "Hora": f"{hora}:00",
                        "Misión": tipo,
                        "Zona": zona_obj,
                        "Agua": f"{litros} L",
                        "Alerta": estado_noti
                    })

        with col_m:
            st.markdown("**Monitor de Vuelo: Tratamiento Focalizado**")

            mapa = folium.Map(
                location=st.session_state.centro_mapa,
                zoom_start=15,
                tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
                attr="Esri",
                zoom_control=False,
                scrollWheelZoom=False,
                dragging=False,
                touchZoom=False,
                doubleClickZoom=False
            )

            if "Zona Óptima" in zonas_dict:
                folium.Polygon(
                    locations=zonas_dict["Zona Óptima"],
                    color="green",
                    fill=True,
                    fill_opacity=0.4,
                    tooltip="Zona Óptima"
                ).add_to(mapa)

                folium.Polygon(
                    locations=zonas_dict["Zona Media"],
                    color="yellow",
                    fill=True,
                    fill_opacity=0.4,
                    tooltip="Zona Media"
                ).add_to(mapa)

                folium.Polygon(
                    locations=zonas_dict["Zona Crítica"],
                    color="red",
                    fill=True,
                    fill_opacity=0.4,
                    tooltip="Zona Crítica"
                ).add_to(mapa)

            if ruta_calculada:
                plugins.AntPath(
                    locations=ruta_calculada,
                    dash_array=[10, 20],
                    delay=800,
                    color=color_ruta,
                    weight=5,
                    pulse_color='white'
                ).add_to(mapa)

            st_folium(
                mapa,
                width=700,
                height=400,
                returned_objects=[]
            )

    # ==========================================
    # TAB 3: BITÁCORA
    # ==========================================
    with tab3:
        st.header("Bitácora")

        if st.session_state.registro_diario:
            st.dataframe(
                pd.DataFrame(st.session_state.registro_diario),
                use_container_width=True
            )
        else:
            st.info("Aún no hay operaciones registradas.")

        msg = (
            f"*REPORTE ENJAMBRE VRA*\n"
            f"Agua total hoy: {st.session_state.total_litros_hoy} L\n"
            f"Operaciones: {len(st.session_state.registro_diario)}"
        )

        link = (
            f"https://api.whatsapp.com/send?"
            f"phone={st.session_state.usuario['telefono']}"
            f"&text={urllib.parse.quote(msg)}"
        )

        st.markdown(
            f'<a href="{link}" target="_blank" class="whatsapp-btn">'
            f'📲 Enviar Reporte General por WhatsApp Web</a>',
            unsafe_allow_html=True
        )
