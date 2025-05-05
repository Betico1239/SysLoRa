import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_autorefresh import st_autorefresh
from firebase import get_data, init_firebase

init_firebase()


def mostrar_vista_principal():
    # 🔄 Refrescar cada 10 segundos (10000 ms)
    st_autorefresh(interval=10000, key="data_refresh")

    st.title("🌾 Dashboard Agro Inteligente")

    # Botón de logout
    with st.sidebar:
        st.write(f"👤 Usuario: `{st.session_state.username}`")
        if st.button("🚪 Cerrar sesión"):
            st.session_state.auth_status = False
            st.session_state.username = ""
            st.rerun()

        st.markdown("## 📊 Últimos valores sensores:")
        with st.container(height=300, border=False):
            datos_lsn = get_data("/ultimo/usr1/lsn50")
            if datos_lsn:
                st.markdown("**LSN50**")
                st.metric("🌡 TempC1", f"{datos_lsn.get('TempC1', 'N/A')} °C")
                st.metric("🔋 BatV", f"{datos_lsn.get('BatV', 'N/A')} V")
            else:
                st.write("❌ No hay datos LSN50")

            datos_htcc = get_data("/ultimo/usr1/cube-cell")
            if datos_htcc:
                st.markdown("**HTCC-AB01**")
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
        tab1, tab2 = st.tabs(["📈 LSN50", "📉 HTCC-AB01"])

        with tab1:
            datos_hist = get_data("/historico/usr1/lsn50")
            if datos_hist:
                df = pd.DataFrame.from_dict(datos_hist, orient="index")
                df.index = pd.to_datetime(df.index)
                df = df.sort_index()
                st.plotly_chart(px.line(df, y="TempC1", title="Temperatura (°C) - LSN50"), use_container_width=True)
                st.plotly_chart(px.line(df, y="BatV", title="Nivel de Batería (V) - LSN50"), use_container_width=True)
            else:
                st.warning("⚠️ Sin datos históricos LSN50.")

        with tab2:
            datos_hist = get_data("/historico/usr1/cube-cell")
            if datos_hist:
                df = pd.DataFrame.from_dict(datos_hist, orient="index")
                df.index = pd.to_datetime(df.index)
                df = df.sort_index()
                st.plotly_chart(px.line(df, y="Humedad", title="Humedad Suelo (%)"), use_container_width=True)
                st.plotly_chart(px.line(df, y="HumoMQ7", title="Sensor MQ7 (%)"), use_container_width=True)
                st.plotly_chart(px.line(df, y="UV", title="UV (lux)"), use_container_width=True)
            else:
                st.warning("⚠️ Sin datos históricos HTCC.")
