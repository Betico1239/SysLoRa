import random
import datetime
import firebase_admin
from firebase_admin import db, credentials

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://syslora2025-default-rtdb.firebaseio.com/'
})

def generar_timestamp():
    now = datetime.datetime.now(datetime.UTC)
    # Formato seguro para Firebase (sin caracteres ilegales)
    return now.strftime("%Y%m%dT%H%M%S")

def simular_lsn50():
    data = {
        "TempC1": round(random.uniform(20.0, 30.0), 2),
        "BatV": round(random.uniform(3.4, 3.8), 3),
        "fecha": generar_timestamp()
    }
    ts = generar_timestamp()
    ref_historico = db.reference(f"/historico/usr1/lsn50/{ts}")
    ref_historico.set(data)

    ref_ultimo = db.reference("/ultimo/usr1/lsn50")
    ref_ultimo.set(data)

def simular_htcc():
    data = {
        "Humedad": round(random.uniform(30, 90), 1),
        "HumoMQ7": round(random.uniform(0, 100), 1),
        "UV": round(random.uniform(100, 1000), 1),
        "fecha": generar_timestamp()
    }
    ts = generar_timestamp()
    ref_historico = db.reference(f"/historico/usr1/htcc-ab01/{ts}")
    ref_historico.set(data)

    ref_ultimo = db.reference("/ultimo/usr1/htcc-ab01")
    ref_ultimo.set(data)

if __name__ == "__main__":
    simular_lsn50()
    simular_htcc()
    print("✅ Datos simulados insertados correctamente.")
