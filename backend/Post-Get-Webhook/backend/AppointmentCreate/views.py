import os
import json
from django.http import JsonResponse
import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
from django.views.decorators.csrf import csrf_exempt
from dotenv import load_dotenv
from .models import Appointment
from .serializers import AppointmentSerializer
from django.utils.dateparse import parse_datetime
from django.utils import timezone
from django.conf import settings
from rest_framework.generics import ListAPIView
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from services import ghl_api
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status


@api_view(["POST"])
def appointment_create(request):
    """
    Crear una cita en GHL y guardarla en MySQL (ya lo tenías).
    """
    data = request.data

    nombre = data.get("nombre")
    email = data.get("email")
    fecha = data.get("fecha")

    if not nombre or not email or not fecha:
        return Response({"error": "Faltan datos requeridos"}, status=status.HTTP_400_BAD_REQUEST)

    # Aquí iría tu lógica real de creación en GHL y MySQL
    cita = {
        "id": 123,  # simulado
        "nombre": nombre,
        "email": email,
        "fecha": fecha,
    }

    return Response(cita, status=status.HTTP_201_CREATED)




@api_view(["POST"])
def crear_contacto_y_cita(request):
    data = request.data  # Los datos del JSON que enviaste

    # --- Validación de datos esenciales ---
    required_fields = ["email", "phone", "calendarId", "startTime", "endTime"]
    if not all(field in data for field in required_fields):
        return Response(
            {"error": "Faltan campos esenciales en la solicitud.", "required": required_fields}, 
            status=status.HTTP_400_BAD_REQUEST
        )

    # ------------------------------------
    # --- 1) Crear Contacto ---
    # ------------------------------------
    try:
        contact_data = {
            "firstName": data.get("firstName", "Paciente"),
            "lastName": data.get("lastName", "Ficticio"),
            "email": data["email"],
            "phone": data["phone"]
        }
        
        # Llama a la función que crea el contacto en GHL
        contacto = ghl_api.create_contact(contact_data)
        
        contact_id = contacto.get("id") or contacto.get("contact", {}).get("id")

        if not contact_id:
            return Response(
                {"error": "No se pudo obtener el ID del contacto. Respuesta inesperada de la API externa.", "respuesta": contacto},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    except Exception as e:
        # Captura errores de conexión o fallos en la API de contacto
        return Response(
            {"error": "Fallo al crear el contacto.", "details": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    # ------------------------------------
    # --- 2) Crear Cita (Usando los datos POST) ---
    # ------------------------------------
    appointment_data = {
        # Usamos los datos del JSON de entrada:
        "calendarId": data["calendarId"], 
        "contactId": contact_id,
        "startTime": data["startTime"], 
        "endTime": data["endTime"],
        
        "locationId": data.get("locationId", "CRlTCqv7ASS9xOpPQ59O"), # Puede tener un valor por defecto si no se envía
        "title": data.get("title", f"Cita de {contact_data['firstName']}"),
        "notes": data.get("notes", "")
    }

    try:
        # Llama a la función que crea la cita en GHL
        cita = ghl_api.create_appointment(appointment_data)
        
        # Si ambas operaciones fueron exitosas:
        return Response({
            "status": "ok",
            "message": "Contacto creado y cita agendada exitosamente.",
            "contact": contacto,
            "appointment": cita
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        error_message = str(e)
        
        # 🔑 CAPTURA DEL ERROR ESPECÍFICO DEL LOG (HTTP 400 - Slot Ocupado)
        if "The slot you have selected is no longer available" in error_message:
            # Responde con 400 ya que el cliente solicitó una hora no disponible
            return Response(
                {"error": "El horario seleccionado ya no está disponible. Por favor, solicite otro.", "details": error_message},
                status=status.HTTP_400_BAD_REQUEST 
            )
        
        # Manejo de cualquier otro error no especificado durante la creación de la cita (e.g., Auth, Server Error)
        return Response(
            {"error": "Fallo interno al intentar programar la cita. Consulte los detalles.", "details": error_message},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )





# Cargar .env
load_dotenv()

# Constantes GHL
GHL_BASE_URL = "https://services.leadconnectorhq.com"
GHL_API_VERSION = os.getenv("GHL_API_VERSION", "2021-04-15")
ACCESS_TOKEN = os.getenv("GHL_ACCESS_TOKEN")
GHL_LOCATION_ID = os.getenv("GHL_LOCATION_ID")  # fallback si viene vacío en el webhook

if not ACCESS_TOKEN:
    raise Exception("Access Token de GHL no configurado en .env (GHL_ACCESS_TOKEN)")

def _to_datetime(iso_str):
    """Convierte ISO8601 string a datetime aware o devuelve None."""
    if not iso_str:
        return None
    dt = parse_datetime(iso_str)
    if dt is None:
        return None
    if settings.USE_TZ and timezone.is_naive(dt):
        tz = timezone.get_current_timezone()
        dt = timezone.make_aware(dt, tz)
    return dt

class AppointmentCreateView(APIView):
    """Crear una cita en GHL y guardarla en MySQL (ya lo tenías)."""
    def post(self, request, *args, **kwargs):
        data = request.data or {}
        required_fields = ["calendarId", "contactId", "startTime", "endTime"]
        for field in required_fields:
            if field not in data:
                return Response({"error": f"Falta el campo: {field}"}, status=status.HTTP_400_BAD_REQUEST)

        location_id = data.get("locationId") or GHL_LOCATION_ID
        if not location_id:
            return Response({"error": "No se encontró locationId (poner GHL_LOCATION_ID en .env o enviarlo en el payload)"},
                            status=status.HTTP_400_BAD_REQUEST)

        headers = {
            "Authorization": f"Bearer {ACCESS_TOKEN}",
            "Version": GHL_API_VERSION,
            "Content-Type": "application/json",
            "LocationId": location_id
        }

        api_payload = {
            "calendarId": data["calendarId"],
            "locationId": location_id,
            "contactId": data["contactId"],
            "startTime": data["startTime"],
            "endTime": data["endTime"],
            "title": data.get("title", "Cita creada desde API"),
            "appointmentStatus": data.get("appointmentStatus", "confirmed"),
            "assignedUserId": data.get("assignedUserId"),
            "ignoreFreeSlotValidation": True,
            "toNotify": True
        }

        try:
            resp = requests.post(f"{GHL_BASE_URL}/calendars/events/appointments", json=api_payload, headers=headers, timeout=15)
            resp.raise_for_status()
            ghl_data = resp.json()

            start_dt = _to_datetime(ghl_data.get("startTime") or api_payload["startTime"])
            end_dt = _to_datetime(ghl_data.get("endTime") or api_payload["endTime"])

            appointment, created = Appointment.objects.update_or_create(
                ghl_id=ghl_data.get("id"),
                defaults={
                    "location_id": ghl_data.get("locationId") or location_id,
                    "calendar_id": ghl_data.get("calendarId") or api_payload["calendarId"],
                    "contact_id": ghl_data.get("contactId") or api_payload["contactId"],
                    "title": ghl_data.get("title") or api_payload.get("title", "Cita"),
                    "appointment_status": ghl_data.get("appointmentStatus") or api_payload.get("appointmentStatus", "confirmed"),
                    "assigned_user_id": ghl_data.get("assignedUserId") or api_payload.get("assignedUserId"),
                    "notes": ghl_data.get("notes") or None,
                    "start_time": start_dt,
                    "end_time": end_dt,
                    "source": ghl_data.get("source")
                }
            )

            serializer = AppointmentSerializer(appointment)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except requests.exceptions.HTTPError as http_err:
            resp = http_err.response
            details = resp.text if resp is not None else str(http_err)
            code = resp.status_code if resp is not None else 500
            return Response({"error": "Error HTTP al crear cita en GHL", "details": details}, status=code)
        except requests.exceptions.RequestException as e:
            return Response({"error": "Error conexión GHL", "details": str(e)}, status=status.HTTP_502_BAD_GATEWAY)
        except Exception as e:
            return Response({"error": "Error interno", "details": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


import uuid

@csrf_exempt
def appointment_webhook(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)

            # Extraer datos principales del webhook
            appointment_data = data.get("appointment", {})
            appointment_id = data.get("ghl_id") or data.get("id") or appointment_data.get("id")
            
            if not appointment_id:
                appointment_id = f"test-{uuid.uuid4()}"  # ID temporal para pruebas

            # Normalizamos campos
            calendar_id = data.get("calendarId") or appointment_data.get("calendarId")
            contact_id = data.get("contactId") or appointment_data.get("contactId")
            location_id = data.get("locationId") or appointment_data.get("locationId")
            title = data.get("title") or appointment_data.get("title") or "Cita"
            appointment_status = (
                data.get("appointmentStatus") or
                appointment_data.get("appointmentStatus") or
                "confirmed"
            )
            assigned_user_id = (
                data.get("assignedUserId") or appointment_data.get("assignedUserId")
            )
            notes = data.get("notes") or appointment_data.get("notes")
            source = data.get("source") or appointment_data.get("source")

            start_time = _to_datetime(data.get("startTime") or appointment_data.get("startTime"))
            end_time = _to_datetime(data.get("endTime") or appointment_data.get("endTime"))

            # Guardar o actualizar en DB
            obj, created = Appointment.objects.update_or_create(
                ghl_id=appointment_id,
                defaults={
                    "calendar_id": calendar_id,
                    "contact_id": contact_id,
                    "location_id": location_id,
                    "title": title,
                    "appointment_status": appointment_status,
                    "assigned_user_id": assigned_user_id,
                    "notes": notes,
                    "start_time": start_time,
                    "end_time": end_time,
                    "source": source,
                }
            )

            return JsonResponse(
                {"ok": True, "ghl_id": appointment_id, "created": created}, status=200)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"error": "Método no permitido"}, status=405)

