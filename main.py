from fastapi import FastAPI, Request
from dotenv import load_dotenv
from datetime import datetime
import pytz
import os

from firebase2 import init_firebase, get_db_ref

# Cargar variables de entorno
load_dotenv()

# Inicializar Firebase
init_firebase()

# Instancia de FastAPI
app = FastAPI()

# Zona horaria Colombia
colombia_tz = pytz.timezone("America/Bogota")

@app.get("/")
async def root():
    return {"message": "Hola desde la API en Replit!"}

@app.post("/uplink")
async def uplink_handler(request: Request):
    body = await request.json()
    print("📡 Datos recibidos:", body)

    device_id = body.get("end_device_ids", {}).get("device_id", "desconocido")
    payload = body.get("uplink_message", {}).get("decoded_payload", {})

    rx_metadata = body.get("uplink_message", {}).get("rx_metadata", [])
    signal_data = {}

    if rx_metadata and isinstance(rx_metadata, list):
        first_metadata = rx_metadata[0]
        signal_data = {
            "rssi": first_metadata.get("rssi"),
            "snr": first_metadata.get("snr"),
            "channel_rssi": first_metadata.get("channel_rssi"),
            "frequency_offset": first_metadata.get("frequency_offset"),
            "timestamp_radio": first_metadata.get("timestamp"),
            "gateway_id": first_metadata.get("gateway_ids", {}).get("gateway_id"),
            "channel_index": first_metadata.get("channel_index"),
        }

    valid_time = datetime.now(colombia_tz).strftime("%Y-%m-%dT%H:%M:%S%z")

    if device_id.startswith("cube-cell"):
        if not all(k in payload for k in ["Humedad", "HumoMQ7", "UV"]):
            return {"status": "error", "message": "Datos incompletos del CubeCell", "device": device_id}
    elif device_id.startswith("lsn50"):
        if not all(k in payload for k in ["BatV", "TempC1"]):
            return {"status": "error", "message": "Datos incompletos del LSN50", "device": device_id}
    else:
        return {"status": "error", "message": "Dispositivo no reconocido", "device": device_id}

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
