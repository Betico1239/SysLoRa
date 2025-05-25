import streamlit as st
from auth import load_users, authenticate_user



# Estado inicial de sesión
if "auth_status" not in st.session_state:
    st.session_state.auth_status = False
    st.session_state.username = ""



# Configuración de la página
st.set_page_config(page_title="SysLoRa Dashboard", page_icon="logo.png", layout="wide")

# Ocultar el menú, la barra de Streamlit y el footer
hide_streamlit_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

if not st.session_state.auth_status:

    # Cargar imagen desde archivo local
    st.image("logo.png", width=100)

    st.title("🔐 Ingreso al sistema Lora TTN")

    username = st.text_input("Usuario")
    password = st.text_input("Contraseña", type="password")

    if st.button("Ingresar"):
        users = load_users()
        if authenticate_user(username, password, users):
            st.session_state.auth_status = True
            st.session_state.username = username
            st.success("✅ Acceso concedido.")
            st.rerun()
        else:
            st.error("❌ Credenciales incorrectas.")
else:
    # Si ya está autenticado, cargar la vista principal
    from usr_view import mostrar_vista_principal
    mostrar_vista_principal()
