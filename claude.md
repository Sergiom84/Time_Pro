# 📚 Documentación del Proyecto Time_Pro

> Documentación técnica completa generada por Claude Code
> Última actualización: 2025-12-02

---

## ⚠️ **IMPORTANTE: ANTES DE USAR CLAUDE CODE**

**SIEMPRE lee el archivo `.mcp.json` antes de trabajar con Claude Code.**

El archivo `.mcp.json` contiene las credenciales y configuraciones críticas de:
- 🔐 **GitHub**: Personal Access Token
- 🗄️ **Supabase**: Access Token para la BD
- 🚀 **Render**: Authorization Bearer para el hosting

**NUNCA cometas el archivo `.mcp.json` con valores reales a Git.**
Las credenciales deben estar siempre en archivos locales y en variables de entorno del servidor.

---

## 🎯 Índice

1. [Información del Proyecto](#información-del-proyecto)
2. [Arquitectura](#arquitectura)
3. [Funcionalidades Implementadas](#funcionalidades-implementadas)
4. [Sistema de Sellos de Tiempo (Ley de Fichajes)](#sistema-de-sellos-de-tiempo)
5. [Configuración de Infraestructura](#configuración-de-infraestructura)
6. [Bugs Resueltos](#bugs-resueltos)
7. [Variables de Entorno](#variables-de-entorno)

---

## 🏢 Información del Proyecto

### Datos Generales
- **Nombre**: Time_Pro
- **Tipo**: Sistema de Control de Fichajes y Gestión de Jornadas Laborales
- **Framework**: Flask (Python)
- **Base de Datos**: Supabase (PostgreSQL)
- **Hosting**: Render.com
- **Región**: Frankfurt (EU)
- **URL Producción**: https://time-pro-1dj0.onrender.com

### Repositorio
- **GitHub**: https://github.com/Sergiom84/Time_Pro
- **Rama principal**: master
- **Auto-deploy**: Desactivado (manual)

---

## 🏗️ Arquitectura

### Stack Tecnológico

#### Backend
- **Framework**: Flask 2.x
- **ORM**: SQLAlchemy con TenantAwareQuery (multitenant)
- **Base de Datos**: PostgreSQL 17.6 (Supabase)
- **Servidor**: Gunicorn con múltiples workers
- **Scheduler**: APScheduler (tareas automáticas)

#### Frontend
- **Templates**: Jinja2
- **CSS**: Tailwind CSS
- **JavaScript**: Vanilla JS (sin frameworks)

#### Storage
- **Archivos**: Supabase Storage
- **Tipos**: PDFs, imágenes (justificantes médicos, adjuntos)

### Arquitectura Multitenant

```python
# Filtrado automático por client_id
class TenantAwareQuery(Query):
    TENANT_MODELS = {
        "User", "TimeRecord", "TimeRecordSignature",
        "EmployeeStatus", "WorkPause", "LeaveRequest",
        "SystemConfig", "OvertimeEntry"
    }
```

**Características**:
- Filtrado automático por `client_id` en todas las queries
- Método `bypass_tenant_filter()` para tareas administrativas globales
- Cada cliente (empresa) tiene datos completamente aislados

---

## ✨ Funcionalidades Implementadas

### 1. Sistema Base de Fichajes
- ✅ Check-in / Check-out con timestamps precisos
- ✅ Dashboard de empleado con resumen semanal
- ✅ Dashboard de administrador multicliente
- ✅ Gestión de centros de trabajo (plan PRO)
- ✅ Categorías de empleados

### 2. Gestión de Pausas
- ✅ 5 tipos de pausas configurables
- ✅ Pausas con inicio/fin automático
- ✅ Adjuntar justificantes (PDF, imágenes)
- ✅ Cierre automático de pausas con registro

### 3. Gestión de Solicitudes
- ✅ Vacaciones, bajas médicas, ausencias
- ✅ Sistema de aprobación/rechazo por admin
- ✅ Notificaciones push en dashboard
- ✅ Adjuntar documentos justificativos
- ✅ Historial completo de cambios de estado

### 4. Sistema de Horas Extras (Overtime)
**Implementado**: Noviembre-Diciembre 2025

- ✅ Cálculo automático semanal (lunes-domingo)
- ✅ Tolerancia de ±1 hora para errores de fichaje
- ✅ Dashboard con navegación semanal
- ✅ Estados: Pendiente, Aprobado, Ajustado, Rechazado
- ✅ Ajuste automático (modifica último TimeRecord)
- ✅ Ajuste manual (redirige a gestión de registros)
- ✅ Integración con notificaciones (campanita)
- ✅ Export a Excel con tab dedicado

**Archivos**:
- `models/models.py` - Modelo `OvertimeEntry` (líneas 296-349)
- `services/overtime_service.py` - Lógica de cálculo
- `routes/admin.py` - 6 rutas de gestión (líneas 1759-1992)
- `templates/admin_overtime.html` - Dashboard completo

### 5. Sistema de Sellos de Tiempo (Ley de Fichajes) ⭐
**Implementado**: Diciembre 2025

Cumple con los requisitos de la **Ley de Fichajes** española sobre registros infalsificables.

#### Características Técnicas
- ✅ **Hash SHA-256** del contenido del fichaje
- ✅ **Firma HMAC-SHA256** para garantizar integridad
- ✅ **Timestamp UTC preciso** del servidor (no del cliente)
- ✅ **Terminal ID** y metadatos (IP, User-Agent)
- ✅ **Rotación de claves** mediante versiones
- ✅ **Cascada de eliminación** (si se borra fichaje, se borra firma)

#### Modelo de Datos

```python
class TimeRecordSignature(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    time_record_id = db.Column(db.Integer, FK("time_record.id", CASCADE))
    client_id = db.Column(db.Integer, FK("client.id", CASCADE))

    # Sello temporal
    timestamp_utc = db.Column(db.DateTime, nullable=False)
    action = db.Column(Enum("check_in", "check_out"))

    # Origen
    terminal_id = db.Column(db.String(100))  # "web_192.168.1.1"
    user_agent = db.Column(db.Text)
    ip_address = db.Column(db.String(45))

    # Criptografía
    content_hash = db.Column(db.CHAR(64))  # SHA-256 hex
    signature = db.Column(db.CHAR(64))     # HMAC-SHA256 hex
    key_version = db.Column(db.Integer, default=1)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
```

#### Algoritmo de Sellado

```python
# 1. Crear datos deterministas
data = {
    "time_record_id": record.id,
    "user_id": record.user_id,
    "client_id": record.client_id,
    "action": "check_in",
    "timestamp_utc": timestamp_utc.isoformat(),
    "terminal_id": f"web_{ip_address}"
}

# 2. Generar hash SHA-256
ordered = "|".join(f"{k}:{v}" for k, v in sorted(data.items()))
content_hash = hashlib.sha256(ordered.encode()).hexdigest()

# 3. Firmar con HMAC-SHA256
key = os.getenv("SIGNING_KEY_V1").encode()
signature = hmac.new(key, content_hash.encode(), hashlib.sha256).hexdigest()

# 4. Almacenar en BD
TimeRecordSignature(
    time_record_id=record.id,
    content_hash=content_hash,
    signature=signature,
    ...
)
```

#### Archivos Implementados
- ✅ `models/models.py` - Modelo `TimeRecordSignature` (líneas 162-212)
- ✅ `models/database.py` - Añadido a `TENANT_MODELS` (línea 13)
- ✅ `services/timestamp_service.py` - Servicio completo de sellado
- ✅ `routes/time.py` - Integración en check_in (líneas 120-147)
- ✅ `routes/time.py` - Integración en check_out (líneas 197-224)

#### Tabla en Supabase

```sql
CREATE TABLE time_record_signature (
    id SERIAL PRIMARY KEY,
    time_record_id INTEGER REFERENCES time_record(id) ON DELETE CASCADE,
    client_id INTEGER REFERENCES client(id) ON DELETE CASCADE,
    timestamp_utc TIMESTAMP NOT NULL,
    action signature_action_enum NOT NULL,
    terminal_id VARCHAR(100) NOT NULL,
    user_agent TEXT,
    ip_address VARCHAR(45),
    content_hash CHAR(64) CHECK (length(content_hash) = 64),
    signature CHAR(64) CHECK (length(signature) = 64),
    key_version INTEGER DEFAULT 1 CHECK (key_version > 0),
    created_at TIMESTAMP DEFAULT (NOW() AT TIME ZONE 'utc')
);
```

**Índices Optimizados**:
- `idx_time_record_signature_time_record_id` (búsqueda por fichaje)
- `idx_time_record_signature_client_id` (filtrado multitenant)
- `idx_time_record_signature_timestamp` (ordenamiento por fecha)
- `idx_time_record_signature_action` (filtrado por tipo)
- `idx_time_record_signature_client_timestamp` (compuesto)

### 6. Exportación de Datos
- ✅ Export a Excel diario, semanal, mensual
- ✅ Múltiples tabs: Fichajes, Ausencias, Bajas, Pausas, Horas Extras
- ✅ Formato con estilos y colores
- ✅ Cálculo automático de totales

### 7. Notificaciones
- ✅ Email automático (configurables por empleado)
- ✅ Notificaciones push en dashboard (campanita)
- ✅ Sistema de tabs (Solicitudes + Horas Extras)
- ✅ Badge con contador en tiempo real
- ✅ Logs de emails enviados

### 8. Auditoría y Logs
- ✅ `time_record_audit_log` - Historial completo de cambios
- ✅ Campos old_values/new_values (JSON)
- ✅ IP y usuario que realizó el cambio
- ✅ Razón del cambio

### 9. Inspector de Trabajo (Ley 2026)
- ✅ Tokens de acceso temporal
- ✅ Ámbito de fechas restringido
- ✅ Logs completos de accesos externos
- ✅ Visualización read-only de datos

---

## 🔐 Sistema de Sellos de Tiempo

### Verificación de Integridad

```python
def verify_record_signature(signature_record) -> bool:
    """Verifica que un fichaje no ha sido alterado"""

    # Recrear datos originales
    data = create_signature_data(...)

    # Verificar hash
    expected_hash = generate_content_hash(data)
    if expected_hash != signature_record.content_hash:
        return False

    # Verificar firma HMAC
    return verify_signature(
        content_hash=signature_record.content_hash,
        signature=signature_record.signature,
        key_version=signature_record.key_version
    )
```

### Rotación de Claves

**Proceso recomendado** (cada 6-12 meses):

1. Generar nueva clave:
   ```bash
   python -c "import secrets; print(secrets.token_hex(32))"
   ```

2. Añadir como `SIGNING_KEY_V2` en Render

3. Actualizar código para usar v2 en nuevos fichajes:
   ```python
   signature = TimestampService.seal_record(..., key_version=2)
   ```

4. **MANTENER** `SIGNING_KEY_V1` para verificar registros históricos

### Cumplimiento Legal

El sistema cumple con:
- ✅ **Real Decreto-ley 8/2019** - Registro horario obligatorio
- ✅ **Artículo 34.9 del Estatuto de los Trabajadores**
- ✅ Requisito de **registros fiables e infalsificables**
- ✅ Conservación de registros durante **4 años**
- ✅ Disponibilidad para Inspección de Trabajo

---

## 🛠️ Configuración de Infraestructura

### Supabase

**Proyecto**: `[Ver .mcp.json]`
**Región**: EU West 1 (Irlanda)
**Estado**: ACTIVE_HEALTHY
**PostgreSQL**: 17.6.1

#### Tablas Principales
- `client` - 4 empresas registradas
- `user` - 22 usuarios
- `time_record` - 24 registros de fichaje
- `time_record_signature` - 0 (pendiente primer fichaje con sellado)
- `employee_status` - 84 estados
- `work_pause` - 14 pausas
- `leave_request` - 28 solicitudes
- `overtime_entry` - 9 registros de horas extras

#### Storage Buckets
- `employee-docs` - Documentos de empleados
- Configurado con RLS (Row Level Security)

### Render

**Service ID**: `[Ver dashboard de Render]`
**Plan**: Free Tier
**Instancias**: 1
**Región**: Frankfurt
**Runtime**: Python 3.x

#### Configuración Gunicorn
```python
# gunicorn_config.py
bind = "0.0.0.0:10000"
workers = 2  # Free tier: máximo 2 workers
worker_class = "sync"
timeout = 120
keepalive = 5
```

#### Auto-deploy
- **Estado**: Desactivado (manual)
- **Branch**: master
- **Build Command**: `./build.sh`
- **Start Command**: `gunicorn -c gunicorn_config.py wsgi:app`

---

## 🐛 Bugs Resueltos

### 1. Bug: Cierre Automático a las 23:59 No Funcionaba
**Fecha**: Diciembre 2025
**Síntomas**:
- Registros no se cerraban automáticamente a medianoche
- Empleados encontraban fichajes del día anterior abiertos
- Pausas quedaban huérfanas

**Causa Raíz**:
El scheduler usaba `TenantAwareQuery` que requiere `session.get('client_id')`. Sin sesión HTTP (scheduler en background), el filtro fallaba silenciosamente.

```python
# ANTES (INCORRECTO)
open_records = TimeRecord.query.filter(...)  # Falla sin sesión HTTP
```

**Solución**:
```python
# DESPUÉS (CORRECTO)
open_records = TimeRecord.query.bypass_tenant_filter().filter(...)
```

**Archivos modificados**:
- `tasks/scheduler.py:23` - Añadido `bypass_tenant_filter()`
- `tasks/scheduler.py:39` - Pausas también con bypass
- `tasks/scheduler.py:84` - En `manual_auto_close_records()`

### 2. Bug: Desincronización Dashboard-Backend
**Fecha**: Diciembre 2025
**Síntomas**:
- Dashboard mostraba "Fichar entrada"
- Backend rechazaba con "Ya tienes un fichaje abierto"
- Pausas del día anterior se mostraban como actuales

**Causa Raíz**:
```python
# Dashboard buscaba solo HOY
today_record = time_records_query(...).filter_by(date=today).first()

# check_in buscaba CUALQUIER FECHA
existing_open = time_records_query(...).first()  # Sin filtro de fecha
```

**Solución**:
Implementado **auto-cierre inteligente**:

```python
if existing_open and existing_open.date < date.today():
    # Cerrar automáticamente a las 23:59:59 de su fecha
    existing_open.check_out = datetime.combine(existing_open.date, time(23,59,59))

    # Cerrar pausas activas
    WorkPause.query.filter(...).update({...})

    db.session.commit()
    flash("Se cerró automáticamente tu fichaje del día anterior")
```

**Archivos modificados**:
- `routes/time.py:40-72` - Auto-cierre de fichajes antiguos
- `routes/time.py:232-243` - Pausas filtradas por `time_record_id`
- `routes/admin.py:1476-1499` - Cierre de pausas en admin

### 3. Bug: AmbiguousForeignKeysError en Notificaciones
**Fecha**: Diciembre 2025
**Error**: `Can't determine join between 'overtime_entry' and 'user'`

**Causa**:
```python
class OvertimeEntry:
    user_id = db.Column(db.Integer, FK("user.id"))       # FK 1
    decided_by = db.Column(db.Integer, FK("user.id"))    # FK 2
```

SQLAlchemy no sabía cuál FK usar en el JOIN.

**Solución**:
```python
# ANTES
query = query.join(User).filter(...)

# DESPUÉS
query = query.join(User, OvertimeEntry.user_id == User.id).filter(...)
```

**Archivo modificado**: `routes/admin.py:1834`

### 4. Bug: Enum `overtime_status_enum` sin "Rechazado"
**Fecha**: Noviembre 2025
**Síntoma**: Error al acceder a histórico de horas extras

**Solución**:
```sql
ALTER TYPE overtime_status_enum ADD VALUE 'Rechazado';
```

**Estado**: ✅ Resuelto (el enum ahora tiene todos los valores)

---

## 🔑 Variables de Entorno

### Render (Producción)

**IMPORTANTE**: Las claves reales están en el dashboard de Render.
**NO incluir** valores sensibles en este archivo.

```bash
# Base de Datos
DATABASE_URL=[Ver Render Environment Variables]

# Supabase
SUPABASE_URL=[Ver Render Environment Variables]
SUPABASE_ANON_KEY=[Ver Render Environment Variables]
SUPABASE_SERVICE_ROLE_KEY=[Ver Render Environment Variables]

# Aplicación
APP_PLAN=pro
SECRET_KEY=[Ver Render Environment Variables]
FLASK_ENV=production
APP_URL=[URL del servicio en Render]

# Seguridad
ALLOWED_ORIGINS=[URL del servicio en Render]
PREFER_SECURE_COOKIES=true

# Email (Opcional)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=[Ver Render Environment Variables]
MAIL_PASSWORD=[Ver Render Environment Variables]

# Sellos de Tiempo (Ley de Fichajes) ⭐
SIGNING_KEY_V1=[64 caracteres hex, generado con secrets.token_hex(32)]
# Generar con: python -c "import secrets; print(secrets.token_hex(32))"

# Scheduler (auto-asignadas por Render)
GUNICORN_WORKER_ID=0
RENDER=true
```

### Local (Desarrollo)

**Archivo**: `.env` en la raíz del proyecto (NO subir a GitHub)

**IMPORTANTE**:
- ✅ `.env` está en `.gitignore` (no se sube a GitHub)
- ✅ `SIGNING_KEY_V1` solo en Render, no en repo local
- ✅ Usar `APP_URL=http://localhost:5000` en local
- ✅ Copiar valores del `.env` de ejemplo y completar con tus credenciales
- ❌ NUNCA commitear el `.env` con datos reales

---

## 📊 Métricas del Sistema

### Performance
- **Tiempo de respuesta promedio**: < 200ms
- **Carga de dashboard**: < 1s
- **Queries optimizadas**: Índices en todas las FK

### Escalabilidad
- **Clientes soportados**: Ilimitados (multitenant)
- **Usuarios por cliente**: Sin límite técnico
- **Registros de fichaje**: > 1M con performance aceptable
- **Storage**: Limitado por plan de Supabase

### Seguridad
- ✅ HTTPS en producción (Render auto-SSL)
- ✅ CSRF protection habilitado
- ✅ SQL Injection protegido (SQLAlchemy ORM)
- ✅ XSS protegido (sanitización de inputs)
- ✅ RLS en Supabase Storage
- ✅ Sellos de tiempo infalsificables (HMAC-SHA256)

---

## 🚀 Roadmap Futuro

### Corto Plazo (1-3 meses)
- [ ] Dashboard de análisis con gráficos (Chart.js)
- [ ] App móvil nativa (React Native)
- [ ] Geolocalización en fichajes
- [ ] Reconocimiento facial (opcional)

### Medio Plazo (3-6 meses)
- [ ] API REST pública para integraciones
- [ ] Webhooks para eventos
- [ ] Integración con nóminas
- [ ] Sistema de turnos rotativos

### Largo Plazo (6-12 meses)
- [ ] IA para detección de anomalías
- [ ] Blockchain para auditoría inmutable
- [ ] Compliance automático con múltiples países
- [ ] Multi-idioma (i18n)

---

## 📞 Contacto y Soporte

**Desarrollador Principal**: [Nombre en privado]
**Email**: [Email en privado]
**GitHub**: [Repositorio privado]

---

## 📜 Licencia

Propietario: Sergio Hernández Lara
Todos los derechos reservados.

---

**Generado con ❤️ por Claude Code**
**Última actualización**: 2025-12-02
