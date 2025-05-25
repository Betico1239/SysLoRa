import firebase_admin
from firebase_admin import credentials, db

import json
import streamlit as st

_app = None  # Interno para controlar inicialización

def init_firebase():
    global _app
    if not firebase_admin._apps:
        # Leer el string JSON del secret
        firebase_key_str = st.secrets["firebase"]["service_account_json"]
        firebase_key_dict = json.loads(firebase_key_str)

        cred = credentials.Certificate(firebase_key_dict)
        _app = firebase_admin.initialize_app(cred, {
            'databaseURL': 'https://syslora2025-default-rtdb.firebaseio.com'
        })

def get_db_ref(path="/"):
    """Devuelve una referencia a una ruta en la base de datos de Firebase."""
    try:
        return db.reference(path)
    except Exception as e:
        print(f"Error al obtener referencia de {path}: {e}")
        return None

def get_data(path="/"):
    try:
        ref = db.reference(path)
        return ref.get()
    except Exception as e:
        print(f"Error al obtener datos de {path}: {e}")
        return None

def check_connection():
    try:
        ref = db.reference("/")
        ref.get()
        print("✅ Conexión a Firebase exitosa.")
        return True
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return False
