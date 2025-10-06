from django.urls import path
from .views import (
    AppointmentCreateView,
    appointment_webhook,
)
from . import views

urlpatterns = [
    path('create/', AppointmentCreateView.as_view(), name="create_appointment"),
    path("webhooks/appointments/", appointment_webhook, name="appointment_webhook"),
    path("webhooks/ghl/appointments/", views.appointment_webhook, name="ghl_appointment_webhook"),  # 👈 esta es la que GHL intenta llamar
    path("create/", views.appointment_create, name="appointment_create"),
]
