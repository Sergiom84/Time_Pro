# Guía de Implementación - Sistema de Solicitudes y Adjuntos

## 📋 Tabla de Contenidos
1. [Resumen de Cambios](#resumen-de-cambios)
2. [Nuevos Estados de Solicitudes](#nuevos-estados-de-solicitudes)
3. [Sistema de Adjuntos con Supabase](#sistema-de-adjuntos-con-supabase)
4. [Filtros y Navegación](#filtros-y-navegación)
5. [Problemas Resueltos](#problemas-resueltos)
6. [Estructura de Base de Datos](#estructura-de-base-de-datos)
7. [Archivos Modificados](#archivos-modificados)
8. [Testing](#testing)

---

## 🎯 Resumen de Cambios

### Funcionalidades Implementadas

#### 1. **Sistema de Estados Diferenciado**
- **Vacaciones y Permisos**: `Pendiente` → `Aprobado` / `Rechazado`
- **Bajas y Ausencias**: `Enviado` → `Recibido`
- Cambio automático de estado cuando el admin visualiza las solicitudes

#### 2. **Sistema de Adjuntos con Supabase Storage**
- Upload de archivos PDF, JPG, PNG
- Almacenamiento en Supabase Storage
- Visualización de documentos en modal
- Soporte para imágenes y PDFs embebidos

#### 3. **Filtros Avanzados en Gestión de Solicitudes**
- Filtro por Centro
- Filtro por Categoría
- Búsqueda por nombre o usuario
- Navegación por semanas para el histórico

#### 4. **Visualizadores de Documentos**
- Modal para visualizar adjuntos
- Soporte para PDF (embed)
- Soporte para imágenes (visualización completa)
- Botón de descarga
- Implementado en:
  - Gestión de Solicitudes de Imputaciones
  - Gestión de Pausas/Descansos

---

## 📊 Nuevos Estados de Solicitudes

### Modelo Actualizado

```python
# models/models.py - LeaveRequest
status = db.Column(
    db.Enum(
        "Pendiente", "Aprobado", "Rechazado", "Cancelado",
        "Enviado", "Recibido",
        name="request_status_enum"
    ),
    nullable=False,
    default="Pendiente"
)

# Nuevos campos de seguimiento
read_by_admin = db.Column(db.Boolean, default=False, nullable=False)
read_date = db.Column(db.DateTime, nullable=True)
```

### Lógica de Estados

#### Para Empleados (Dashboard)
```javascript
// employee_dashboard.html - Líneas 789-797
let statusText = request.status;
if (request.request_type === 'Vacaciones' || request.request_type === 'Permiso especial') {
  // Vacaciones: Muestra "Pendiente" o "Aprobado"
  if (request.status === 'Enviado') statusText = 'Pendiente';
} else {
  // Bajas y Ausencias: Muestra "Enviado" o "Recibido"
  if (request.status === 'Pendiente') statusText = 'Enviado';
}
```

#### Para Administradores
```python
# routes/admin.py - Líneas 922-928
leave_types = ["Baja médica", "Ausencia justificada", "Ausencia injustificada"]
for leave_req in pending_requests:
    if leave_req.request_type in leave_types and leave_req.status == "Enviado":
        leave_req.status = "Recibido"
        leave_req.read_by_admin = True
        leave_req.read_date = datetime.now()
```

---

## 📎 Sistema de Adjuntos con Supabase

### Configuración

```python
# config/supabase_config.py
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")  # Opcional pero recomendado

STORAGE_BUCKET = "Justificantes"
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
```

### Variables de Entorno Necesarias

```bash
# .env
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_ANON_KEY=tu_anon_key_aqui
SUPABASE_SERVICE_KEY=tu_service_role_key_aqui  # Opcional
```

### Proceso de Upload

```python
# utils/file_utils.py - upload_file_to_supabase()

1. Validar archivo (tamaño, extensión, tipo)
2. Sanitizar nombre del archivo
3. Leer contenido del archivo
4. Upload a Supabase usando requests (no httpx)
5. Generar Signed URL para acceso
6. Retornar metadata del archivo
```

### Estructura de Almacenamiento

```
Justificantes/
├── solicitudes/
│   ├── user_1/
│   │   ├── Baja_Medica_20251103_204730.pdf
│   │   └── Justificante_20251104_101520.jpg
│   └── user_2/
│       └── Permiso_20251105_153045.pdf
└── pausas/
    ├── user_1/
    │   └── Descanso_20251103_120000.jpg
    └── user_3/
        └── Almuerzo_20251104_140000.pdf
```

### Por qué usar `requests` en lugar de `httpx`

**Problema encontrado:**
```
httpx.RemoteProtocolError: illegal request line
```

**Solución:**
```python
# Antes (con httpx a través de supabase-py)
response = client.storage.from_(STORAGE_BUCKET).upload(...)  # ❌ Error

# Después (con requests directamente)
response = requests.post(upload_url, data=file_content, headers=headers)  # ✅ OK
```

**Beneficios:**
- Control total sobre la petición HTTP
- Sin problemas de protocolo
- Mejor manejo de errores
- Más logging para debugging

---

## 🔍 Filtros y Navegación

### Gestión de Solicitudes de Imputaciones

#### Filtros Disponibles
```html
<!-- admin_leave_requests.html -->
<form method="GET" action="/admin/leave_requests">
  <!-- Centro -->
  <select name="centro">
    <option value="all">Todos</option>
    <option value="Centro 1">Centro 1</option>
    <option value="Centro 2">Centro 2</option>
    <option value="Centro 3">Centro 3</option>
  </select>

  <!-- Categoría -->
  <select name="categoria">
    <option value="all">Todas</option>
    <option value="Coordinador">Coordinador</option>
    <option value="Empleado">Empleado</option>
    <option value="Gestor">Gestor</option>
  </select>

  <!-- Buscar Usuario -->
  <input type="text" name="usuario" placeholder="Nombre, apellido o usuario...">
</form>
```

#### Navegación por Semanas
```python
# routes/admin.py - Líneas 884-910
week_offset = int(request.args.get("week_offset", "0"))
current_week_start = today - timedelta(days=today.weekday())
week_start = current_week_start + timedelta(weeks=week_offset)
week_end = week_start + timedelta(days=6)
week_text = f"Semana {week_number} ({week_start.strftime('%d')} - {week_end.strftime('%d de %B')})"
```

#### Botones de Navegación
- **Semana Actual**: Muestra la semana en curso (turquesa)
- **Semana Siguiente**: Avanza una semana
- **Semana Anterior**: Retrocede una semana (solo visible si `week_offset > 0`)

### Gestión de Pausas/Descansos

#### Navegación por Días
```python
# Similar a solicitudes pero por días
filter_date = request.args.get("date", datetime.now().strftime('%Y-%m-%d'))
prev_date = (filter_date - timedelta(days=1)).strftime('%Y-%m-%d')
next_date = (filter_date + timedelta(days=1)).strftime('%Y-%m-%d')
```

---

## 🐛 Problemas Resueltos

### 1. Error "illegal request line" en httpx

**Síntoma:**
```
httpx.RemoteProtocolError: illegal request line
POST /time/requests/new HTTP/1.1" 400
```

**Causa:**
- Conflicto en httpx al enviar archivos binarios a Supabase
- Problema con el formato de la petición HTTP

**Solución:**
```python
# utils/file_utils.py - Líneas 155-190
import requests

# Usar requests directamente
response = requests.post(
    upload_url,
    data=file_content,
    headers={
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": mime_type,
        "x-upsert": "true"
    },
    timeout=30
)
```

### 2. CHECK Constraint Desactualizado

**Síntoma:**
```sql
ERROR: new row violates check constraint "leave_request_status_check"
DETAIL: Failing row contains (..., Enviado, ...)
```

**Causa:**
- La migración actualizó el ENUM pero no el CHECK constraint
- El constraint seguía validando solo los estados antiguos

**Solución:**
```sql
-- fix_status_constraint.py
ALTER TABLE leave_request DROP CONSTRAINT leave_request_status_check;

ALTER TABLE leave_request ADD CONSTRAINT leave_request_status_check
CHECK (status::text = ANY (ARRAY[
    'Pendiente', 'Aprobado', 'Rechazado', 'Cancelado',
    'Enviado', 'Recibido'  -- NUEVOS
]));
```

### 3. Conflicto de Variables en Python

**Síntoma:**
```python
UnboundLocalError: cannot access local variable 'request' where it is not associated with a value
```

**Causa:**
```python
# routes/admin.py
for request in pending_requests:  # ❌ Sobrescribe el objeto request de Flask
    ...
filter_centro = request.args.get("centro")  # ❌ Error
```

**Solución:**
```python
for leave_req in pending_requests:  # ✅ Usar nombre diferente
    if leave_req.request_type in leave_types:
        leave_req.status = "Recibido"
```

### 4. Configuración de Supabase Keys

**Problema Inicial:**
```python
# config/supabase_config.py
SUPABASE_KEY = os.getenv("SUPABASE_KEY")  # ❌ No existe en .env
```

**Solución:**
```python
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")  # De .env
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")  # Opcional
SUPABASE_KEY = os.getenv("SUPABASE_KEY") or SUPABASE_SERVICE_KEY or SUPABASE_ANON_KEY
```

---

## 🗄️ Estructura de Base de Datos

### Tabla: `leave_request`

```sql
CREATE TABLE leave_request (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES "user"(id) ON DELETE CASCADE NOT NULL,
    request_type leave_type_enum NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    reason TEXT,
    status request_status_enum NOT NULL DEFAULT 'Pendiente',
    approved_by INTEGER REFERENCES "user"(id),
    approval_date TIMESTAMP,

    -- Nuevos campos para seguimiento
    read_by_admin BOOLEAN DEFAULT FALSE NOT NULL,
    read_date TIMESTAMP,

    -- Campos para archivos adjuntos
    attachment_url VARCHAR(500),
    attachment_filename VARCHAR(255),
    attachment_type VARCHAR(50),
    attachment_size INTEGER,

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Enum de tipos
CREATE TYPE leave_type_enum AS ENUM (
    'Vacaciones',
    'Baja médica',
    'Ausencia justificada',
    'Ausencia injustificada',
    'Permiso especial'
);

-- Enum de estados (ACTUALIZADO)
CREATE TYPE request_status_enum AS ENUM (
    'Pendiente',
    'Aprobado',
    'Rechazado',
    'Cancelado',
    'Enviado',    -- NUEVO
    'Recibido'    -- NUEVO
);

-- Check Constraint (ACTUALIZADO)
ALTER TABLE leave_request
ADD CONSTRAINT leave_request_status_check
CHECK (status::text = ANY (ARRAY[
    'Pendiente', 'Aprobado', 'Rechazado', 'Cancelado',
    'Enviado', 'Recibido'
]));
```

### Tabla: `work_pause`

```sql
CREATE TABLE work_pause (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES "user"(id) ON DELETE CASCADE NOT NULL,
    time_record_id INTEGER REFERENCES time_record(id) ON DELETE CASCADE NOT NULL,
    pause_type pause_type_enum NOT NULL,
    pause_start TIMESTAMP NOT NULL,
    pause_end TIMESTAMP,
    notes TEXT,

    -- Campos para archivos adjuntos
    attachment_url VARCHAR(500),
    attachment_filename VARCHAR(255),
    attachment_type VARCHAR(50),
    attachment_size INTEGER,

    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## 📁 Archivos Modificados

### Backend (Python)

#### `models/models.py`
**Cambios:**
- Añadidos estados `Enviado` y `Recibido` al enum
- Nuevos campos `read_by_admin` y `read_date`

**Líneas clave:** 172-183

#### `routes/time.py`
**Cambios:**
- Lógica actualizada para asignar estado `Enviado` a bajas/ausencias
- Mejor manejo de errores en upload de archivos
- Logging detallado para debugging

**Líneas clave:** 531-589

#### `routes/admin.py`
**Cambios:**
- Cambio automático de `Enviado` → `Recibido` al visualizar
- Filtros por centro, categoría y usuario
- Navegación por semanas
- Fix de conflicto de variables (`request` → `leave_req`)

**Líneas clave:** 873-1002

#### `utils/file_utils.py`
**Cambios:**
- Reescritura completa del upload usando `requests`
- Generación de signed URLs
- Validación robusta de archivos
- Logging exhaustivo

**Líneas clave:** 94-235

#### `config/supabase_config.py`
**Cambios:**
- Soporte para múltiples tipos de keys
- Fallback automático entre keys

**Líneas clave:** 10-15

### Frontend (HTML/JavaScript)

#### `src/templates/employee_dashboard.html`
**Cambios:**
- Lógica para mostrar estados correctos según tipo de solicitud
- Colores actualizados para nuevos estados
- Mejor UX en visualización de solicitudes

**Líneas clave:** 778-822

#### `src/templates/admin_leave_requests.html`
**Cambios:**
- Sección de filtros compacta
- Navegación por semanas con botones
- Modal de visualización de adjuntos (ya existente)
- Diseño responsive

**Líneas clave:** 6-68

#### `src/templates/admin_work_pauses.html`
**Cambios:**
- Diseño de filtros compacto
- Navegación por días
- Modal de visualización de adjuntos

**Líneas clave:** 6-43

### Migraciones

#### `migrations/add_read_tracking_to_leave_requests.sql`
```sql
-- Añadir nuevos estados al enum
-- Añadir campos read_by_admin y read_date
-- Actualizar solicitudes existentes
```

#### Scripts de Utilidad Creados

1. **`apply_leave_request_update.py`**
   - Aplica migración de estados y campos de seguimiento

2. **`fix_status_constraint.py`**
   - Actualiza CHECK constraint con nuevos estados

3. **`check_enum_status.py`**
   - Verifica estados en el enum de BD

4. **`check_constraints.py`**
   - Lista todos los CHECK constraints de la tabla

5. **`test_supabase_upload.py`**
   - Prueba conexión y upload a Supabase

6. **`test_upload_with_requests.py`**
   - Prueba upload usando requests directamente

---

## 🧪 Testing

### Tests Manuales Realizados

#### 1. Upload de Archivos
```bash
python test_upload_with_requests.py
# ✅ Upload exitoso
# ✅ Signed URL generada
# ✅ Eliminación correcta
```

#### 2. Estados de Solicitudes
- ✅ Vacaciones: `Pendiente` → `Aprobado`
- ✅ Baja médica: `Enviado` → `Recibido` (automático al visualizar)
- ✅ Visualización correcta en dashboard del empleado

#### 3. Filtros y Navegación
- ✅ Filtro por centro funciona
- ✅ Filtro por categoría funciona
- ✅ Búsqueda de usuarios funciona
- ✅ Navegación por semanas funciona
- ✅ Filtros se mantienen al navegar entre semanas

#### 4. Visualización de Adjuntos
- ✅ PDF se muestra embebido en modal
- ✅ Imágenes se muestran con tamaño completo
- ✅ Botón de descarga funciona
- ✅ Modal se cierra correctamente

### Casos de Prueba Sugeridos

#### Test 1: Crear Solicitud con Adjunto (Empleado)
```
1. Login como empleado
2. Click en "Imputaciones"
3. Seleccionar "Baja médica"
4. Rellenar fechas y motivo
5. Adjuntar un PDF de prueba
6. Enviar solicitud
✅ Esperado: Solicitud creada con estado "Enviado", archivo subido
```

#### Test 2: Visualizar Solicitud (Admin)
```
1. Login como admin
2. Ir a "Gestión de Solicitudes"
3. Ver la solicitud de baja médica
✅ Esperado: Estado cambia automáticamente a "Recibido"
```

#### Test 3: Aprobar Vacaciones (Admin)
```
1. Empleado crea solicitud de vacaciones
2. Admin ve solicitud (estado: "Pendiente")
3. Admin aprueba la solicitud
✅ Esperado: Estado cambia a "Aprobado"
```

#### Test 4: Visualizar Adjunto (Admin)
```
1. Click en botón "Ver" de justificante
2. Verificar que se abre el modal
3. PDF se visualiza correctamente
4. Click en "Descargar"
✅ Esperado: Archivo se descarga correctamente
```

---

## 📝 Notas Importantes

### Seguridad

1. **Validación de Archivos**
   - Extensiones permitidas: PDF, PNG, JPG, JPEG
   - Tamaño máximo: 5MB
   - Nombres sanitizados automáticamente

2. **Autenticación**
   - Bucket privado en Supabase
   - Signed URLs con expiración (1 año)
   - Solo usuarios autenticados pueden subir/ver archivos

3. **Permisos**
   - Empleados solo ven sus propias solicitudes
   - Admins de centro solo ven solicitudes de su centro
   - Super Admin ve todas las solicitudes

### Performance

1. **Almacenamiento**
   - Archivos en Supabase Storage (no en BD)
   - Solo URLs y metadata en PostgreSQL
   - Carga bajo demanda de adjuntos

2. **Consultas Optimizadas**
   - Joins eficientes con User
   - Límites en consultas de histórico
   - Índices en campos filtrados

### Mantenimiento

1. **Limpieza de Archivos**
   - Considerar implementar limpieza de archivos huérfanos
   - Política de retención de adjuntos antiguos

2. **Logs**
   - Logging detallado en uploads
   - Tracking de cambios de estado
   - Historial de aprobaciones

3. **Backup**
   - Base de datos: Automático en Supabase
   - Storage: Automático en Supabase
   - Considerar exportaciones periódicas

---

## 🚀 Despliegue

### Checklist Pre-Deploy

- [ ] Variables de entorno configuradas en Render
  - `SUPABASE_URL`
  - `SUPABASE_ANON_KEY`
  - `SUPABASE_SERVICE_KEY` (recomendado)

- [ ] Bucket "Justificantes" creado en Supabase

- [ ] Políticas de Storage configuradas en Supabase

- [ ] Migraciones aplicadas:
  - [ ] `apply_leave_request_update.py`
  - [ ] `fix_status_constraint.py`

- [ ] Tests manuales pasados

- [ ] `requirements.txt` actualizado con `requests==2.32.5`

### Variables de Entorno en Render

```bash
DATABASE_URL=postgresql://...
FLASK_ENV=production
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_ANON_KEY=tu_anon_key
SUPABASE_SERVICE_KEY=tu_service_key  # Recomendado para storage
```

### Comandos de Deploy

```bash
# En Render, se ejecuta automáticamente:
pip install -r requirements.txt
gunicorn main:app
```

---

## 📚 Referencias

### Documentación Externa
- [Supabase Storage API](https://supabase.com/docs/guides/storage)
- [Flask File Uploads](https://flask.palletsprojects.com/en/3.0.x/patterns/fileuploads/)
- [Requests Library](https://requests.readthedocs.io/)
- [PostgreSQL ENUM Types](https://www.postgresql.org/docs/current/datatype-enum.html)

### Archivos de Proyecto Relevantes
- `ATTACHMENT_IMPLEMENTATION.md` - Documentación de adjuntos (original)
- `TESTING_GUIDE.md` - Guía de testing (si existe)
- `README.md` - Documentación general del proyecto

---

## 🎉 Resumen Final

### Lo que Funciona
✅ Sistema de estados diferenciado (Vacaciones vs Bajas)
✅ Upload de archivos con Supabase Storage
✅ Visualización de adjuntos en modal
✅ Filtros avanzados con navegación por semanas
✅ Cambio automático de estado al visualizar
✅ Tracking de lectura por administrador
✅ URLs firmadas para acceso seguro
✅ Diseño responsive y compacto

### Mejoras Futuras Sugeridas
- [ ] Notificaciones push cuando cambia el estado
- [ ] Historial de cambios de estado
- [ ] Exportación de solicitudes a PDF/Excel
- [ ] Límite de tamaño de archivo configurable por admin
- [ ] Previsualización de imagen antes de subir
- [ ] Compresión automática de imágenes grandes
- [ ] Soporte para múltiples archivos adjuntos
- [ ] Limpieza automática de archivos antiguos

---

**Fecha de Creación:** 03 de Noviembre de 2025
**Última Actualización:** 03 de Noviembre de 2025
**Versión:** 1.0
**Autor:** Claude Code (Anthropic)
**Proyecto:** Time Tracker - Gestión de Solicitudes y Adjuntos
