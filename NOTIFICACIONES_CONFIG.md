# Configuración de Notificaciones por Correo

## ✅ Funcionalidad Implementada

Se ha añadido un sistema completo de notificaciones por correo electrónico para recordar a los empleados que fichen su entrada y salida.

### Características:
- ✅ Botón de configuración en el dashboard del empleado
- ✅ Modal interactivo para configurar preferencias
- ✅ Selección de días de la semana (L, M, X, J, V, S, D)
- ✅ Configuración de horarios para entrada y salida
- ✅ Envío automático de correos cada 5 minutos
- ✅ Ventana de 5 minutos antes de la hora configurada
- ✅ Backend con Flask-Mail y APScheduler

## 📋 Pasos para Configurar

### 1. Configurar Variables de Entorno

Crea un archivo `.env` en la raíz del proyecto (puedes copiar `.env.example`):

```bash
# Copiar el archivo de ejemplo
cp .env.example .env
```

### 2. Configurar Cuenta de Correo (Gmail)

Para usar Gmail necesitas generar una **Contraseña de Aplicación**:

1. Ve a tu cuenta de Google: https://myaccount.google.com/
2. En el menú lateral, selecciona "Seguridad"
3. En "Acceso a Google", activa la "Verificación en dos pasos" si no está activa
4. Vuelve a "Seguridad" y busca "Contraseñas de aplicaciones"
5. Genera una nueva contraseña para "Correo"
6. Copia la contraseña generada (16 caracteres)

### 3. Editar el archivo .env

```env
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=tu_correo@gmail.com
MAIL_PASSWORD=xxxx xxxx xxxx xxxx  # Contraseña de aplicación
MAIL_DEFAULT_SENDER=tu_correo@gmail.com
APP_URL=http://localhost:5000  # O tu URL de producción
```

### 4. Aplicar Migración de Base de Datos

Ejecuta el script SQL en tu base de datos:

```bash
# Si estás usando psql (PostgreSQL):
psql -U tu_usuario -d tu_base_de_datos -f migrations/add_email_notifications.sql

# O ejecuta directamente desde un cliente SQL:
-- Copia y pega el contenido de migrations/add_email_notifications.sql
```

### 5. Instalar Dependencias

Si aún no lo has hecho:

```bash
source venv/bin/activate  # Activar entorno virtual
pip install -r requirements.txt
```

### 6. Ejecutar la Aplicación

```bash
source venv/bin/activate
python main.py
```

## 🎯 Cómo Usar las Notificaciones

### Para Empleados:

1. Inicia sesión en tu cuenta de empleado
2. En el dashboard, haz clic en el botón "**Notificaciones**" (icono de calendario)
3. Marca la casilla "**Recibir notificaciones por correo**"
4. Selecciona los días de la semana que trabajas
5. Configura las horas de entrada y salida
6. Haz clic en "**Guardar**"

**Ejemplo de configuración:**
- Días: Lunes, Martes, Miércoles, Jueves, Viernes
- Hora de entrada: 08:45 (recibirás correo entre 08:40 y 08:45)
- Hora de salida: 17:45 (recibirás correo entre 17:40 y 17:45)

## 📧 Formato de los Correos

Los empleados recibirán dos tipos de correos:

### Correo de Entrada:
```
Asunto: ⏰ Recordatorio de Fichaje de Entrada

Hola [Nombre],

Este es un recordatorio para que no olvides fichar tu entrada.

Centro: [Tu Centro]

Puedes fichar desde el panel de empleado en: [URL]

¡Que tengas un buen día!
```

### Correo de Salida:
```
Asunto: ⏰ Recordatorio de Fichaje de Salida

Hola [Nombre],

Este es un recordatorio para que no olvides fichar tu salida.

Centro: [Tu Centro]

Puedes fichar desde el panel de empleado en: [URL]

¡Hasta mañana!
```

## ⚙️ Configuración Técnica

### Frecuencia de Verificación
El sistema verifica cada **5 minutos** si hay usuarios que necesitan recibir notificaciones.

### Ventana de Envío
Los correos se envían en una **ventana de 5 minutos antes** de la hora configurada para evitar spam.

Por ejemplo, si configuras:
- Hora de entrada: 09:00
- El correo se enviará entre las 08:55 y 09:00

### Archivo de Configuración del Scheduler
El scheduler se configura en: `main.py:219-258`

Si quieres cambiar la frecuencia de verificación, edita la línea:
```python
trigger=CronTrigger(minute='*/5'),  # Cada 5 minutos
```

## 🔧 Solución de Problemas

### No se envían correos
1. Verifica que las variables de entorno en `.env` sean correctas
2. Comprueba que la contraseña de aplicación de Gmail esté bien configurada
3. Revisa los logs de la aplicación para ver errores
4. Asegúrate de que el scheduler esté iniciado (verás mensajes en el log al iniciar)

### Error "Authentication failed"
- Verifica que hayas generado una contraseña de aplicación (no uses tu contraseña normal de Gmail)
- Asegúrate de que la verificación en dos pasos esté activa en tu cuenta de Google

### Los correos llegan tarde
- El sistema verifica cada 5 minutos, puede haber un pequeño retraso
- Puedes ajustar la frecuencia en `main.py` si lo necesitas

### Usar otro proveedor de correo (no Gmail)

Para Outlook/Hotmail:
```env
MAIL_SERVER=smtp-mail.outlook.com
MAIL_PORT=587
MAIL_USE_TLS=True
```

Para otros proveedores, consulta su documentación SMTP.

## 📂 Archivos Modificados/Creados

- `models/models.py` - Añadidos campos de notificación al User
- `main.py` - Configuración de Flask-Mail y scheduler
- `tasks/email_service.py` - Lógica de envío de correos (NUEVO)
- `routes/time.py` - Rutas API para preferencias
- `src/templates/employee_dashboard.html` - Botón y modal
- `migrations/add_email_notifications.sql` - Migración SQL (NUEVO)
- `.env.example` - Plantilla de variables de entorno (NUEVO)

## 🎨 Personalización

### Cambiar el contenido de los correos
Edita el archivo `tasks/email_service.py` en la función `send_notification_email()`.

### Cambiar la frecuencia del scheduler
Edita `main.py` línea 244:
```python
trigger=CronTrigger(minute='*/10'),  # Cada 10 minutos
# o
trigger=CronTrigger(minute='0', hour='8,17'),  # Solo a las 8:00 y 17:00
```

## 📞 Soporte

Si tienes problemas o preguntas, revisa los logs de la aplicación:
```bash
python main.py 2>&1 | tee app.log
```
