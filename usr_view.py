import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_autorefresh import st_autorefresh
from firebase import get_data, init_firebase

import plotly.graph_objects as go

from datetime import datetime, timezone


# Inicializar Firebase
init_firebase()

def mostrar_vista_principal():
    # 🔄 Refrescar cada 10 segundos (10000 ms)
    st_autorefresh(interval=10000, key="data_refresh")

    st.title("🌾 Dashboard Agro Inteligente")

    # Botón de logout
    with st.sidebar:

        # Cargar imagen desde archivo local
        st.image("logo.png", width=80)

        st.write(f"👤 Usuario: `{st.session_state.username}`")
        if st.button("🚪 Cerrar sesión"):
            st.session_state.auth_status = False
            st.session_state.username = ""
            st.rerun()

        st.markdown("## 📊 Últimos valores sensores:")
        with st.container(height=300, border=False):
            datos_lsn = get_data("/ultimo/usr1/lsn50/sensor_data")
            if datos_lsn:
                st.markdown("**LSN50**")
                estado_lsn = evaluar_estado_sensor(get_data("/ultimo/usr1/lsn50/fecha"), 30)
                st.write(f"📶 Estado: **{estado_lsn}**")

                st.metric("🌡 TempC1", f"{datos_lsn.get('TempC1', 'N/A')} °C")
                st.metric("🔋 BatV", f"{datos_lsn.get('BatV', 'N/A')} V")
            else:
                st.write("❌ No hay datos LSN50")

            datos_htcc = get_data("/ultimo/usr1/cube-cell/sensor_data")
            humedad = datos_htcc.get("Humedad", None)
            humo = datos_htcc.get("HumoMQ7", None)

            if datos_htcc:
                st.markdown("**HTCC-AB01**")
                estado_htcc = evaluar_estado_sensor(get_data("/ultimo/usr1/cube-cell/fecha"), 25)
                st.write(f"📶 Estado: **{estado_htcc}**")

                # Indicador de Humedad (barra de progreso)
                if humedad is not None:
                    humedad_valor = float(humedad)
                    st.markdown(f"💧 **Humedad Suelo: {humedad_valor:.0f}%**")
                    st.progress(min(max(int(humedad_valor), 0), 100))
                else:
                    st.markdown("💧 **Humedad Suelo: N/A**")

                # Indicador de Humo (barra de progreso)
                if humo is not None:
                    humo_valor = float(humo)
                    st.markdown(f"🌫 **MQ7 Humo: {humo_valor:.0f}%**")
                    st.progress(min(max(int(humo_valor), 0), 100))
                else:
                    st.markdown("🌫 **MQ7 Humo: N/A**")

                st.metric("🌞 UV", f"{datos_htcc.get('UV', 'N/A')} Lux")
            else:
                st.write("❌ No hay datos HTCC")

    col1, col2 = st.columns([2, 5])

    with col1:
        st.subheader("📅 Historial Reciente")
        st.write("Se muestra el historial de los sensores conectados a la red TTN.")

    with col2:
        tab1, tab2, tab3 = st.tabs(["📈 LSN50", "📉 HTCC-AB01", "📶 Señal"])

        with tab1:
            datos_hist = get_data("/historico/usr1/lsn50")

            if datos_hist:
                # Extraer datos de sensor_data y convertir a DataFrame
                registros = {
                    timestamp: contenido["sensor_data"]
                    for timestamp, contenido in datos_hist.items()
                    if "sensor_data" in contenido
                }

                df = pd.DataFrame.from_dict(registros, orient="index")
                df.index = pd.to_datetime(df.index)
                df = df.sort_index()

                # Agregamos columna 'Fecha' y 'Hora'
                df["Fecha"] = df.index.date
                df["Hora"] = df.index.hour

                # Selectbox para seleccionar día disponible
                fechas_disponibles = sorted(df["Fecha"].unique(), reverse=False)
                fecha_seleccionada = st.selectbox(
                    "📅 Selecciona el día", 
                    fechas_disponibles,
                    index=1  # el primer elemento (más reciente) se selecciona por defecto
                )

                # Selectbox para seleccionar periodo del día
                # Último dato disponible en el DataFrame
                hora_ultimo_dato = df.index[-1].hour

                # Determinar franja por hora
                franja_default = "Mañana" if hora_ultimo_dato < 12 else "Tarde"

                franja_seleccionada = st.selectbox(
                    "🕒 Selecciona la franja horaria",
                    ["Mañana", "Tarde"],
                    index=0 if franja_default == "Mañana" else 1
                )


                if franja_seleccionada.startswith("Mañana"):
                    df_filtrado = df[(df["Fecha"] == fecha_seleccionada) & (df["Hora"] < 12)]
                else:
                    df_filtrado = df[(df["Fecha"] == fecha_seleccionada) & (df["Hora"] >= 12)]

                # Mostrar gráficas solo si hay datos en ese periodo
                if not df_filtrado.empty:
                    if "TempC1" in df_filtrado.columns and df_filtrado["TempC1"].notnull().any():
                        fig_temp = px.line(
                            df_filtrado,
                            x=df_filtrado.index,
                            y="TempC1",
                            title="🌡 Temperatura (°C) - LSN50",
                            markers=True,
                            line_shape="linear",
                            color_discrete_sequence=["#FF6B6B"]  # rojo suave
                        )
                        st.plotly_chart(fig_temp, use_container_width=True)
                    else:
                        st.info("No hay datos de temperatura disponibles para este rango.")

                    if "BatV" in df_filtrado.columns and df_filtrado["BatV"].notnull().any():
                        fig_bat = px.line(
                            df_filtrado,
                            x=df_filtrado.index,
                            y="BatV",
                            title="🔋 Nivel de Batería (V) - LSN50",
                            markers=True,
                            line_shape="linear",
                            color_discrete_sequence=["#4BC0C0"]  # azul verdoso
                        )
                        st.plotly_chart(fig_bat, use_container_width=True)
                    else:
                        st.info("No hay datos de batería disponibles para este rango.")
                else:
                    st.warning("⚠️ No hay datos en este día y periodo seleccionados.")
            else:
                st.warning("⚠️ Sin datos históricos LSN50.")



        with tab2:
            datos_hist = get_data("/historico/usr1/cube-cell")  # actualiza el endpoint

            if datos_hist:
                # Extraer los valores de sensor_data y usarlos como DataFrame
                registros = {}
                for timestamp, contenido in datos_hist.items():
                    if "sensor_data" in contenido:
                        registros[timestamp] = contenido["sensor_data"]

                # Convertir a DataFrame
                df = pd.DataFrame.from_dict(registros, orient="index")
                df.index = pd.to_datetime(df.index)
                df = df.sort_index()

                # Obtener fechas únicas disponibles en el DataFrame
                fechas_disponibles = df.index.date
                fechas_unicas = sorted(set(fechas_disponibles))

                # Obtener fecha del último dato
                fecha_ultimo_dato = df.index[-1].date()
                hora_ultimo_dato = df.index[-1].hour

                # Determinar franja por hora
                franja_default = "Mañana" if hora_ultimo_dato < 12 else "Tarde"

                # Selectboxes para filtros
                fecha_seleccionada = st.selectbox(
                    "📅 Selecciona la fecha",
                    fechas_unicas,
                    index=fechas_unicas.index(fecha_ultimo_dato),
                    key="fecha_cubecell"
                )

                franja_seleccionada = st.selectbox(
                    "🕒 Selecciona la franja horaria",
                    ["Mañana", "Tarde"],
                    index=0 if franja_default == "Mañana" else 1,
                    key="franja_cubecell"
                )

                # Definir el rango de horas según la franja
                if franja_seleccionada == "Mañana":
                    hora_inicio = 0
                    hora_fin = 11
                else:
                    hora_inicio = 12
                    hora_fin = 23

                # Filtrar el DataFrame según la fecha y la franja horaria
                df_filtrado = df[
                    (df.index.date == fecha_seleccionada) &
                    (df.index.hour >= hora_inicio) &
                    (df.index.hour <= hora_fin)
                ]

                if df_filtrado.empty:
                    st.info("ℹ️ No hay datos para esta fecha y franja horaria.")
                else:
                    # Gráficas con colores personalizados y marcadores
                    color_humedad = "#17BECF"  # celeste
                    color_uv = "#9467BD"       # morado
                    color_mq7 = "#8C564B"      # marrón

                    fig_hum = px.line(
                        df_filtrado,
                        y="Humedad",
                        title="💧 Humedad (%) - CubeCell",
                        markers=True
                    )
                    fig_hum.update_traces(line=dict(color=color_humedad))

                    fig_uv = px.line(
                        df_filtrado,
                        y="UV",
                        title="☀️ Radiación UV - CubeCell",
                        markers=True
                    )
                    fig_uv.update_traces(line=dict(color=color_uv))

                    fig_mq7 = px.line(
                        df_filtrado,
                        y="HumoMQ7",
                        title="🚬 Sensor MQ7 - CubeCell",
                        markers=True
                    )
                    fig_mq7.update_traces(line=dict(color=color_mq7))

                    # Mostrar gráficos
                    st.plotly_chart(fig_hum, use_container_width=True)
                    st.plotly_chart(fig_uv, use_container_width=True)
                    st.plotly_chart(fig_mq7, use_container_width=True)

            else:
                st.warning("⚠️ Sin datos históricos CubeCell.")

         
        with tab3:
            st.subheader("📶 Calidad de Conexión - RSSI / SNR")

            # Cargar datos
            datos_lsn = get_data("/historico/usr1/lsn50")
            datos_htcc = get_data("/historico/usr1/cube-cell")

            df_lsn = extraer_signal_quality(datos_lsn)
            df_htcc = extraer_signal_quality(datos_htcc)

            # Unificar fechas para selección
            fechas_disponibles = sorted(
                list(set(df_lsn.index.date) | set(df_htcc.index.date)),
                reverse=True
            )

            if fechas_disponibles:
                # Filtros de selección
                fecha_default = max(fechas_disponibles)
                fecha_seleccionada = st.selectbox(
                    "📅 Selecciona la fecha",
                    fechas_disponibles,
                    index=0,
                    format_func=lambda x: x.strftime("%Y-%m-%d"),
                    key="fecha_tab3"
                )

                # Definir franja horaria por hora
                df_todos = pd.concat([df_lsn, df_htcc]).sort_index()
                ultima_hora = df_todos.index[-1].hour
                franja_default = "Mañana" if ultima_hora < 13 else "Tarde"

                franja_seleccionada = st.selectbox(
                    "🕒 Selecciona la franja horaria",
                    ["Mañana", "Tarde"],
                    index=0 if franja_default == "Mañana" else 1,
                    key="franja_tab3"
                )

                hora_min = 0 if franja_seleccionada == "Mañana" else 13
                hora_max = 12 if franja_seleccionada == "Mañana" else 23

                # Filtrar por fecha y franja horaria
                def filtrar(df):
                    return df[
                        (df.index.date == fecha_seleccionada) &
                        (df.index.hour >= hora_min) & (df.index.hour <= hora_max)
                    ]

                df_lsn_filtrado = filtrar(df_lsn)
                df_htcc_filtrado = filtrar(df_htcc)

                # 📍 Indicadores de calidad (último dato disponible en esa franja)
                if not df_lsn_filtrado.empty:
                    st.subheader("📍 Últimos Indicadores")

                    col1, col2 = st.columns(2)

                    with col1:
                        rssi_lsn = df_lsn_filtrado["rssi"].iloc[-1]
                        snr_lsn = df_lsn_filtrado["snr"].iloc[-1]
                        estado_rssi_lsn, estado_snr_lsn = evaluar_calidad_conexion(rssi_lsn, snr_lsn)

                        st.metric("📡 LSN50 RSSI", f"{rssi_lsn} dBm")
                        st.write(f"Estado RSSI: {estado_rssi_lsn}")
                        st.metric("📶 LSN50 SNR", f"{snr_lsn} dB")
                        st.write(f"Estado SNR: {estado_snr_lsn}")

                    if not df_htcc_filtrado.empty:
                        with col2:
                            rssi_htcc = df_htcc_filtrado["rssi"].iloc[-1]
                            snr_htcc = df_htcc_filtrado["snr"].iloc[-1]
                            estado_rssi_htcc, estado_snr_htcc = evaluar_calidad_conexion(rssi_htcc, snr_htcc)

                            st.metric("📡 HTCC RSSI", f"{rssi_htcc} dBm")
                            st.write(f"Estado RSSI: {estado_rssi_htcc}")
                            st.metric("📶 HTCC SNR", f"{snr_htcc} dB")
                            st.write(f"Estado SNR: {estado_snr_htcc}")

                # 📈 Gráficas individuales
                if not df_lsn_filtrado.empty:
                    st.plotly_chart(px.line(
                        df_lsn_filtrado, y="rssi", title="📡 RSSI - LSN50", markers=True,
                        color_discrete_sequence=["#1f77b4"]
                    ), use_container_width=True)

                    st.plotly_chart(px.line(
                        df_lsn_filtrado, y="snr", title="📶 SNR - LSN50", markers=True,
                        color_discrete_sequence=["#2ca02c"]
                    ), use_container_width=True)
                else:
                    st.warning("⚠️ No hay datos históricos para LSN50 en esa franja.")

                if not df_htcc_filtrado.empty:
                    st.plotly_chart(px.line(
                        df_htcc_filtrado, y="rssi", title="📡 RSSI - HTCC", markers=True,
                        color_discrete_sequence=["#d62728"]
                    ), use_container_width=True)

                    st.plotly_chart(px.line(
                        df_htcc_filtrado, y="snr", title="📶 SNR - HTCC", markers=True,
                        color_discrete_sequence=["#9467bd"]
                    ), use_container_width=True)
                else:
                    st.warning("⚠️ No hay datos históricos para HTCC en esa franja.")

                # 📊 Comparativa RSSI
                if not df_lsn_filtrado.empty and not df_htcc_filtrado.empty:
                    df_comp = pd.concat([
                        df_lsn_filtrado[["rssi"]].rename(columns={"rssi": "RSSI_LSN50"}),
                        df_htcc_filtrado[["rssi"]].rename(columns={"rssi": "RSSI_HTCC"})
                    ], axis=1)

                    df_comp = df_comp.reset_index().rename(columns={"index": "Fecha"})

                    df_melt = df_comp.melt(id_vars="Fecha", var_name="Nodo", value_name="RSSI")

                    color_map = {
                        "RSSI_LSN50": "#1f77b4",
                        "RSSI_HTCC": "#d62728"
                    }

                    fig = px.line(
                        df_melt,
                        x="Fecha",
                        y="RSSI",
                        color="Nodo",
                        color_discrete_map=color_map,
                        title="📊 Comparativa RSSI entre nodos",
                        markers=True
                    )
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("⚠️ No hay datos disponibles para mostrar en esta pestaña.")






def evaluar_estado_sensor(fecha_str, umbral_segundos):
    if not fecha_str:
        return "❌ Sin datos"
    try:
        fecha_dato = datetime.fromisoformat(fecha_str)  # o usa `pd.to_datetime` si te falla
        ahora = datetime.now(timezone.utc)
        diferencia = (ahora - fecha_dato).total_seconds()
        if diferencia <= umbral_segundos:
            return "🟢 En línea"
        elif diferencia <= umbral_segundos * 1.2:
            return "🟠 Retrasado"
        else:
            return "🔴 Desconectado"
    except Exception as e:
        return f"⚠️ Error ({e})"


def evaluar_calidad_conexion(rssi, snr):
    # Evaluar calidad de RSSI
    if rssi is not None:
        if rssi > -90:
            estado_rssi = "🟢 Fuerte"
        elif rssi > -110:
            estado_rssi = "🟠 Media"
        else:
            estado_rssi = "🔴 Débil"
    else:
        estado_rssi = "❌ N/D"

    # Evaluar calidad de SNR
    if snr is not None:
        if snr > 5:
            estado_snr = "🟢 Buena"
        elif snr > -5:
            estado_snr = "🟠 Media"
        else:
            estado_snr = "🔴 Mala"
    else:
        estado_snr = "❌ N/D"

    return estado_rssi, estado_snr

def extraer_signal_quality(datos):
                """
                Extrae 'rssi' y 'snr' de 'signal_quality' y devuelve DataFrame con índice datetime.
                """
                if not datos:
                    return pd.DataFrame()

                registros = {}
                for timestamp, contenido in datos.items():
                    if "signal_quality" in contenido:
                        # Extraer rssi y snr
                        signal = contenido["signal_quality"]
                        registros[timestamp] = {
                            "rssi": signal.get("rssi", None),
                            "snr": signal.get("snr", None)
                        }

                df = pd.DataFrame.from_dict(registros, orient="index")
                df.index = pd.to_datetime(df.index)
                df = df.sort_index()
                return df


