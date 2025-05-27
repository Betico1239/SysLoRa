import firebase_admin
from firebase_admin import credentials, db
import os
import json

_app = None

def init_firebase():
    global _app
    if not firebase_admin._apps:
        try:
            key_json_str = os.getenv("FIREBASE_KEY_JSON")
            key_dict = json.loads(key_json_str)
            cred = credentials.Certificate(key_dict)
            _app = firebase_admin.initialize_app(cred, {
                'databaseURL': 'https://syslora2025-default-rtdb.firebaseio.com'
            })
            print("✅ Firebase inicializado correctamente.")
        except Exception as e:
            print(f"❌ Error al inicializar Firebase: {e}")

def get_db_ref(path="/"):
    try:
        return db.reference(path)
    except Exception as e:
        print(f"❌ Error al obtener referencia de {path}: {e}")
        return None

def get_data(path="/"):
    try:
        ref = db.reference(path)
        return ref.get()
    except Exception as e:
        print(f"❌ Error al obtener datos de {path}: {e}")
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
