from fastapi import FastAPI, Request
import uvicorn
import os
import ngrok
import threading
from dotenv import load_dotenv
from datetime import datetime
import pytz
from firebase import init_firebase, get_db_ref  # Importa funciones desde firebase.py

# Cargar variables de entorno
load_dotenv()

# Inicializar Firebase si aún no se ha hecho
init_firebase()

# Crear instancia de FastAPI
app = FastAPI()

# Zona horaria Colombia
colombia_tz = pytz.timezone("America/Bogota")

@app.get("/")
async def root():
    return {"message": "Hola desde la API!"}

@app.post("/uplink")
async def uplink_handler(request: Request):
    body = await request.json()
    print("📡 Datos recibidos de TTN:", body)

    # Obtener el ID del dispositivo que envió los datos
    device_id = body.get("end_device_ids", {}).get("device_id", "desconocido")

    # Extraer payload decodificado
    payload = body.get("uplink_message", {}).get("decoded_payload", {})

    # Validación del payload
    if "Humedad" not in payload or "HumoMQ7" not in payload or "UV" not in payload:
        return {"status": "error", "message": "Datos incompletos", "device": device_id}

    # Obtener fecha y hora actual en zona horaria de Colombia
    colombia_time = datetime.now(colombia_tz)
    valid_time = colombia_time.strftime("%Y%m%dT%H%M%S")

    # Ruta del histórico: /historico/usr1/{device_id}/{fecha}
    historico_ref = get_db_ref(f"/historico/usr1/{device_id}")
    if historico_ref:
        historico_ref.child(valid_time).set(payload)
        print("✅ Datos guardados en histórico.")

    # Ruta del último dato: /ultimo/usr1/{device_id}
    ultimo_ref = get_db_ref(f"/ultimo/usr1/{device_id}")
    if ultimo_ref:
        payload_con_fecha = payload.copy()
        payload_con_fecha["fecha"] = valid_time  # añade timestamp al último payload
        ultimo_ref.set(payload_con_fecha)
        print("🆕 Último dato actualizado.")

    return {"status": "ok", "device": device_id, "carga": payload}


# Función para iniciar ngrok
def start_ngrok():
    auth_token = os.getenv("NGROK_AUTH_TOKEN")
    if auth_token:
        ngrok.set_auth_token(auth_token)
        listener = ngrok.connect(8000)
        print(f"🌐 Tu API está disponible públicamente en: {listener.url()}")
    else:
        print("❌ No se encontró el token de ngrok en el archivo .env")

# Ejecutar FastAPI y ngrok
if __name__ == "__main__":
    threading.Thread(target=start_ngrok, daemon=True).start()
    uvicorn.run("main:app", host="127.0.0.1", port=8000)
