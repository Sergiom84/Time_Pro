# 🚀 Guía de Despliegue Multi-Instance (GitHub + Render)

## Arquitectura del Sistema

Time Tracker está diseñado para **despliegue multi-instance**, donde cada cliente tiene:

- ✅ **Su propia instancia** (app independiente en Render)
- ✅ **Su propia base de datos** (PostgreSQL/Supabase)
- ✅ **Su propio dominio** (cliente1.onrender.com, cliente2.onrender.com)
- ✅ **Su propio plan** (Lite o Pro)

### ¿El código actual lo soporta?

**SÍ, completamente.** El sistema ya está preparado para esto:

```
Cliente 1                          Cliente 2                          Cliente 3
├─ timetracker-cliente1.onrender  ├─ timetracker-cliente2.onrender  ├─ timetracker-cliente3.onrender
├─ BD Supabase Cliente 1          ├─ BD Supabase Cliente 2          ├─ BD PostgreSQL Render
├─ APP_PLAN=lite                  ├─ APP_PLAN=pro                   ├─ APP_PLAN=pro
├─ MAX_EMPLOYEES=5                ├─ MAX_EMPLOYEES=unlimited        ├─ MAX_EMPLOYEES=unlimited
└─ .env específico                └─ .env específico                └─ .env específico
```

---

## 📋 Sistema de Planes (config.py)

El código actual usa `config.py` que lee `APP_PLAN` del entorno:

### Plan Lite
```bash
APP_PLAN=lite
```
- ✅ Máximo 5 empleados
- ✅ 1 solo centro
- ❌ Sin selector de centros múltiples

### Plan Pro
```bash
APP_PLAN=pro
```
- ✅ Empleados ilimitados
- ✅ Múltiples centros (Centro 1, Centro 2, Centro 3)
- ✅ Selector de centros en interfaz
- ✅ Restricciones por centro para administradores

---

## 🎯 Preparación para GitHub

### 1. Archivo .env.example

Crea un `.env.example` (sin datos sensibles) para que cada cliente configure el suyo:

```bash
# App Configuration
FLASK_APP=main.py
FLASK_ENV=production
APP_PLAN=pro  # o 'lite'

# Database Configuration
DATABASE_URL=postgresql://user:password@host:5432/database

# Supabase (opcional, solo si usas Supabase Storage)
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_ANON_KEY=tu_anon_key
SUPABASE_KEY=tu_service_role_key

# Email Configuration
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USE_SSL=False
MAIL_USERNAME=tu_correo@gmail.com
MAIL_PASSWORD=tu_password_de_aplicacion
MAIL_DEFAULT_SENDER=TimeTracker <tu_correo@gmail.com>
APP_URL=https://tu-app.onrender.com
```

### 2. .gitignore

Asegúrate de que estos archivos NO se suban a GitHub:

```gitignore
# Environment variables (datos sensibles)
.env

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
ENV/

# Database
*.db
*.sqlite3

# Logs
*.log

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Render
render.yaml  # opcional, cada cliente puede tener el suyo
```

---

## 🌐 Despliegue en Render

### Para cada cliente nuevo:

#### 1. Crear nueva instancia en Render
- Click en "New +" → "Web Service"
- Conectar tu repositorio de GitHub
- Configurar:
  - **Name**: `timetracker-cliente-nombre`
  - **Region**: Europe (Frankfurt) o según ubicación del cliente
  - **Branch**: main
  - **Build Command**: `pip install -r requirements.txt`
  - **Start Command**: `gunicorn -k eventlet -w 1 --bind 0.0.0.0:$PORT main:app`

#### 2. Crear base de datos PostgreSQL
- En Render Dashboard → "New +" → "PostgreSQL"
- **Name**: `timetracker-bd-cliente-nombre`
- **Region**: Same as web service
- Copiar la **Internal Database URL**

#### 3. Configurar Variables de Entorno
En Render → Web Service → Environment:

```bash
# Plan
APP_PLAN=pro  # o 'lite' según el cliente

# Base de datos (usar Internal Database URL de Render)
DATABASE_URL=postgresql://user:password@dpg-xxxxx:5432/database_xxxxx

# Email (específico para cada cliente)
MAIL_USERNAME=cliente@sudominio.com
MAIL_PASSWORD=password_de_aplicacion_gmail
MAIL_DEFAULT_SENDER=TimeTracker Cliente <cliente@sudominio.com>
APP_URL=https://timetracker-cliente-nombre.onrender.com

# SMTP
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USE_SSL=False

# (Opcional) Supabase Storage si el cliente quiere adjuntos
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_ANON_KEY=key
SUPABASE_KEY=service_role_key
```

#### 4. Deploy
- Click en "Manual Deploy" → "Deploy latest commit"
- Esperar 2-5 minutos
- La app estará disponible en `https://timetracker-cliente-nombre.onrender.com`

---

## 📊 Ejemplo Práctico: 3 Clientes

### Cliente A - Empresa Pequeña (Plan Lite)
```yaml
Render Web Service: timetracker-empresa-a
Base de datos: PostgreSQL Render
APP_PLAN=lite
MAX_EMPLOYEES=5
URL: https://timetracker-empresa-a.onrender.com
```

### Cliente B - Empresa Mediana (Plan Pro)
```yaml
Render Web Service: timetracker-empresa-b
Base de datos: Supabase
APP_PLAN=pro
Múltiples centros: Sí
URL: https://timetracker-empresa-b.onrender.com
```

### Cliente C - Corporativo (Plan Pro)
```yaml
Render Web Service: timetracker-corporate-c
Base de datos: PostgreSQL Render
APP_PLAN=pro
Custom domain: fichajes.empresac.com
URL: https://fichajes.empresac.com
```

---

## ⚙️ Configuración Específica por Cliente

### 1. Plan Lite vs Pro

El código **automáticamente** ajusta las funcionalidades según `APP_PLAN`:

**Plan Lite:**
```python
if config.is_lite():
    # Oculta selector de centros
    # Limita a 5 empleados
    # Muestra solo 1 centro
```

**Plan Pro:**
```python
if config.is_pro():
    # Muestra selector de centros
    # Empleados ilimitados
    # Múltiples centros
```

### 2. Email personalizado por cliente

Cada cliente puede usar su propio correo corporativo:

```bash
# Cliente A
MAIL_USERNAME=noreply@empresaa.com
MAIL_DEFAULT_SENDER=Control de Fichajes <noreply@empresaa.com>

# Cliente B
MAIL_USERNAME=rrhh@empresab.com
MAIL_DEFAULT_SENDER=RRHH Empresa B <rrhh@empresab.com>
```

### 3. Dominio personalizado (opcional)

En Render → Settings → Custom Domain:
- `fichajes.empresaa.com` → Cliente A
- `timetracker.empresab.com` → Cliente B

---

## 🔒 Seguridad Multi-Instance

### ✅ Aislamiento Garantizado

Cada instancia está **completamente aislada**:

1. **Base de datos separada** → Los datos NO se comparten entre clientes
2. **App independiente** → Cada cliente tiene su propio código corriendo
3. **Variables de entorno únicas** → Configuración específica por cliente
4. **Sesiones independientes** → No hay cross-contamination

### Verificación de aislamiento:

```python
# Cada instancia tiene su propia:
- db.engine (conexión a BD diferente)
- app.config (configuración única)
- scheduler (proceso independiente)
- mail (servidor SMTP específico)
```

---

## 📦 Estructura del Repositorio en GitHub

```
time-tracker/
├── README.md                    # Descripción general
├── DEPLOYMENT.md               # Esta guía
├── MEJORAS_NOTIFICACIONES.md   # Documentación técnica
├── requirements.txt            # Dependencias
├── .env.example                # Template de configuración
├── .gitignore                  # Archivos a ignorar
├── main.py                     # Punto de entrada
├── config.py                   # Sistema de planes
├── models/                     # Modelos de BD
├── routes/                     # Rutas de la app
├── tasks/                      # Tareas programadas
├── migrations/                 # Migraciones de BD
└── src/
    ├── templates/              # HTML
    └── static/                 # CSS, JS, imágenes
```

---

## 🚀 Checklist de Despliegue Nuevo Cliente

- [ ] 1. Crear Web Service en Render
- [ ] 2. Crear base de datos PostgreSQL en Render
- [ ] 3. Configurar variables de entorno (APP_PLAN, DATABASE_URL, MAIL_*)
- [ ] 4. Deploy inicial
- [ ] 5. Verificar que carga correctamente
- [ ] 6. Ejecutar migraciones (automático en primer deploy)
- [ ] 7. Crear usuario super admin inicial
- [ ] 8. Configurar correo de notificaciones
- [ ] 9. (Opcional) Configurar dominio personalizado
- [ ] 10. Entregar credenciales al cliente

---

## 💰 Costos Estimados (Render)

### Por Cliente:

**Plan Starter (Recomendado para empresas pequeñas/medianas):**
- Web Service: **$7/mes** (512 MB RAM)
- PostgreSQL: **$7/mes** (1 GB storage)
- **Total: $14/mes por cliente**

**Plan Professional (Empresas grandes):**
- Web Service: **$25/mes** (2 GB RAM)
- PostgreSQL: **$25/mes** (10 GB storage)
- **Total: $50/mes por cliente**

**Free Tier (Solo para demos/pruebas):**
- Web Service: **Gratis** (512 MB RAM, duerme después de 15 min inactividad)
- PostgreSQL: **Gratis** (1 GB storage, expira después de 90 días)

---

## 🎓 Modelo de Negocio Sugerido

### Precios de venta al cliente:

**Plan Lite** (Hasta 5 empleados):
- €15-20/mes por cliente
- Margen: €6-13/mes
- Incluye: 1 centro, notificaciones, exportación

**Plan Pro** (Ilimitado):
- €40-60/mes por cliente
- Margen: €15-35/mes
- Incluye: Múltiples centros, empleados ilimitados, soporte prioritario

---

## 📞 Soporte Técnico

### Para nuevos clientes:

1. **Onboarding**: Configurar instancia inicial (1-2 horas)
2. **Capacitación**: Videollamada de 30 min para mostrar funcionalidades
3. **Soporte**: Email/chat para dudas técnicas
4. **Actualizaciones**: Deploy automático desde GitHub

### Actualizaciones globales:

Cuando actualices el código en GitHub:
1. Hacer push a `main`
2. Render detecta el cambio
3. **Cada cliente se actualiza automáticamente**
4. Sin downtime (rolling deploy)

---

## ✅ Resumen

**¿El código actual soporta múltiples clientes?**
- ✅ **SÍ, al 100%**

**¿Cada cliente está aislado?**
- ✅ **SÍ, completamente**

**¿Puedo tener clientes con Plan Lite y Pro al mismo tiempo?**
- ✅ **SÍ, solo cambia `APP_PLAN` en cada instancia**

**¿Es escalable?**
- ✅ **SÍ, puedes tener 1, 10, 100+ clientes**

**¿Es seguro?**
- ✅ **SÍ, cada BD es independiente, zero sharing**

---

**Implementado por**: Time Tracker Team
**Última actualización**: 2025-11-06
**Versión**: 3.0 (con lock distribuido)
