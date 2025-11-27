# Guía de Pruebas - Patacones de mi tierra (Plan LITE)

Esta guía te ayudará a verificar que el cliente "Patacones de mi tierra" funciona correctamente.

## Pre-requisitos

Antes de empezar, asegúrate de haber:

1. ✅ Creado el cliente "Patacones de mi tierra"
2. ✅ Creado el administrador
3. ✅ (Opcional) Creado empleados de prueba

## Configuración Inicial

### 1. Verificar el archivo .env

Asegúrate de que el archivo `.env` existe y tiene la configuración correcta:

```bash
DATABASE_URL=postgresql://postgres.gqesfclbingbihakiojm:...@aws-1-eu-west-1.pooler.supabase.com:6543/postgres
SUPABASE_URL=https://gqesfclbingbihakiojm.supabase.co
SUPABASE_ANON_KEY=...
SUPABASE_SERVICE_ROLE_KEY=...
APP_PLAN=pro  # Nota: Este es el plan por defecto, cada cliente tiene su propio plan en la BD
SECRET_KEY=dev-secret-key-change-in-production
FLASK_ENV=development
```

### 2. Iniciar la aplicación

Desde PowerShell o terminal:

```bash
python main.py
```

O si estás en producción:

```bash
gunicorn --config gunicorn.conf.py wsgi:app
```

Deberías ver:

```
 * Running on http://127.0.0.1:5000
```

### 3. Acceder a la aplicación

Abre tu navegador y ve a: `http://localhost:5000`

---

## Pruebas del Administrador

### Prueba 1: Inicio de sesión del administrador

1. En la página de login, introduce:
   - **Username**: `admin_patacones`
   - **Password**: `Patacones2025!`

2. Click en "Iniciar Sesión"

3. **Resultado esperado**:
   - ✅ Deberías ver el panel de administrador
   - ✅ En la parte superior debe decir "Patacones de mi tierra"
   - ✅ NO debe aparecer un selector de centros (es plan LITE con 1 solo centro)

### Prueba 2: Verificar restricciones del Plan LITE

1. Ve a **Gestionar Empleados**

2. **Resultado esperado**:
   - ✅ Debe mostrar el administrador y los empleados creados
   - ✅ Debe haber un límite visible de 5 empleados máximo

3. Intenta crear un sexto empleado:
   - **Resultado esperado**: Debería aparecer un mensaje indicando que has alcanzado el límite del plan LITE

### Prueba 3: Crear un empleado nuevo

1. Click en **"Añadir Empleado"**

2. Completa el formulario:
   - **Username**: `test_empleado`
   - **Nombre completo**: `Empleado de Prueba`
   - **Email**: `test@pataconesdetierra.com`
   - **Contraseña**: `Test2025!`
   - **Horas semanales**: `40`
   - **Centro**: `Patacones de mi tierra` (debe ser el único disponible)
   - **Categoría**: Selecciona "Camarero" o "Cocinero"

3. Click en **"Guardar"**

4. **Resultado esperado**:
   - ✅ El empleado debe crearse correctamente
   - ✅ Debe aparecer en la lista de empleados
   - ✅ El contador de empleados debe aumentar

### Prueba 4: Gestionar centros y categorías

1. Ve a **Configuración** → **Centros**

2. **Resultado esperado**:
   - ✅ Debe aparecer solo "Patacones de mi tierra"
   - ✅ Como es plan LITE, NO debe permitir crear más centros

3. Ve a **Configuración** → **Categorías**

4. **Resultado esperado**:
   - ✅ Deben aparecer las categorías: Cocinero, Camarero, Gestor
   - ✅ Debes poder crear nuevas categorías si es necesario

---

## Pruebas del Empleado

### Prueba 5: Inicio de sesión como empleado

1. Cierra sesión del administrador

2. Inicia sesión con uno de los empleados de prueba:
   - **Username**: `maria_gomez`
   - **Password**: `Maria2025!`

3. **Resultado esperado**:
   - ✅ Deberías ver el dashboard del empleado
   - ✅ Debe mostrar el nombre "María Gómez"
   - ✅ NO debe tener acceso a funciones de administración

### Prueba 6: Registrar entrada (fichaje)

1. En el dashboard del empleado, click en **"Registrar Entrada"**

2. **Resultado esperado**:
   - ✅ Debe aparecer un mensaje de confirmación
   - ✅ La hora de entrada debe registrarse
   - ✅ El botón debe cambiar a "Registrar Salida"

3. Verifica en la tabla de registros:
   - ✅ Debe aparecer el fichaje de hoy con la hora de entrada

### Prueba 7: Registrar pausa

1. Click en **"Registrar Pausa"**

2. Selecciona:
   - **Tipo de pausa**: "Hora del almuerzo"
   - **Notas**: "Almuerzo"

3. Click en **"Iniciar Pausa"**

4. **Resultado esperado**:
   - ✅ La pausa debe iniciarse
   - ✅ Debe aparecer el timer de pausa activa

5. Click en **"Finalizar Pausa"**

6. **Resultado esperado**:
   - ✅ La pausa debe registrarse correctamente
   - ✅ La duración debe calcularse automáticamente

### Prueba 8: Registrar salida

1. Click en **"Registrar Salida"**

2. **Resultado esperado**:
   - ✅ La hora de salida debe registrarse
   - ✅ La duración total del trabajo debe calcularse (restando pausas)
   - ✅ El botón debe volver a "Registrar Entrada"

### Prueba 9: Solicitar vacaciones

1. Ve a **Solicitudes** → **Nueva Solicitud**

2. Completa el formulario:
   - **Tipo**: "Vacaciones"
   - **Fecha inicio**: Selecciona una fecha futura
   - **Fecha fin**: Selecciona una fecha futura (después de la fecha de inicio)
   - **Motivo**: "Vacaciones de verano"

3. Click en **"Enviar Solicitud"**

4. **Resultado esperado**:
   - ✅ La solicitud debe crearse con estado "Pendiente"
   - ✅ Debe aparecer en la lista de solicitudes del empleado

---

## Pruebas de Administración

### Prueba 10: Revisar solicitudes de empleados

1. Cierra sesión e inicia sesión como administrador

2. Ve a **Solicitudes** o **Gestión de Solicitudes**

3. **Resultado esperado**:
   - ✅ Debe aparecer la solicitud de vacaciones creada por María Gómez
   - ✅ Debe estar marcada como "Pendiente"
   - ✅ Debe tener un badge o indicador de "sin leer"

### Prueba 11: Aprobar/Rechazar solicitudes

1. Click en la solicitud de vacaciones

2. Revisa los detalles

3. Añade una nota en **Notas del administrador**: "Aprobado"

4. Selecciona **"Aprobar"** y click en **"Guardar"**

5. **Resultado esperado**:
   - ✅ El estado debe cambiar a "Aprobado"
   - ✅ La fecha de aprobación debe registrarse
   - ✅ El empleado debe poder ver el estado actualizado

### Prueba 12: Ver reportes

1. Ve a **Reportes** → **Reporte Mensual**

2. Selecciona el mes actual

3. **Resultado esperado**:
   - ✅ Debe mostrar todos los fichajes del mes
   - ✅ Debe calcular correctamente las horas trabajadas
   - ✅ Debe mostrar las pausas registradas
   - ✅ Debe mostrar los días con solicitudes aprobadas

### Prueba 13: Exportar datos

1. En la página de reportes, click en **"Exportar a Excel"**

2. **Resultado esperado**:
   - ✅ Debe descargarse un archivo Excel
   - ✅ El archivo debe contener todos los datos del reporte
   - ✅ Debe estar correctamente formateado

---

## Pruebas de Seguridad y Permisos

### Prueba 14: Aislamiento de clientes (Multi-tenant)

1. Intenta acceder a datos de otro cliente (si tienes más clientes):
   - Por ejemplo, modifica la URL para ver datos de client_id=1

2. **Resultado esperado**:
   - ✅ NO debes poder ver datos de otros clientes
   - ✅ Todos los datos deben estar filtrados por client_id

### Prueba 15: Permisos de empleados

1. Inicia sesión como empleado (no administrador)

2. Intenta acceder a URLs de administración:
   - `http://localhost:5000/admin/users`
   - `http://localhost:5000/admin/reports`

3. **Resultado esperado**:
   - ✅ Debes ser redirigido al dashboard del empleado
   - ✅ Debe aparecer un mensaje de "Acceso denegado" o similar

---

## Pruebas de Integridad de Datos

### Prueba 16: Validaciones de formularios

1. Intenta crear un empleado con email duplicado

2. **Resultado esperado**:
   - ✅ Debe mostrar un error indicando que el email ya existe

3. Intenta crear un empleado sin completar campos obligatorios

4. **Resultado esperado**:
   - ✅ Debe mostrar errores de validación

### Prueba 17: Registro de auditoría

1. Como administrador, modifica un fichaje de un empleado:
   - Ve a **Gestionar Registros**
   - Edita un registro existente
   - Añade una nota en **Notas del administrador**

2. **Resultado esperado**:
   - ✅ El campo `modified_by` debe registrar el ID del administrador
   - ✅ El campo `updated_at` debe actualizarse

---

## Pruebas de UI/UX

### Prueba 18: Temas y personalización

1. En el perfil del usuario, cambia el tema:
   - Click en el botón de **"Cambiar Tema"**
   - Prueba los temas disponibles

2. **Resultado esperado**:
   - ✅ El tema debe cambiar inmediatamente
   - ✅ La preferencia debe guardarse por usuario
   - ✅ Al recargar la página, debe mantener el tema seleccionado

### Prueba 19: Responsiveness (diseño móvil)

1. Abre las herramientas de desarrollador (F12)

2. Activa el modo responsive y selecciona un dispositivo móvil

3. Navega por la aplicación:
   - Dashboard
   - Formulario de fichaje
   - Listado de registros

4. **Resultado esperado**:
   - ✅ La interfaz debe adaptarse correctamente
   - ✅ Los botones deben ser accesibles
   - ✅ No debe haber elementos cortados o superpuestos

---

## Checklist Final

Marca las pruebas completadas:

- [ ] Inicio de sesión del administrador
- [ ] Verificar restricciones del plan LITE
- [ ] Crear empleado nuevo
- [ ] Gestionar centros y categorías
- [ ] Inicio de sesión como empleado
- [ ] Registrar entrada (fichaje)
- [ ] Registrar pausa
- [ ] Registrar salida
- [ ] Solicitar vacaciones
- [ ] Revisar solicitudes de empleados
- [ ] Aprobar/Rechazar solicitudes
- [ ] Ver reportes
- [ ] Exportar datos
- [ ] Aislamiento de clientes
- [ ] Permisos de empleados
- [ ] Validaciones de formularios
- [ ] Registro de auditoría
- [ ] Temas y personalización
- [ ] Responsiveness

---

## Problemas Comunes

### Error: "No se puede conectar a la base de datos"

- Verifica que el archivo `.env` existe y tiene las credenciales correctas
- Verifica que la base de datos en Supabase está activa

### Error: "Cliente no encontrado"

- Ejecuta: `python create_patacones_client.py`
- Verifica en Supabase que el cliente existe con slug `patacones-de-mi-tierra`

### Error: "Has alcanzado el límite de empleados"

- Es correcto. Plan LITE permite máximo 5 empleados (incluyendo el admin)
- Si necesitas más, debes cambiar el plan a PRO

### Los fichajes no se registran

- Verifica que el empleado tiene un `center_id` asignado
- Verifica que el empleado está activo (`is_active = true`)

---

## Siguiente Paso: Producción

Una vez completadas todas las pruebas:

1. Cambia las contraseñas predeterminadas
2. Actualiza el `SECRET_KEY` en el archivo `.env`
3. Configura las variables de entorno de correo si usarás notificaciones
4. Despliega la aplicación en el servidor de producción

---

¡Felicidades! Has completado la configuración y prueba del cliente "Patacones de mi tierra".
