import requests
from django.conf import settings

BASE_URL = settings.GHL_API_BASE
HEADERS = {
    "Authorization": f"Bearer {settings.GHL_ACCESS_TOKEN}",
    "Content-Type": "application/json",
    "Accept": "application/json",
    "Version": "2021-07-28"  # Obligatorio para LeadConnector
}


def create_contact(data):
    url = f"{BASE_URL}/contacts/"
    data["locationId"] = "CRlTCqv7ASS9xOpPQ59O"  # 👈 agrega tu locationId aquí

    print("🔗 URL:", url)
    print("🪶 Headers:", HEADERS)
    print("📦 Data enviada:", data)

    res = requests.post(url, headers=HEADERS, json=data)
    print("📩 Respuesta:", res.text)
    res.raise_for_status()
    return res.json()



def create_appointment(data):
    url = f"{BASE_URL}/calendars/events/appointments/"
    data["locationId"] = "CRlTCqv7ASS9xOpPQ59O"
    print("🔗 URL (cita):", url)
    print("🪶 Headers:", HEADERS)
    print("📦 Data enviada:", data)

    res = requests.post(url, headers=HEADERS, json=data)
    print("📩 Respuesta:", res.text)

    # Manejo de errores
    if not res.ok:
        raise Exception(f"Error al crear cita: {res.status_code} - {res.text}")

    try:
        response_json = res.json()
        return response_json.get("appointment", response_json)
    except Exception as e:
        raise Exception(f"Error parseando respuesta de la cita: {e}")
