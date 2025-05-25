import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_autorefresh import st_autorefresh
from firebase import get_data, init_firebase

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
        st.image("logo.png", width=100)

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
            if datos_htcc:
                st.markdown("**HTCC-AB01**")
                estado_htcc = evaluar_estado_sensor(get_data("/ultimo/usr1/cube-cell/fecha"), 25)
                st.write(f"📶 Estado: **{estado_htcc}**")

                st.metric("💧 Humedad Suelo", f"{datos_htcc.get('Humedad', 'N/A')} %")
                st.metric("🌫 MQ7 Humo", f"{datos_htcc.get('HumoMQ7', 'N/A')} %")
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
                # Extraer los valores de sensor_data y usarlos como DataFrame
                registros = {}
                for timestamp, contenido in datos_hist.items():
                    if "sensor_data" in contenido:
                        registros[timestamp] = contenido["sensor_data"]

                # Convertir a DataFrame
                df = pd.DataFrame.from_dict(registros, orient="index")
                df.index = pd.to_datetime(df.index)
                df = df.sort_index()

                # Mostrar gráficos de líneas
                st.plotly_chart(px.line(df, y="TempC1", title="Temperatura (°C) - LSN50"), use_container_width=True)
                st.plotly_chart(px.line(df, y="BatV", title="Nivel de Batería (V) - LSN50"), use_container_width=True)
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

                # Mostrar gráficos de líneas
                st.plotly_chart(px.line(df, y="Humedad", title="Humedad (%) - CubeCell"), use_container_width=True)
                st.plotly_chart(px.line(df, y="UV", title="Radiación UV - CubeCell"), use_container_width=True)
                st.plotly_chart(px.line(df, y="HumoMQ7", title="Sensor MQ7 - CubeCell"), use_container_width=True)
            else:
                st.warning("⚠️ Sin datos históricos CubeCell.")
         
        with tab3:
            st.subheader("📶 Calidad de Conexión - RSSI / SNR")

            datos_lsn = get_data("/historico/usr1/lsn50")
            datos_htcc = get_data("/historico/usr1/cube-cell")

            # Indicadores últimos valores
            def evaluar_calidad_conexion(rssi, snr):
                if rssi is not None:
                    if rssi > -90:
                        estado_rssi = "🟢 Fuerte"
                    elif rssi > -110:
                        estado_rssi = "🟠 Media"
                    else:
                        estado_rssi = "🔴 Débil"
                else:
                    estado_rssi = "❌ N/D"

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

            df_lsn = extraer_signal_quality(datos_lsn)
            df_htcc = extraer_signal_quality(datos_htcc)

            if not df_lsn.empty:
                st.subheader("📍 Últimos Indicadores")
                col1, col2 = st.columns(2)

                with col1:
                    rssi_lsn = df_lsn["rssi"].iloc[-1]
                    snr_lsn = df_lsn["snr"].iloc[-1]
                    estado_rssi_lsn, estado_snr_lsn = evaluar_calidad_conexion(rssi_lsn, snr_lsn)

                    st.metric("📡 LSN50 RSSI", f"{rssi_lsn} dBm")
                    st.write(f"Estado RSSI: {estado_rssi_lsn}")
                    st.metric("📶 LSN50 SNR", f"{snr_lsn} dB")
                    st.write(f"Estado SNR: {estado_snr_lsn}")

                if not df_htcc.empty:
                    with col2:
                        rssi_htcc = df_htcc["rssi"].iloc[-1]
                        snr_htcc = df_htcc["snr"].iloc[-1]
                        estado_rssi_htcc, estado_snr_htcc = evaluar_calidad_conexion(rssi_htcc, snr_htcc)

                        st.metric("📡 HTCC RSSI", f"{rssi_htcc} dBm")
                        st.write(f"Estado RSSI: {estado_rssi_htcc}")
                        st.metric("📶 HTCC SNR", f"{snr_htcc} dB")
                        st.write(f"Estado SNR: {estado_snr_htcc}")

            # Gráficas RSSI/SNR individuales
            if not df_lsn.empty:
                st.plotly_chart(px.line(df_lsn, y="rssi", title="📡 RSSI - LSN50"), use_container_width=True)
                st.plotly_chart(px.line(df_lsn, y="snr", title="📶 SNR - LSN50"), use_container_width=True)
            else:
                st.warning("⚠️ No hay datos históricos o de señal para LSN50.")

            if not df_htcc.empty:
                st.plotly_chart(px.line(df_htcc, y="rssi", title="📡 RSSI - HTCC"), use_container_width=True)
                st.plotly_chart(px.line(df_htcc, y="snr", title="📶 SNR - HTCC"), use_container_width=True)
            else:
                st.warning("⚠️ No hay datos históricos o de señal para HTCC.")

            # Comparativa RSSI
            if not df_lsn.empty and not df_htcc.empty:
                # Asegúrate de que el índice contiene las fechas (y es de tipo datetime)
                df_lsn.index = pd.to_datetime(df_lsn.index)
                df_htcc.index = pd.to_datetime(df_htcc.index)

                # Combinar los DataFrames en uno solo con fechas como índice
                df_comp = pd.concat([
                    df_lsn[["rssi"]].rename(columns={"rssi": "RSSI_LSN50"}),
                    df_htcc[["rssi"]].rename(columns={"rssi": "RSSI_HTCC"})
                ], axis=1)

                df_comp = df_comp.reset_index().rename(columns={"index": "Fecha"})

                # Derretimos el DataFrame para que Plotly lo interprete mejor
                df_melt = df_comp.melt(id_vars="Fecha", var_name="Nodo", value_name="RSSI")

                # Paleta de colores personalizada
                color_map = {
                    "RSSI_LSN50": "#1f77b4",  # azul
                    "RSSI_HTCC": "#d62728"    # rojo
                }

                # Restablecer el índice (las fechas) como columna
                df_comp = df_comp.reset_index().rename(columns={"index": "Fecha"})

                # Crear la gráfica
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


