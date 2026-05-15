import streamlit as st
import folium
from folium import plugins
from streamlit_folium import st_folium
import time
import pandas as pd
from datetime import date
import urllib.parse
import requests
from twilio.rest import Client

# --- 1. CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="Enjambre VRA | Plataforma Integral",
    page_icon="🚁",
    layout="wide"
)

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

# --- MEMORIA DEL SISTEMA ---
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
# FUNCIÓN PARA OBTENER CLIMA REAL
# ==========================================
def obtener_clima_real(lat, lon):
    try:
        url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={lat}&longitude={lon}"
            f"&current_weather=true"
            f"&hourly=relative_humidity_2m"
        )

        respuesta = requests.get(url).json()

        temp = respuesta["current_weather"]["temperature"]
        viento = respuesta["current_weather"]["windspeed"]
        humedad = respuesta["hourly"]["relative_humidity_2m"][0]

        return {
            "temp": temp,
            "hum": humedad,
            "viento": viento
        }

    except:
        return {
            "temp": 13.8,
            "hum": 73,
            "viento": 1.7
        }


# ==========================================
# FUNCIÓN PARA ENVIAR WHATSAPP CON TWILIO
# ==========================================
def enviar_whatsapp_twilio(mensaje, telefono_destino):
    try:
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
# FUNCIÓN PARA CALCULAR RUTA DEL DRON
# ==========================================
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

        paso_lat = (max(lats) - min(lats)) / 4

        for i in range(5):
            lat_actual = max(lats) - (i * paso_lat)

            if i % 2 == 0:
                ruta.extend([
                    [lat_actual, min(lons)],
                    [lat_actual, max(lons)]
                ])
            else:
                ruta.extend([
                    [lat_actual, max(lons)],
                    [lat_actual, min(lons)]
                ])

    elif patron == "Espiral (Foco Central)":
        for i in range(1, 6):
            r = (0.001 / 5) * i
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

            submit = st.form_submit_button(
                "Ingresar al Sistema",
                type="primary",
                use_container_width=True
            )

            if submit and nombre and email and telefono:
                tel_limpio = ''.join(filter(str.isdigit, telefono))

                st.session_state.usuario = {
                    'nombre': nombre,
                    'email': email,
                    'telefono': tel_limpio
                }

                st.session_state.paso = 'onboarding_mapa'
                st.rerun()


# ==========================================
# FASE 2: MAPA
# ==========================================
elif st.session_state.paso == 'onboarding_mapa':
    st.header(
        f"Bienvenido {st.session_state.usuario['nombre']} - Delimitación Satelital"
    )

    st.write(
        "📍 **Paso 1:** Utilice la herramienta de polígono ⬠ para dibujar su parcela real."
    )

    mapa_dibujo = folium.Map(
        location=[-33.456, -70.650],
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

    st.write("📍 **Paso 2:** Ingrese el área total de la zona.")

    area_ingresada = st.number_input(
        "Área total del predio (m²):",
        min_value=100,
        max_value=1000000,
        value=5000,
        step=100
    )

    if st.button("Confirmar Terreno y Continuar ➡️", type="primary"):
        st.session_state.parcela_area = area_ingresada

        lat_clima, lon_clima = -33.456, -70.650

        if mapa_data and mapa_data.get("all_drawings"):
            dibujo = mapa_data["all_drawings"][0]
            st.session_state.poligono_coords = dibujo["geometry"]["coordinates"][0]

            coords_formateadas = [
                [p[1], p[0]]
                for p in st.session_state.poligono_coords
            ]

            pts_unicos = (
                coords_formateadas[:-1]
                if coords_formateadas[0] == coords_formateadas[-1]
                else coords_formateadas
            )

            st.session_state.centro_mapa = [
                sum(p[0] for p in pts_unicos) / len(pts_unicos),
                sum(p[1] for p in pts_unicos) / len(pts_unicos)
            ]

            lon_clima = st.session_state.poligono_coords[0][0]
            lat_clima = st.session_state.poligono_coords[0][1]

        st.session_state.clima_real = obtener_clima_real(lat_clima, lon_clima)
        st.session_state.paso = 'onboarding_cultivos'
        st.rerun()


# ==========================================
# FASE 3: CULTIVOS
# ==========================================
elif st.session_state.paso == 'onboarding_cultivos':
    st.header("🌾 Distribución de Plantaciones")

    st.write(
        f"Usted cuenta con un límite total de "
        f"**{st.session_state.parcela_area} m²** registrados."
    )

    cultivos_seleccionados = st.multiselect(
        "Seleccione cultivos presentes:",
        DB_CULTIVOS
    )

    if cultivos_seleccionados:
        area_asignada_total = 0
        asignaciones = {}

        for cultivo in cultivos_seleccionados:
            m2 = st.number_input(
                f"Asignar m² para {cultivo}:",
                min_value=0,
                max_value=st.session_state.parcela_area,
                value=0,
                step=100
            )

            asignaciones[cultivo] = m2
            area_asignada_total += m2

        st.progress(min(area_asignada_total / st.session_state.parcela_area, 1.0))

        st.write(
            f"Espacio utilizado: **{area_asignada_total} m²** "
            f"de **{st.session_state.parcela_area} m²**"
        )

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
    st.title(
        f"📊 Dashboard Enjambre VRA | Admin: {st.session_state.usuario['nombre']}"
    )

    with st.sidebar:
        st.header("🕒 Cronograma Operativo (Autónomo)")

        st.markdown(
            '<div class="horario-auto">💧 <b>05:30 AM</b> - Riego General</div>',
            unsafe_allow_html=True
        )

        st.markdown(
            '<div class="horario-auto">🧪 <b>08:00 AM</b> - Aplicación Vitaminas</div>',
            unsafe_allow_html=True
        )

        st.markdown(
            '<div class="horario-auto">🛡️ <b>06:00 PM</b> - Control Antiplagas</div>',
            unsafe_allow_html=True
        )

    tab1, tab2, tab3 = st.tabs([
        "🌱 1. Sensores y Suelo",
        "🚁 2. Logística Dron",
        "📈 3. Reporte y WhatsApp"
    ])

    # ==========================================
    # PESTAÑA 1: SENSORES Y SUELO
    # ==========================================
    with tab1:
        st.write("Datos extraídos en tiempo real de la zona satelital seleccionada.")

        clima_cols = st.columns(4)

        temp_real = st.session_state.clima_real["temp"]
        hum_real = st.session_state.clima_real["hum"]
        viento_real = st.session_state.clima_real["viento"]

        clima_cols[0].metric(
            "Temp. Zona Seleccionada",
            f"{temp_real}°C",
            "Sensory Data"
        )

        clima_cols[1].metric(
            "Humedad Ambiental",
            f"{hum_real}%",
            "IoT"
        )

        clima_cols[2].metric(
            "Velocidad de Viento",
            f"{viento_real} km/h",
            "Drone Safe" if viento_real < 25 else "-Riesgo Vuelo"
        )

        clima_cols[3].metric(
            "Radiación / Evaporación",
            "Alta" if temp_real > 26 else "Normal",
            "-Riesgo Foliar" if temp_real > 26 else "Óptimo"
        )

        st.markdown("---")

        nombres_cultivos = list(st.session_state.cultivos_asignados.keys())
        zonas = st.columns(3)

        if len(nombres_cultivos) > 0:
            with zonas[0]:
                st.markdown(
                    f'''
                    <div class="sensor-verde">
                    <b>Sector A: {nombres_cultivos[0]}</b><br>
                    Área: {st.session_state.cultivos_asignados[nombres_cultivos[0]]} m²<br>
                    Humedad Suelo: 68%<br>
                    Estado: Óptimo
                    </div>
                    ''',
                    unsafe_allow_html=True
                )

        if len(nombres_cultivos) > 1:
            with zonas[1]:
                st.markdown(
                    f'''
                    <div class="sensor-amarillo">
                    <b>Sector B: {nombres_cultivos[1]}</b><br>
                    Área: {st.session_state.cultivos_asignados[nombres_cultivos[1]]} m²<br>
                    Humedad Suelo: 45%<br>
                    Estado: Estrés leve
                    </div>
                    ''',
                    unsafe_allow_html=True
                )

        with zonas[2]:
            st.markdown(
                f'''
                <div class="sensor-rojo">
                <b>🚨 Zona de Riesgo</b><br>
                Humedad Suelo: {"22%" if hum_real > 40 else "15% (CRÍTICO)"}<br>
                Alerta hídrica<br>
                Requiere Atención
                </div>
                ''',
                unsafe_allow_html=True
            )

    # ==========================================
    # PESTAÑA 2: LOGÍSTICA DRON
    # ==========================================
    with tab2:
        st.header("Centro de Mando Logístico VRA")

        col_ctrl, col_map = st.columns([1, 2])

        ruta_calculada = []
        color_ruta = "cyan"

        with col_ctrl:
            st.subheader("Control Manual Excepcional")

            hora_actual = st.slider(
                "Reloj:",
                0,
                23,
                14,
                format="%d:00 hrs"
            )

            tipo_mision = st.radio(
                "Acción a ejecutar:",
                [
                    "Riego de Emergencia",
                    "Nutrición (Proteínas)",
                    "Tratamiento (Anti-plagas)"
                ]
            )

            patron_vuelo = st.selectbox(
                "Patrón de Despliegue Táctico:",
                [
                    "Zig-Zag (Cobertura Total)",
                    "Espiral (Foco Central)",
                    "Perimetral (Bordes)"
                ]
            )

            es_riesgoso = (
                tipo_mision == "Riego de Emergencia"
                and 10 <= hora_actual <= 18
            )

            boton_deshabilitado = False

            if es_riesgoso:
                st.error("⚠️ ADVERTENCIA: Riego diurno detectado (Efecto lupa).")

                if not st.checkbox("Declaro entender los riesgos y autorizo."):
                    boton_deshabilitado = True

            if st.button(
                "🚀 Forzar Despliegue",
                type="primary",
                disabled=boton_deshabilitado,
                use_container_width=True
            ):
                if tipo_mision == "Riego de Emergencia":
                    litros_usados = st.session_state.parcela_area * 0.5
                else:
                    litros_usados = 0

                st.session_state.total_litros_hoy += litros_usados

                if tipo_mision == "Riego de Emergencia":
                    color_ruta = "cyan"
                elif tipo_mision == "Nutrición (Proteínas)":
                    color_ruta = "orange"
                else:
                    color_ruta = "red"

                ruta_calculada = calcular_ruta_patron(
                    st.session_state.poligono_coords,
                    patron_vuelo,
                    st.session_state.centro_mapa[0],
                    st.session_state.centro_mapa[1]
                )

                with st.spinner(
                    f"Transmitiendo patrón {patron_vuelo} al dron..."
                ):
                    time.sleep(2)

                    st.success(f"✅ Dron en vuelo. Patrón: {patron_vuelo}")

                    if litros_usados > 0:
                        st.info(f"💧 Agua calculada: {litros_usados} L.")

                    st.toast(
                        f"📧 Correo SMTP enviado a {st.session_state.usuario['email']}",
                        icon="✅"
                    )

                    st.session_state.registro_diario.append({
                        "Hora": f"{hora_actual}:00",
                        "Misión": tipo_mision,
                        "Patrón": patron_vuelo,
                        "Agua Usada": f"{litros_usados} L",
                        "Estado": "Completado"
                    })

        with col_map:
            st.markdown(
                "**Monitor de Vuelo: Estrés Hídrico Intra-Parcela Zonal**"
            )

            mapa_dron = folium.Map(
                location=st.session_state.centro_mapa,
                zoom_start=15,
                tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
                attr="Esri",
                zoom_control=False,
                scrollWheelZoom=False,
                dragging=False,
                touchZoom=False,
                doubleClickZoom=False,
                keyboard=False
            )

            if st.session_state.poligono_coords:
                coords_formateadas = [
                    [p[1], p[0]]
                    for p in st.session_state.poligono_coords
                ]

                pts = (
                    coords_formateadas[:-1]
                    if coords_formateadas[0] == coords_formateadas[-1]
                    else coords_formateadas
                )

                n = len(pts)

                if n >= 3:
                    c_lat, c_lon = st.session_state.centro_mapa
                    centroide = [c_lat, c_lon]

                    t1 = n // 3
                    t2 = 2 * (n // 3)

                    zona_verde = [centroide] + pts[0:t1 + 1] + [centroide]
                    zona_amarilla = [centroide] + pts[t1:t2 + 1] + [centroide]
                    zona_roja = [centroide] + pts[t2:] + [pts[0], centroide]

                    folium.Polygon(
                        locations=zona_verde,
                        color="green",
                        fill=True,
                        fill_color="green",
                        fill_opacity=0.45,
                        tooltip="Zona Óptima: 68% Humedad"
                    ).add_to(mapa_dron)

                    folium.Polygon(
                        locations=zona_amarilla,
                        color="yellow",
                        fill=True,
                        fill_color="yellow",
                        fill_opacity=0.45,
                        tooltip="Zona Media: 45% Humedad"
                    ).add_to(mapa_dron)

                    folium.Polygon(
                        locations=zona_roja,
                        color="red",
                        fill=True,
                        fill_color="red",
                        fill_opacity=0.45,
                        tooltip="Zona Crítica: 22% Humedad"
                    ).add_to(mapa_dron)

                else:
                    folium.Polygon(
                        locations=coords_formateadas,
                        color="red",
                        fill=True,
                        fill_opacity=0.4
                    ).add_to(mapa_dron)

            if ruta_calculada:
                plugins.AntPath(
                    locations=ruta_calculada,
                    dash_array=[10, 20],
                    delay=800,
                    color=color_ruta,
                    weight=5,
                    pulse_color='white'
                ).add_to(mapa_dron)

            st_folium(
                mapa_dron,
                width=700,
                height=400,
                returned_objects=[]
            )

    # ==========================================
    # PESTAÑA 3: REPORTE Y WHATSAPP CON TWILIO
    # ==========================================
    with tab3:
        st.header("Bitácora y Costos")

        if st.session_state.registro_diario:
            st.dataframe(
                pd.DataFrame(st.session_state.registro_diario),
                use_container_width=True
            )
        else:
            st.write("Aún no se han registrado vuelos hoy.")

        st.markdown("---")
        st.subheader("📲 Exportación Automática")

        resumen_texto = f"""*REPORTE ENJAMBRE VRA* 🚁🌱
Gerente: {st.session_state.usuario['nombre']}
Área cubierta: {st.session_state.parcela_area} m2
💧 *Agua Utilizada Hoy: {st.session_state.total_litros_hoy} Litros*
Estado: ESTABLE ✅"""

        st.text_area(
            "Mensaje a enviar:",
            value=resumen_texto,
            height=150,
            disabled=True
        )

        st.info(
            "Este botón envía el reporte directamente por WhatsApp usando Twilio."
        )

        if st.button(
            "📲 Enviar Reporte por WhatsApp con Twilio",
            type="primary",
            use_container_width=True
        ):
            exito, resultado = enviar_whatsapp_twilio(
                resumen_texto,
                st.session_state.usuario["telefono"]
            )

            if exito:
                st.success("✅ Reporte enviado correctamente por WhatsApp.")
                st.caption(f"ID del mensaje Twilio: {resultado}")
            else:
                st.error("❌ No se pudo enviar el mensaje por Twilio.")
                st.code(resultado)

        st.markdown("---")
        st.caption(
            "Recuerda que el número ingresado debe tener formato internacional. "
            "Ejemplo Chile: 56912345678."
        )
