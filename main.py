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

    device_id = body.get("end_device_ids", {}).get("device_id", "desconocido")
    payload = body.get("uplink_message", {}).get("decoded_payload", {})

    # Extraer rx_metadata si existe
    rx_metadata = body.get("uplink_message", {}).get("rx_metadata", [])
    signal_data = {}

    if rx_metadata and isinstance(rx_metadata, list):
        first_metadata = rx_metadata[0]  # Solo usamos el primer gateway por ahora
        signal_data = {
            "rssi": first_metadata.get("rssi"),
            "snr": first_metadata.get("snr"),
            "channel_rssi": first_metadata.get("channel_rssi"),
            "frequency_offset": first_metadata.get("frequency_offset"),
            "timestamp_radio": first_metadata.get("timestamp"),
            "gateway_id": first_metadata.get("gateway_ids", {}).get("gateway_id"),
            "channel_index": first_metadata.get("channel_index"),
        }

    colombia_time = datetime.now(colombia_tz)
    valid_time = colombia_time.strftime("%Y-%m-%dT%H:%M:%S%z")

    # Validación según el dispositivo
    if device_id.startswith("cube-cell"):
        if not all(k in payload for k in ["Humedad", "HumoMQ7", "UV"]):
            return {"status": "error", "message": "Datos incompletos del CubeCell", "device": device_id}
    elif device_id.startswith("lsn50"):
        if not all(k in payload for k in ["BatV", "TempC1"]):
            return {"status": "error", "message": "Datos incompletos del LSN50", "device": device_id}
    else:
        return {"status": "error", "message": "Dispositivo no reconocido", "device": device_id}

    # Guardar en Firebase
    historico_ref = get_db_ref(f"/historico/usr1/{device_id}")
    if historico_ref:
        historico_ref.child(valid_time).set({
            "sensor_data": payload,
            "signal_quality": signal_data
        })

    ultimo_ref = get_db_ref(f"/ultimo/usr1/{device_id}")
    if ultimo_ref:
        payload_con_fecha = {
            "sensor_data": payload,
            "signal_quality": signal_data,
            "fecha": valid_time
        }
        ultimo_ref.set(payload_con_fecha)

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
