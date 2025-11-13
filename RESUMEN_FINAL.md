# RESUMEN EJECUTIVO - ESTRUCTURA TIME_PRO

## Información Solicitada - Respuestas Directas

### 1. ESTRUCTURA GENERAL DEL PROYECTO

**Framework**: Flask (Python) + Jinja2 Templates + Tailwind CSS
**Patrón**: Blueprint-based MVC con multi-tenant

**Estructura Clave:**
```
Time_Pro/
├── models/          → SQLAlchemy ORM (User, TimeRecord, Category, etc.)
├── routes/          → Flask Blueprints (auth, time, admin, export)
├── src/templates/   → Jinja2 HTML templates
├── static/          → CSS/JS compilados
├── utils/           → Helpers (multitenant, file_utils)
├── migrations/      → Alembic DB migrations
├── tasks/           → Background jobs (scheduler)
└── main.py          → Flask app entry point
```

**Stack Técnico:**
- Backend: Flask, SQLAlchemy, Flask-Mail, Flask-SocketIO
- BD: PostgreSQL (Supabase prod) / SQLite (dev)
- Frontend: Jinja2 + HTML5 + Tailwind CSS + JavaScript
- Migración: Alembic
- Deploy: Render/Heroku (Procfile + gunicorn)

---

### 2. DEFINICIÓN ACTUAL DE CATEGORÍAS (category_enum)

**Ubicación**: `/models/models.py` líneas 82-88 (tabla `user`)

**Tipo Actual**: PostgreSQL ENUM
```python
categoria = db.Column(
    db.Enum("Coordinador", "Empleado", "Gestor", name="category_enum"),
    nullable=True
)
```

**Valores Fijos**: "Coordinador", "Empleado", "Gestor"
**Limitación**: Hardcodeado, cambios requieren migración
**Duplicado**: DEFAULT_CATEGORIES en `/routes/admin.py:20`

**Problema Identificado**: No es dinámico por cliente (solicitación principal)

---

### 3. ARCHIVOS DE MODELOS Y BD

**Principal**: `/models/models.py`

**8 Modelos Definidos:**
1. **Client** - Empresas/clientes multi-tenant (id, name, slug, plan, branding)
2. **Category** - Categorías DINÁMICAS POR CLIENTE (id, client_id, name, description)
   - **YA EXISTE pero NO SE USA** - está huérfano, listo para integración
3. **User** - Empleados (id, client_id, username, email, **categoria** ENUM)
4. **TimeRecord** - Fichajes entrada/salida (id, client_id, user_id, check_in/out)
5. **EmployeeStatus** - Estado diario (Trabajado/Baja/Ausente/Vacaciones)
6. **WorkPause** - Pausas laborales (Descanso/Almuerzo/Médicos)
7. **LeaveRequest** - Solicitudes de ausencia (Vacaciones/Baja/Ausencia)
8. **SystemConfig** - Configuración por cliente (key-value store)

**Base de Datos**: `/models/database.py`
- **TenantAwareQuery**: Clase personalizada de SQLAlchemy
- Filtra automáticamente por `client_id` para seguridad multi-tenant
- TENANT_MODELS: User, TimeRecord, EmployeeStatus, WorkPause, LeaveRequest, SystemConfig
- **NOTA**: Category NO está en TENANT_MODELS (error, debería estarlo)

---

### 4. MANEJO DE client_id EN EL PROYECTO

**Arquitectura Multi-Tenant:**

1. **Sesión**: Al login, `session['client_id']` se establece desde usuario.client_id
2. **Queries**: TenantAwareQuery filtra automáticamente: WHERE client_id = X
3. **Inserción**: Todos los insert incluyen `client_id = session.get('client_id')`
4. **Autorización**: Protege datos por cliente transparentemente

**Tablas con client_id:**
- `client` (PK)
- `category` (FK) ← YA LISTO para usar
- `user` (FK)
- `time_record` (FK)
- `employee_status` (FK)
- `work_pause` (FK)
- `leave_request` (FK)
- `system_config` (FK)

**Flujo**: Login → session['client_id'] → Queries filtradas → Datos aislados

---

### 5. ARCHIVOS PRINCIPALES POR FUNCIONALIDAD

#### A. GESTIONAR REGISTROS (Time Tracking)
- **Ruta Backend**: `/routes/time.py`
- **Rutas Principales**:
  - POST `/check_in` - Fichar entrada
  - POST `/check_out` - Fichar salida
  - GET `/calendar` - Calendario
  - GET `/history` - Historial
  - POST `/time/pause/start` - Pausa
  - POST `/time/requests/new` - Solicitud ausencia
- **Templates**: employee_dashboard.html, check_in_out_form.html, history.html
- **Modelos**: TimeRecord, WorkPause, EmployeeStatus

#### B. DASHBOARD
- **Ruta Backend**: `/routes/admin.py:154` GET `/admin/dashboard`
- **Templates**: admin_dashboard.html, employee_dashboard.html
- **Datos**: Resumen horas, empleados activos/inactivos, registros abiertos

#### C. GESTIONAR USUARIOS
- **Ruta Backend**: `/routes/admin.py`
  - GET/POST `/admin/manage-users` (línea 259)
  - GET/POST `/admin/add_user` (línea 299)
  - GET/POST `/admin/edit_user/<user_id>` (línea 428)
  - POST `/admin/delete_user/<user_id>` (línea 509)
  - POST `/admin/toggle_user_active/<user_id>` (línea 525)
- **Templates**: manage_users.html, user_form.html
- **Campo**: `categoria` (selector con DEFAULT_CATEGORIES)
- **Filtros**: Por centro, categoría, búsqueda

#### D. GESTIÓN DE SOLICITUDES (Leave Requests)
- **Ruta Backend**: `/routes/admin.py:999` GET/POST `/admin/leave_requests`
- **Template**: admin_leave_requests.html
- **Tipos**: Vacaciones, Baja médica, Ausencia justificada, Ausencia injustificada, Permiso especial

#### E. CALENDARIO
- **Ruta Backend**: `/routes/admin.py:736` GET/POST `/admin/calendar`
- **API Endpoints**:
  - GET `/admin/api/events` (línea 742) - Eventos JSON
  - GET `/admin/api/employees` (línea 813) - Lista empleados
  - GET `/admin/api/centro_info` (línea 832) - Info centros
- **Template**: admin_calendar.html
- **Librería**: FullCalendar (@fullcalendar en node_modules)

#### F. EXPORTAR EXCEL
- **Ruta Backend**: `/routes/export.py`
  - POST `/export/excel` (línea 333) - Diaria/Semanal/Mensual
  - POST `/export/excel_monthly` (línea 664) - Mensual específica
  - GET `/export/excel_daily` (línea 1056) - Form diaria
  - GET `/export/pdf_daily` (línea 1121) - PDF diaria
- **Template**: export_excel.html
- **Formatos**: Excel (.xlsx) con 3 pestañas, PDF con tablas
- **Columnas**: Usuario, Nombre, **Categoría**, Centro, Fecha, Entrada, Salida, Horas, Notas
- **Filtros**: Usuario, Centro, Categoría, Rango de fechas

---

### RESUMEN VISUAL DE INTEGRACIÓN DE CATEGORÍAS

**Puntos donde se usa category_enum:**

```
1. MODELO (models/models.py:82-88)
   └─ User.categoria [ENUM hardcodeado]

2. BACKEND (routes/admin.py)
   ├─ Línea 20: DEFAULT_CATEGORIES = ["Coordinador", "Empleado", "Gestor"]
   ├─ Línea 22-35: get_categorias_disponibles() - Lee de BD pero fallback a DEFAULT
   ├─ Línea 160, 280: Filtro manage_users() por User.categoria
   ├─ Línea 326: add_user() asigna categoria=request.form.get("categoria")
   ├─ Línea 477: edit_user() actualiza user.categoria
   └─ Línea 803: admin_calendar() incluye user.categoria en eventos

3. FRONTEND (templates)
   ├─ manage_users.html línea 32-37: Selector filtro categoría
   ├─ user_form.html: Selector categoría al crear/editar usuario
   ├─ export_excel.html: Filtro categoría
   ├─ admin_dashboard.html: Posibles filtros
   └─ admin_calendar.html: Mostrar categoría en eventos

4. EXPORTACIÓN (routes/export.py)
   ├─ Línea 93, 124, 157, 173, 189: user.categoria en columnas
   ├─ Línea 436-437, 464-465, 733-734, 760-761: Filtro WHERE user.categoria == X
   └─ Múltiples líneas: Exporta categoria en Excel/PDF

5. API (routes/admin.py)
   └─ Línea 803: Incluye categoría en eventos JSON para calendario
```

---

## ARCHIVOS A CONSULTAR (RUTAS ABSOLUTAS)

```
ESTRUCTURA GENERAL:
/mnt/c/Users/Sergio/Desktop/Time_Pro/main.py              → Entry point
/mnt/c/Users/Sergio/Desktop/Time_Pro/plan_config.py       → Config planes lite/pro

MODELOS:
/mnt/c/Users/Sergio/Desktop/Time_Pro/models/models.py     → 8 modelos (con Category)
/mnt/c/Users/Sergio/Desktop/Time_Pro/models/database.py   → TenantAwareQuery

RUTAS:
/mnt/c/Users/Sergio/Desktop/Time_Pro/routes/auth.py       → Login/logout
/mnt/c/Users/Sergio/Desktop/Time_Pro/routes/time.py       → Check-in/out/pauses
/mnt/c/Users/Sergio/Desktop/Time_Pro/routes/admin.py      → Usuarios, dashboard, calendario
/mnt/c/Users/Sergio/Desktop/Time_Pro/routes/export.py     → Excel/PDF exports

TEMPLATES:
/mnt/c/Users/Sergio/Desktop/Time_Pro/src/templates/base.html
/mnt/c/Users/Sergio/Desktop/Time_Pro/src/templates/manage_users.html
/mnt/c/Users/Sergio/Desktop/Time_Pro/src/templates/user_form.html
/mnt/c/Users/Sergio/Desktop/Time_Pro/src/templates/admin_dashboard.html
/mnt/c/Users/Sergio/Desktop/Time_Pro/src/templates/employee_dashboard.html
/mnt/c/Users/Sergio/Desktop/Time_Pro/src/templates/admin_calendar.html
/mnt/c/Users/Sergio/Desktop/Time_Pro/src/templates/export_excel.html
/mnt/c/Users/Sergio/Desktop/Time_Pro/src/templates/admin_leave_requests.html
/mnt/c/Users/Sergio/Desktop/Time_Pro/src/templates/admin_work_pauses.html

UTILIDADES:
/mnt/c/Users/Sergio/Desktop/Time_Pro/utils/multitenant.py → Multi-tenant functions
/mnt/c/Users/Sergio/Desktop/Time_Pro/utils/file_utils.py  → File upload/validation

CONFIGURACIÓN:
/mnt/c/Users/Sergio/Desktop/Time_Pro/.env                 → Variables de entorno
/mnt/c/Users/Sergio/Desktop/Time_Pro/config/supabase_config.py

MIGRACIONES:
/mnt/c/Users/Sergio/Desktop/Time_Pro/migrations/versions/ → Scripts Alembic
```

---

## DOCUMENTACIÓN GENERADA

1. **PROJECT_STRUCTURE_ANALYSIS.md** (15KB)
   - Análisis profundo de estructura
   - 9 secciones detalladas
   - Diagrama de modelos y relaciones
   - Estado actual de categorías

2. **IMPLEMENTATION_GUIDE.md** (22KB)
   - Guía paso a paso de implementación
   - Código de ejemplo para cada cambio
   - Templates HTML completos
   - Script de migración Alembic
   - Checklist de 20+ items

---

## CONCLUSIÓN

El proyecto Time_Pro está bien estructurado como aplicación multi-tenant con:
- Infraestructura lista para categorías dinámicas (Category model existe)
- Aislamiento de datos por client_id transparente
- Modelo ENUM actual que necesita refactor a FK

**Próximo paso**: Implementar integración de `Category` con `User` siguiendo la guía de implementación proporcionada.

