# ESTRUCTURA DEL PROYECTO TIME_PRO - ANÁLISIS COMPLETO

## 1. ESTRUCTURA GENERAL DEL PROYECTO

### Framework Base
- **Backend**: Flask (Python)
- **Frontend**: Plantillas Jinja2 + HTML/CSS/JavaScript
- **ORM**: SQLAlchemy
- **BD**: PostgreSQL (Supabase en producción, SQLite local)
- **Build Tool**: Vite (para assets estáticos)
- **Estilos**: Tailwind CSS
- **Herramientas**: Flask-SocketIO, Flask-Mail, Flask-Migrate, APScheduler

### Estructura de Carpetas
```
Time_Pro/
├── models/                  # Modelos SQLAlchemy
│   ├── database.py         # Instancia DB y clase TenantAwareQuery
│   ├── models.py           # Definición de modelos (User, TimeRecord, etc.)
│   └── email_log.py        # Modelo para logs de email
│
├── routes/                 # Blueprints de Flask (rutas)
│   ├── auth.py            # Login, logout, registro
│   ├── time.py            # Check-in/out, pauses, leave requests
│   ├── admin.py           # Gestión de usuarios, registros, configuración
│   └── export.py          # Exportación Excel/PDF
│
├── src/
│   ├── templates/         # Plantillas HTML Jinja2
│   │   ├── base.html                    # Template base
│   │   ├── manage_users.html            # Gestión de usuarios
│   │   ├── user_form.html               # Formulario add/edit usuario
│   │   ├── manage_records.html          # Gestión de registros
│   │   ├── admin_dashboard.html         # Dashboard admin
│   │   ├── employee_dashboard.html      # Dashboard empleado
│   │   ├── admin_calendar.html          # Calendario
│   │   ├── export_excel.html            # Exportación Excel
│   │   ├── admin_leave_requests.html    # Solicitudes de ausencia
│   │   └── admin_work_pauses.html       # Pausas laborales
│   │
│   ├── pages/             # Componentes React (minimal)
│   │   ├── Home.jsx
│   │   └── Login.jsx
│   │
│   └── static/            # Assets compilados
│
├── static/                # Assets públicos
│   └── css/              # Estilos compilados
│
├── config/               # Configuración
│   └── supabase_config.py # Credenciales Supabase
│
├── utils/
│   ├── multitenant.py    # Utilidades multi-cliente
│   └── file_utils.py     # Utilidades para archivos
│
├── migrations/           # Migraciones Alembic
│   └── versions/         # Scripts de migración
│
├── tasks/                # Tareas programadas
│   └── scheduler.py      # Auto-cierre de registros
│
├── main.py              # Punto de entrada Flask
├── plan_config.py       # Configuración de planes (lite/pro)
└── requirements.txt     # Dependencias Python
```

---

## 2. DEFINICIÓN ACTUAL DE CATEGORÍAS (category_enum)

### Ubicación: `/mnt/c/Users/Sergio/Desktop/Time_Pro/models/models.py` (líneas 82-88)

```python
categoria = db.Column(
    db.Enum(
        "Coordinador", "Empleado", "Gestor",
        name="category_enum"
    ),
    nullable=True
)
```

### Características Actuales
- **Tipo**: ENUM de PostgreSQL
- **Valores fijos**: "Coordinador", "Empleado", "Gestor"
- **Ubicación**: Tabla `user` (campo `categoria`)
- **Nullable**: Sí (puede ser nulo)
- **Limitación**: Hardcodeado en el modelo, requiere migración para cambios

### Problemas Identificados
- No es dinámico por cliente
- Cambios requieren migración de BD
- El modelo Category existe pero NO se integra con la tabla User
- DEFAULT_CATEGORIES en `/routes/admin.py` línea 20 duplica esta información

---

## 3. ARCHIVOS DE MODELOS Y ESQUEMAS DE BASE DE DATOS

### Archivo Principal: `/mnt/c/Users/Sergio/Desktop/Time_Pro/models/models.py`

**Modelos Clave:**

1. **Client** (líneas 7-36)
   - `id` (PK)
   - `name`, `slug` (Identificadores únicos por cliente)
   - `plan` (Enum: "lite" | "pro")
   - `logo_url`, `primary_color`, `secondary_color` (Branding)
   - Relaciones: `users`, `categories`

2. **Category** (líneas 38-53) - **YA EXISTE pero NO SE USA**
   - `id` (PK)
   - `client_id` (FK a Client) - **IMPORTANTE: ya está listo para multi-tenant**
   - `name` (String 100)
   - `description` (String 255)
   - `created_at` (DateTime)
   - **Constraint**: Única por cliente (client_id, name)

3. **User** (líneas 55-130)
   - `id`, `client_id`, `username`, `password_hash`, `full_name`, `email`
   - `role` (Enum: "admin" | "super_admin" | null)
   - `weekly_hours`, `is_active`, `theme_preference`
   - `centro` (Enum: "Centro 1/2/3")
   - **`categoria` (ENUM hardcodeado)** ← ESTO SERÁ REEMPLAZADO
   - Notificaciones: `email_notifications`, `notification_days`, `notification_time_entry/exit`

4. **TimeRecord** (líneas 132-149)
   - `id`, `client_id`, `user_id`, `date`
   - `check_in`, `check_out` (DateTime)
   - `notes`, `modified_by`, `created_at`, `updated_at`

5. **EmployeeStatus** (líneas 151-185)
   - Estado diario: "Trabajado", "Baja", "Ausente", "Vacaciones"
   - `client_id`, `user_id`, `date`
   - Constraint: Única por cliente/usuario/día

6. **WorkPause** (líneas 188-220)
   - Pausas laborales: "Descanso", "Almuerzo", "Médicos", "Desplazamientos"
   - `client_id`, `user_id`, `time_record_id`
   - Soporta archivos adjuntos

7. **LeaveRequest** (líneas 223-267)
   - Solicitudes de ausencia
   - `client_id`, `user_id`
   - Estados: "Pendiente", "Aprobado", "Rechazado", "Cancelado"

8. **SystemConfig** (líneas 270-314)
   - Configuración por cliente
   - `key-value` store
   - Actualmente almacena: `theme` (Tema visual del sistema)

### Archivo BD: `/mnt/c/Users/Sergio/Desktop/Time_Pro/models/database.py`

**TenantAwareQuery** (líneas 5-120)
- Clase personalizada de SQLAlchemy Query
- Aplica filtrado automático por `client_id`
- TENANT_MODELS: User, TimeRecord, EmployeeStatus, WorkPause, LeaveRequest, SystemConfig
- **IMPORTANTE**: Category NO está en TENANT_MODELS (debería estarlo)
- Método `bypass_tenant_filter()` para casos especiales

---

## 4. MANEJO DE client_id EN EL PROYECTO

### Flujo de client_id

1. **Autenticación** (`routes/auth.py`)
   - Al login, se obtiene el usuario y su `client_id`
   - Se guarda en `session['client_id']`

2. **Filtrado Automático** (`utils/multitenant.py`)
   - `get_current_client_id()` - obtiene de sesión
   - `get_current_client()` - obtiene objeto Client
   - Filtro aplicado automáticamente por `TenantAwareQuery`

3. **Inserción de Datos** (`routes/time.py`, línea 80)
   ```python
   client_id = session.get("client_id", 1)  # Multi-tenant
   new_rec = TimeRecord(
       client_id=client_id,
       user_id=user_id,
       ...
   )
   ```

4. **Queries Automáticas** (`models/database.py`)
   - Todas las queries de modelos TENANT_MODELS incluyen filtro WHERE client_id = X
   - Transparente para el desarrollador

### Tablas con client_id
- `client` (PK)
- `category` (FK)
- `user` (FK)
- `time_record` (FK)
- `employee_status` (FK)
- `work_pause` (FK)
- `leave_request` (FK)
- `system_config` (FK)

---

## 5. ARCHIVOS PRINCIPALES POR FUNCIONALIDAD

### A. GESTIONAR REGISTROS (Time Tracking)

**Rutas Backend** (`/mnt/c/Users/Sergio/Desktop/Time_Pro/routes/time.py`):
- `POST /check_in` - Fichar entrada
- `POST /check_out` - Fichar salida
- `GET /dashboard` - Dashboard empleado
- `GET /calendar` - Vista calendario
- `GET /history` - Historial
- `POST /time/pause/start` - Iniciar pausa
- `POST /time/pause/end/<pause_id>` - Finalizar pausa
- `POST /time/requests/new` - Crear solicitud de ausencia
- `GET /time/requests/my` - Mis solicitudes

**Plantillas**:
- `/src/templates/employee_dashboard.html` - Dashboard principal
- `/src/templates/check_in_out_form.html` - Formulario fichar
- `/src/templates/history.html` - Historial
- `/src/templates/open_records.html` - Registros abiertos

**Modelos**:
- `TimeRecord` - Registros de entrada/salida
- `WorkPause` - Pausas durante jornada
- `EmployeeStatus` - Estado diario

---

### B. DASHBOARD

**Rutas Backend** (`/mnt/c/Users/Sergio/Desktop/Time_Pro/routes/admin.py`):
- `GET /admin/dashboard` (línea 154) - Dashboard admin

**Plantillas**:
- `/src/templates/admin_dashboard.html` - Vista admin con estadísticas
- `/src/templates/employee_dashboard.html` - Vista empleado

**Datos Mostrados**:
- Resumen de horas trabajadas
- Empleados activos/inactivos
- Registros abiertos
- Solicitudes pendientes

---

### C. GESTIONAR USUARIOS

**Rutas Backend** (`/mnt/c/Users/Sergio/Desktop/Time_Pro/routes/admin.py`):
- `GET /admin/manage-users` (línea 259) - Listar usuarios
- `GET /admin/add_user` + `POST /admin/add_user` (línea 299) - Crear usuario
- `GET /admin/edit_user/<user_id>` + `POST` (línea 428) - Editar usuario
- `POST /admin/delete_user/<user_id>` (línea 509) - Eliminar usuario
- `POST /admin/toggle_user_active/<user_id>` (línea 525) - Activar/desactivar

**Plantillas**:
- `/src/templates/manage_users.html` - Listado usuarios
- `/src/templates/user_form.html` - Formulario add/edit

**Campos de Usuario Incluidos** (`user_form.html`):
- username, full_name, email, password
- weekly_hours
- role (admin/super_admin/null)
- centro (Centro 1/2/3)
- **categoria** (Coordinador/Empleado/Gestor) ← **AQUÍ USA EL ENUM ACTUAL**
- hire_date, termination_date
- theme_preference
- email_notifications, notification_days, notification_time

**Filtros en Listado** (`manage_users.html`, línea 32-37):
```html
<select name="categoria">
  {% for cat in categorias %}
    <option value="{{ cat }}">{{ cat }}</option>
  {% endfor %}
</select>
```

---

### D. GESTIÓN DE SOLICITUDES (Leave Requests)

**Rutas Backend** (`/mnt/c/Users/Sergio/Desktop/Time_Pro/routes/admin.py`):
- `GET /admin/leave_requests` (línea 999) - Listar solicitudes
- `POST /admin/leave_requests/approve/<request_id>` - Aprobar
- `POST /admin/leave_requests/reject/<request_id>` - Rechazar

**Plantillas**:
- `/src/templates/admin_leave_requests.html` - Gestión solicitudes

**Tipos**: Vacaciones, Baja médica, Ausencia justificada, etc.

---

### E. CALENDARIO

**Rutas Backend** (`/mnt/c/Users/Sergio/Desktop/Time_Pro/routes/admin.py`):
- `GET /admin/calendar` (línea 736) - Vista calendario
- `GET /admin/api/events` (línea 742) - Eventos para calendario (JSON)
- `GET /admin/api/employees` (línea 813) - Lista empleados (JSON)
- `GET /admin/api/centro_info` (línea 832) - Info de centros (JSON)

**Plantillas**:
- `/src/templates/admin_calendar.html` - Vista calendario

**Librerías**:
- FullCalendar (node_modules/@fullcalendar/)

---

### F. EXPORTAR EXCEL

**Rutas Backend** (`/mnt/c/Users/Sergio/Desktop/Time_Pro/routes/export.py`):
- `GET/POST /export/excel` (línea 333) - Exportación Excel diaria/semanal/mensual
- `GET/POST /export/excel_monthly` (línea 664) - Exportación mensual específica
- `GET /export/excel_daily` (línea 1056) - Formulario exportación diaria
- `GET /export/pdf_daily` (línea 1121) - Exportación PDF diaria

**Plantillas**:
- `/src/templates/export_excel.html` - Interfaz exportación

**Formatos Soportados**:
- Excel (.xlsx) con múltiples pestañas
- PDF con tablas
- Filtros: por usuario, centro, categoría, rango de fechas

**Columnas Exportadas** (línea 93, 124, etc.):
- Usuario, Nombre, **Categoría**, Centro, Fecha, Entrada, Salida, Horas, Notas

---

## 6. INTEGRACIÓN DE CATEGORÍAS EN PUNTOS CLAVE

### Dónde se Usa category_enum Actualmente

1. **Modelo User** (`models/models.py:82-88`)
   - Campo ENUM directo

2. **Admin Routes** (`routes/admin.py`):
   - Línea 20: `DEFAULT_CATEGORIES = ["Coordinador", "Empleado", "Gestor"]`
   - Línea 22-35: Función `get_categorias_disponibles()` - **LEE DE BD Category, pero fallback a DEFAULT_CATEGORIES**
   - Línea 243, 293, 302, 432: Se pasa `categorias` a templates

3. **Admin Templates**:
   - `manage_users.html` - Filtro por categoría (línea 32-37)
   - `user_form.html` - Selector categoría al crear/editar
   - Línea 65: Columna "Categoría" en tabla

4. **Export Routes** (`routes/export.py`):
   - Línea 93, 124, 157, 173, 189: Se incluye `user.categoria` en exports
   - Línea 436-437, 464-465, 733-734, 760-761: Filtros por categoría en queries

5. **Admin Calendar** (`routes/admin.py:803`):
   - Se incluye categoría en eventos del calendario

---

## 7. ARCHIVOS DE CONFIGURACIÓN

### `/mnt/c/Users/Sergio/Desktop/Time_Pro/plan_config.py`
- Configuración de planes (lite/pro)
- CENTER_LABEL, CENTER_LABEL_PLURAL
- MAX_EMPLOYEES
- Features por plan

### `/mnt/c/Users/Sergio/Desktop/Time_Pro/utils/multitenant.py`
- Funciones multi-tenant
- `get_current_client()`, `get_current_client_id()`
- `get_client_config()` - Retorna config por cliente
- `client_has_feature()` - Verifica features

### `/.env`
- DATABASE_URL - Conexión BD
- MAIL_* - Configuración email
- SECRET_KEY - Key Flask
- APP_PLAN - Plan por defecto (lite/pro)

---

## 8. RESUMEN DE CAMBIOS NECESARIOS

Para implementar **Categorías Personalizadas por Cliente**:

1. **Migración BD**: Cambiar campo `categoria` en User de ENUM a FK de Category
2. **Modelo**: Actualizar relación User → Category
3. **Admin Routes**: Integrar CRUD de categorías, usar dinamicamente
4. **Templates**: Actualizar forms/filters para usar categorías dinámicas
5. **Export**: Asegurar exports usen categorías dinámicas
6. **Permisos**: Considerar si admins pueden crear/editar categorías

### Archivos a Modificar:
- `/models/models.py` - Relación User-Category
- `/models/database.py` - Agregar Category a TENANT_MODELS
- `/routes/admin.py` - CRUD categorías, actualizar get_categorias_disponibles
- `/src/templates/manage_users.html`, `user_form.html` - UI dinámico
- `/src/templates/export_excel.html` - Filtros dinámicos
- Migraciones Alembic - Transformar datos ENUM → FK

---

## 9. ARCHIVOS RELEVANTES (RUTAS ABSOLUTAS)

```
/mnt/c/Users/Sergio/Desktop/Time_Pro/models/models.py (Modelos + Category actual)
/mnt/c/Users/Sergio/Desktop/Time_Pro/models/database.py (TenantAwareQuery)
/mnt/c/Users/Sergio/Desktop/Time_Pro/routes/admin.py (Gestión usuarios + CRUD categorías)
/mnt/c/Users/Sergio/Desktop/Time_Pro/routes/time.py (Registros de tiempo)
/mnt/c/Users/Sergio/Desktop/Time_Pro/routes/export.py (Exportaciones)
/mnt/c/Users/Sergio/Desktop/Time_Pro/routes/auth.py (Autenticación)
/mnt/c/Users/Sergio/Desktop/Time_Pro/src/templates/manage_users.html (Listado usuarios)
/mnt/c/Users/Sergio/Desktop/Time_Pro/src/templates/user_form.html (Form usuario)
/mnt/c/Users/Sergio/Desktop/Time_Pro/src/templates/admin_dashboard.html (Dashboard)
/mnt/c/Users/Sergio/Desktop/Time_Pro/src/templates/export_excel.html (Export UI)
/mnt/c/Users/Sergio/Desktop/Time_Pro/utils/multitenant.py (Multitenant utilities)
/mnt/c/Users/Sergio/Desktop/Time_Pro/main.py (Punto entrada Flask)
/mnt/c/Users/Sergio/Desktop/Time_Pro/plan_config.py (Config planes)
```

