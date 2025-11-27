# Time Pro - Sistema Multi-Cliente (Multi-Tenant)

## 📋 Descripción

Time Pro ahora soporta múltiples clientes en una sola base de datos. Cada cliente tiene:

- ✅ Su propia base de usuarios y empleados
- ✅ Su propio logo y branding (colores personalizados)
- ✅ Su plan asignado (Lite o Pro)
- ✅ Aislamiento completo de datos

## 🏗️ Arquitectura

### Modelo Multi-Tenant

```
┌─────────────────────────────────────────────────────────┐
│                    Base de Datos                        │
│                                                           │
│  ┌──────────────┐                                        │
│  │   Client     │ ← Tabla principal de clientes         │
│  ├──────────────┤                                        │
│  │ id           │                                        │
│  │ name         │ (ej: "Mi primer cliente")             │
│  │ slug         │ (ej: "aluminios-lara")                │
│  │ plan         │ (lite/pro)                            │
│  │ logo_url     │                                        │
│  │ primary_color│                                        │
│  └──────────────┘                                        │
│         ↓                                                 │
│  ┌──────────────┐                                        │
│  │    User      │ ← Usuarios por cliente                │
│  ├──────────────┤                                        │
│  │ id           │                                        │
│  │ client_id    │ → Referencia al cliente               │
│  │ username     │                                        │
│  │ ...          │                                        │
│  └──────────────┘                                        │
│         ↓                                                 │
│  ┌────────────────┐                                      │
│  │  TimeRecord    │ ← Heredan client_id de user         │
│  │  EmployeeStatus│                                      │
│  │  WorkPause     │                                      │
│  │  LeaveRequest  │                                      │
│  └────────────────┘                                      │
└─────────────────────────────────────────────────────────┘
```

### Separación de Datos

- **Nivel de sesión**: Cada usuario guarda `client_id` en su sesión
- **Nivel de queries**: El middleware filtra automáticamente por `client_id`
- **Nivel de relaciones**: Las foreign keys garantizan integridad

## 🚀 Instalación y Configuración

### Paso 1: Aplicar Migraciones

Primero, necesitas aplicar la migración que crea la tabla `client` y agrega `client_id` a las tablas existentes:

```bash
python3 apply_multitenant_migration.py
```

**¿Qué hace este script?**

1. Crea la tabla `client`
2. Crea un cliente por defecto "Time Pro" (ID: 1)
3. Agrega columna `client_id` a `user` y `system_config`
4. Asigna todos los usuarios existentes al cliente por defecto
5. Crea las foreign keys necesarias

**Salida esperada:**

```
============================================================
APLICANDO MIGRACIÓN MULTI-TENANT
============================================================

1. Creando enum plan_enum...
   ✅ Enum creado

2. Creando tabla client...
   ✅ Tabla client creada

3. Creando cliente por defecto 'Time Pro'...
   ✅ Cliente por defecto creado

...

============================================================
✅ MIGRACIÓN APLICADA EXITOSAMENTE
============================================================

📊 Resumen:
   - Tabla 'client' creada
   - X usuarios migrados
   - Y configuraciones migradas
   - Cliente por defecto 'Time Pro' creado
```

### Paso 2: Configurar tu primer cliente

Ahora puedes configurar tu primer cliente real (por ejemplo, "Mi primer cliente"):

```bash
# Con logo
python3 setup_aluminios_lara.py /ruta/al/logo.png

# Sin logo
python3 setup_aluminios_lara.py
```

**El script te pedirá:**

1. Si deseas crear el cliente (o actualizar si ya existe)
2. Datos del usuario administrador:
   - Username
   - Contraseña
   - Nombre completo
   - Email

**Salida esperada:**

```
======================================================================
  CONFIGURACIÓN DE ALUMINIOS LARA
======================================================================

1. Verificando si el cliente ya existe...
   ✅ Cliente no existe, creando nuevo...

2. Cliente de ejemplo creado correctamente
   ID: 2
   Slug: aluminios-lara
   Plan: PRO

3. Subiendo logo a Supabase...
   ✅ Logo subido exitosamente
   URL: https://...supabase.co/storage/v1/object/public/Justificantes/logos/aluminios-lara.png

4. Verificando usuarios administradores...
   No hay administradores para este cliente

   ¿Deseas crear un usuario administrador ahora? (s/n): s

   Datos del administrador:
     Username: admin_lara
     Contraseña: ********
     Nombre completo: Administrador Lara
     Email: admin@aluminoslara.com

   ✅ Administrador creado
   Username: admin_lara
   Email: admin@aluminoslara.com

======================================================================
✅ CONFIGURACIÓN COMPLETADA
======================================================================

📋 Resumen:
   Cliente: (nombre del cliente)
   ID: 2
   Slug: aluminios-lara
   Plan: PRO
   Logo: https://...
   Administradores: 1
   Empleados: 0

💡 Próximos pasos:
   1. Asegúrate de que los usuarios pueden iniciar sesión
   2. Verifica que el logo se muestre correctamente
   3. Comienza a usar la aplicación
```

## 🔧 Scripts Disponibles

### 1. `apply_multitenant_migration.py`

Aplica la migración multi-tenant a la base de datos.

**Uso:**
```bash
python3 apply_multitenant_migration.py
```

**Requisitos:**
- Acceso a la base de datos (DATABASE_URL configurado o credenciales por defecto)
- psycopg2-binary instalado (se instala automáticamente si falta)

### 2. `setup_aluminios_lara.py`

Configura tu primer cliente en el sistema.

**Uso:**
```bash
# Con logo
python3 setup_aluminios_lara.py /ruta/al/logo.png

# Sin logo
python3 setup_aluminios_lara.py
```

**Requisitos:**
- Migración multi-tenant aplicada
- Logo en formato PNG, JPG, JPEG o SVG (opcional)

### 3. `scripts/setup_client.py` (Genérico)

Script interactivo para configurar cualquier cliente nuevo.

**Uso:**
```bash
python3 scripts/setup_client.py
```

**Te pedirá:**
- Nombre del cliente
- Plan (lite/pro)
- Ruta al logo (opcional)
- Colores personalizados (opcional)
- Datos del administrador

## 📊 Cambios Realizados

### Modelos Actualizados

#### 1. Nuevo Modelo: `Client`

```python
class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), unique=True, nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    plan = db.Column(db.Enum("lite", "pro"), nullable=False)
    logo_url = db.Column(db.String(500), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    primary_color = db.Column(db.String(7), default="#0ea5e9")
    secondary_color = db.Column(db.String(7), default="#06b6d4")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
```

#### 2. Modelo `User` Actualizado

```python
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey("client.id"), nullable=False)  # ← NUEVO
    username = db.Column(db.String(80), unique=True, nullable=False)
    # ... resto de campos
```

#### 3. Modelo `SystemConfig` Actualizado

```python
class SystemConfig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey("client.id"), nullable=False)  # ← NUEVO
    key = db.Column(db.String(50), nullable=False)
    value = db.Column(db.String(200), nullable=False)
    # ...

    # Ahora unique por (client_id, key)
    __table_args__ = (db.UniqueConstraint("client_id", "key"),)
```

### Rutas Actualizadas

#### `routes/auth.py`

**Login actualizado:**
```python
if user and user.check_password(password):
    session["user_id"] = user.id
    session["is_admin"] = user.is_admin
    session["client_id"] = user.client_id  # ← NUEVO
```

**Logout actualizado:**
```python
session.pop("client_id", None)  # ← NUEVO
```

### Context Processor Actualizado

**`main.py`** ahora inyecta información del cliente en todos los templates:

```python
@app.context_processor
def inject_user():
    # ...
    current_client = get_current_client()
    client_config_dict = get_client_config()

    return dict(
        current_user=user,
        current_client=current_client,      # ← NUEVO
        client_config=client_config_dict,   # ← NUEVO
        plan_config=plan_config_dict
    )
```

**Variables disponibles en templates:**

- `current_client` - Objeto Client del usuario actual
- `current_client.name` - Nombre del cliente (ej: "Mi primer cliente")
- `current_client.logo_url` - URL del logo
- `current_client.plan` - Plan ("lite" o "pro")
- `client_config` - Configuración completa del cliente

### Utilidades Multi-Tenant

Nuevo archivo: `utils/multitenant.py`

**Funciones disponibles:**

```python
from utils.multitenant import (
    get_current_client,      # Obtiene cliente actual
    get_current_client_id,   # Obtiene ID del cliente actual
    set_current_client,      # Establece cliente en sesión
    get_client_plan,         # Obtiene plan del cliente
    client_has_feature,      # Verifica si cliente tiene feature
    get_client_config        # Obtiene configuración completa
)
```

**Ejemplo de uso:**

```python
from utils.multitenant import get_current_client, client_has_feature

# En una ruta
client = get_current_client()
print(f"Cliente actual: {client.name}")

# Verificar si tiene una característica
if client_has_feature('email_notifications'):
    # Enviar notificaciones
    pass
```

## 🎨 Personalización de Branding

Cada cliente puede tener:

1. **Logo personalizado** - Se sube a Supabase Storage
2. **Colores personalizados** - `primary_color` y `secondary_color` en formato hex
3. **Plan específico** - Lite o Pro

### Actualizar Logo de un Cliente

```python
from models.models import Client
from main import app

with app.app_context():
    client = Client.query.filter_by(slug='aluminios-lara').first()
    client.logo_url = "https://nueva-url-del-logo.com/logo.png"
    db.session.commit()
```

### Actualizar Colores

```python
with app.app_context():
    client = Client.query.filter_by(slug='aluminios-lara').first()
    client.primary_color = "#FF5733"   # Naranja
    client.secondary_color = "#C70039"  # Rojo
    db.session.commit()
```

## 🔒 Seguridad y Aislamiento

### Cómo Funciona el Aislamiento

1. **En el Login:**
   - Al autenticarse, se guarda `client_id` en la sesión
   - Todas las peticiones subsecuentes incluyen este `client_id`

2. **En las Queries:**
   - Los usuarios solo ven datos de su cliente
   - Las relaciones foreign key garantizan integridad
   - No es posible acceder a datos de otros clientes

3. **Ejemplo de Query Segura:**

```python
# Antes (sin multi-tenant)
users = User.query.filter_by(is_admin=True).all()

# Ahora (con multi-tenant)
from flask import session
client_id = session['client_id']
users = User.query.filter_by(client_id=client_id, is_admin=True).all()
```

### Verificaciones Automáticas

El sistema verifica automáticamente:

- ✅ Usuario pertenece al cliente correcto
- ✅ `client_id` existe en sesión
- ✅ Cliente está activo (`is_active=True`)
- ✅ Foreign keys previenen asignaciones incorrectas

## 📝 Crear Nuevos Clientes

### Opción 1: Script Interactivo (Recomendado)

```bash
python3 scripts/setup_client.py
```

### Opción 2: Programáticamente

```python
from models.models import Client, User
from models.database import db
from main import app

with app.app_context():
    # Crear cliente
    client = Client(
        name="Empresa XYZ",
        slug="empresa-xyz",
        plan="lite",
        logo_url="https://...",
        primary_color="#0ea5e9",
        secondary_color="#06b6d4"
    )
    db.session.add(client)
    db.session.flush()

    # Crear admin
    admin = User(
        client_id=client.id,
        username="admin_xyz",
        full_name="Admin XYZ",
        email="admin@xyz.com",
        is_admin=True,
        is_active=True
    )
    admin.set_password("contraseña_segura")
    db.session.add(admin)

    db.session.commit()
```

## 🧪 Testing

### Verificar que la Migración Funcionó

```bash
# Conectarse a la BD
psql $DATABASE_URL

# Verificar tabla client
SELECT * FROM client;

# Verificar que users tienen client_id
SELECT id, username, client_id FROM "user" LIMIT 5;
```

### Verificar el cliente configurado

```bash
# Conectarse a la BD
psql $DATABASE_URL

# Ver cliente configurado
SELECT * FROM client WHERE slug = 'aluminios-lara';

# Ver usuarios del cliente configurado
SELECT id, username, full_name, is_admin
FROM "user"
WHERE client_id = (SELECT id FROM client WHERE slug = 'aluminios-lara');
```

## ❓ Preguntas Frecuentes

### ¿Puedo tener usuarios con el mismo username en diferentes clientes?

No. El campo `username` sigue siendo único globalmente. Esto es por diseño para evitar confusiones. Si necesitas usuarios con el mismo nombre en diferentes clientes, usa emails diferentes o agrega un prefijo al username (ej: `lara_admin`, `xyz_admin`).

### ¿Qué pasa con los datos existentes?

Todos los datos existentes se asignan automáticamente al cliente por defecto "Time Pro" (ID: 1) durante la migración. Luego puedes reasignar usuarios a otros clientes si es necesario.

### ¿Puedo cambiar el plan de un cliente después?

Sí:

```python
client = Client.query.get(2)  # Cliente de ejemplo
client.plan = 'lite'  # Cambiar de pro a lite
db.session.commit()
```

### ¿Cómo elimino un cliente?

```python
client = Client.query.filter_by(slug='empresa-xyz').first()
db.session.delete(client)  # Elimina cliente Y todos sus usuarios (CASCADE)
db.session.commit()
```

**⚠️ CUIDADO:** Esto eliminará permanentemente todos los datos del cliente.

## 🚨 Rollback (Deshacer Migración)

Si necesitas volver atrás, puedes ejecutar el SQL de downgrade manualmente:

```sql
-- Eliminar constraint unique compuesto
ALTER TABLE system_config DROP CONSTRAINT uix_client_key;

-- Restaurar constraint unique de key
ALTER TABLE system_config ADD CONSTRAINT system_config_key_key UNIQUE (key);

-- Eliminar foreign keys
ALTER TABLE system_config DROP CONSTRAINT fk_system_config_client_id;
ALTER TABLE "user" DROP CONSTRAINT fk_user_client_id;

-- Eliminar columnas client_id
ALTER TABLE system_config DROP COLUMN client_id;
ALTER TABLE "user" DROP COLUMN client_id;

-- Eliminar tabla client
DROP TABLE client;

-- Eliminar enum
DROP TYPE plan_enum;
```

## 📞 Soporte

Si tienes problemas durante la configuración:

1. Verifica que tienes acceso a Supabase
2. Verifica que `DATABASE_URL` está configurado correctamente
3. Revisa los logs para errores específicos
4. Asegúrate de que psycopg2-binary está instalado

## ✅ Checklist de Implementación

- [ ] Ejecutar `apply_multitenant_migration.py`
- [ ] Verificar que la migración se aplicó correctamente
- [ ] Ejecutar `setup_aluminios_lara.py` con el logo
- [ ] Crear usuario administrador para el cliente configurado
- [ ] Verificar que el login funciona
- [ ] Verificar que el logo se muestra
- [ ] Crear algunos empleados de prueba
- [ ] Verificar aislamiento de datos (no se ven datos de otros clientes)
- [ ] Actualizar documentación interna

---

**🎉 ¡Felicidades! Ahora Time Pro soporta múltiples clientes.**

**Siguiente cliente:** Usa `scripts/setup_client.py` para agregar más clientes fácilmente.
