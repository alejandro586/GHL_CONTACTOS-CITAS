# 🩺 Integración Contactos + Citas (GoHighLevel API + Django)

## 📌 Objetivo General
Implementar una integración doble entre **Contactos** y **Citas** en GoHighLevel (GHL), de forma que:
- Cada cita esté vinculada a un **contacto real** en GHL.
- El sistema local (Django) mantenga sincronizados los registros de citas mediante un proceso de **reconciliación diaria**.

---

## 🚀 Flujo de Trabajo

### 1. Creación de Contacto y Cita Asociada

#### Objetivo
Vincular cada cita a un contacto existente o recién creado en GHL.

#### Pasos
1. **Crear un contacto (paciente ficticio o real)**
   ```http
   POST /contacts

## 📦 Esquema General

┌───────────────────────────────┐  
│ **1. Requisitos**             │  
├───────────────────────────────┤  
│ - Cuenta GHL activa           │  
│ - API Key (Bearer Token)      │  
│ - Django + SQLite o PostgreSQL│  
│ - requests / dotenv instalados│  
│ - Postman o CURL para pruebas │  
└───────────────────────────────┘  

┌───────────────────────────────┐  
│ **2. Endpoints GHL**          │  
├───────────────────────────────┤  
│ POST /contacts                │ → Crear contacto (paciente)  
│ POST /calendars/events/apmts  │ → Crear cita vinculada  
│ GET  /calendars/events/apmts  │ → Listar citas (últimas 24h)  
└───────────────────────────────┘  

┌───────────────────────────────┐  
│ **3. Django – Appointments**  │  
├───────────────────────────────┤  
│ Modelo:                       │  
│ • appointmentId               │  
│ • contactId                   │  
│ • calendarId                  │  
│ • status                      │  
│ • startTime / endTime         │  
│ • created_at                  │  
│                               │  
│ Endpoint API:                 │  
│ • /api/appointments/          │  
│ • CRUD básico local           │  
│ • Sincronización con GHL      │  
└───────────────────────────────┘  

┌───────────────────────────────┐  
│ **4. Reconciliación Diaria**  │  
├───────────────────────────────┤  
│ • Job programado cada mañana  │  
│ • GET /appointments?from=...  │  
│ • Compara con base local      │  
│ • Detecta faltantes, canceladas│  
│ • Genera reporte JSON diario  │  
└───────────────────────────────┘  

┌───────────────────────────────┐  
│ **5. Flujo Contacto + Cita**  │  
├───────────────────────────────┤  
│ 1️⃣ POST /contacts → crear contacto│  
│ 2️⃣ Obtener contactId              │  
│ 3️⃣ POST /appointments (con ID)    │  
│ 4️⃣ Guardar cita en DB local       │  
│ 5️⃣ Verificar en dashboard GHL     │  
└───────────────────────────────┘  

┌───────────────────────────────┐  
│ **6. Reconciliación - Reporte**│  
├───────────────────────────────┤  
│ • faltantes_local[]            │  
│ • canceladas_no_actualizadas[] │  
│ • desincronizadas[]            │  
│ • fecha: YYYY-MM-DD            │  
└───────────────────────────────┘  
