# Cliente: Patacones de mi tierra - Configuración Completa

## 📋 Resumen

Este paquete contiene todos los archivos necesarios para crear y configurar el cliente "Patacones de mi tierra" en modo **LITE** en Time Pro.

---

## 🎯 ¿Qué se ha preparado?

### 1. Scripts de Configuración Automática

- **`create_patacones_client.py`**: Script automatizado que crea todo con un solo comando
- **`add_test_employees.py`**: Añade 4 empleados de prueba al cliente
- **`setup_patacones.sh`**: Script bash para ejecutar todo automáticamente (Linux/WSL)

### 2. Configuración SQL Manual

- **`setup_patacones.sql`**: Archivo SQL con todos los comandos para crear el cliente directamente en Supabase

### 3. Documentación

- **`INSTRUCCIONES_RAPIDAS.txt`**: Guía rápida para empezar (¡EMPIEZA AQUÍ!)
- **`SETUP_PATACONES.md`**: Documentación detallada con 3 métodos de configuración
- **`GUIA_PRUEBAS_PATACONES.md`**: Guía completa de pruebas (19 pruebas de funcionalidad)
- **`README_PATACONES.md`**: Este archivo

### 4. Utilidades

- **`generate_patacones_hash.py`**: Genera hash de contraseña para el administrador
- **`check_clients.py`**: Verifica los clientes existentes en la base de datos
- **`.env`**: Archivo de configuración con credenciales de Supabase (ya creado)

---

## 🚀 Inicio Rápido (3 Pasos)

### Paso 1: Ejecutar el script automatizado

Abre **PowerShell** en Windows y ejecuta:

```powershell
cd C:\Users\sergi\Desktop\Aplicaciones\Time_Pro
python create_patacones_client.py
```

### Paso 2: Añadir empleados de prueba (opcional)

```powershell
python add_test_employees.py
```

### Paso 3: Iniciar la aplicación y probar

```powershell
python main.py
```

Luego abre tu navegador en: `http://localhost:5000`

**Credenciales del administrador:**
- Username: `admin_patacones`
- Password: `Patacones2025!`

---

## 📁 Estructura del Cliente

```
Patacones de mi tierra (LITE)
│
├── Plan: LITE
│   ├── Máximo 5 empleados (incluyendo admin)
│   ├── 1 centro
│   └── Sin selector de centros
│
├── Administrador
│   ├── Username: admin_patacones
│   ├── Password: Patacones2025!
│   ├── Email: admin@pataconesdetierra.com
│   └── Rol: super_admin
│
├── Centro Principal
│   └── Patacones de mi tierra
│
├── Categorías
│   ├── Cocinero
│   ├── Camarero
│   └── Gestor
│
└── Empleados de Prueba (opcional - 4)
    ├── María Gómez (Camarero)
    ├── Carlos Rodríguez (Cocinero)
    ├── Ana Martínez (Camarero)
    └── Juan López (Cocinero)
```

---

## 📊 Características del Plan LITE

### ✅ Incluye:

- Hasta 5 empleados
- 1 centro
- Sistema de fichajes (entrada/salida)
- Registro de pausas
- Solicitudes de permisos (vacaciones, bajas)
- Reportes básicos
- Exportación a Excel
- Vista de calendario
- Notificaciones por email
- Temas personalizables por usuario

### ❌ No incluye:

- Empleados ilimitados
- Múltiples centros
- Selector de centros
- Reportes avanzados

---

## 🔧 Métodos de Instalación

Tienes 3 opciones para crear el cliente:

### Opción 1: Script Automático (⭐ Recomendado)

```bash
python create_patacones_client.py
```

**Ventajas:** Rápido, sin intervención manual
**Requisitos:** Python con Flask instalado

### Opción 2: Script Interactivo

```bash
python scripts/setup_client.py
```

**Ventajas:** Más control sobre los datos
**Requisitos:** Python con Flask instalado

### Opción 3: SQL Manual

1. Genera el hash de contraseña:
   ```bash
   python generate_password_hash.py
   ```

2. Ejecuta el SQL en Supabase siguiendo las instrucciones en `setup_patacones.sql`

**Ventajas:** No requiere Python local
**Requisitos:** Acceso al SQL Editor de Supabase

---

## 📝 Credenciales Predefinidas

### Administrador
```
Username: admin_patacones
Password: Patacones2025!
Email: admin@pataconesdetierra.com
```

### Empleados de Prueba

```
1. María Gómez (Camarero)
   Username: maria_gomez
   Password: Maria2025!
   Email: maria.gomez@pataconesdetierra.com

2. Carlos Rodríguez (Cocinero)
   Username: carlos_rodriguez
   Password: Carlos2025!
   Email: carlos.rodriguez@pataconesdetierra.com

3. Ana Martínez (Camarero)
   Username: ana_martinez
   Password: Ana2025!
   Email: ana.martinez@pataconesdetierra.com

4. Juan López (Cocinero)
   Username: juan_lopez
   Password: Juan2025!
   Email: juan.lopez@pataconesdetierra.com
```

⚠️ **IMPORTANTE:** Cambia estas contraseñas en producción

---

## ✅ Lista de Verificación

Antes de poner en producción:

- [ ] Cliente creado correctamente
- [ ] Administrador puede iniciar sesión
- [ ] Empleados creados (al menos 1)
- [ ] Fichajes funcionan correctamente
- [ ] Pausas se registran
- [ ] Solicitudes de permisos funcionan
- [ ] Reportes se generan correctamente
- [ ] Exportación a Excel funciona
- [ ] Límite de 5 empleados se respeta
- [ ] No aparece selector de centros (es LITE)
- [ ] Todas las contraseñas predeterminadas cambiadas
- [ ] SECRET_KEY actualizado en .env
- [ ] Pruebas completadas (ver GUIA_PRUEBAS_PATACONES.md)

---

## 🐛 Solución de Problemas

### Problema: "No se puede ejecutar Python"

**Solución:**
1. Verifica que Python esté instalado: `python --version`
2. Si no está instalado, descárgalo de: https://www.python.org/downloads/
3. Instala las dependencias: `pip install -r requirements.txt`

### Problema: "Cliente ya existe"

**Solución:**
- El script detectará que el cliente ya existe y solo actualizará datos
- Si quieres recrearlo, elimínalo primero desde Supabase

### Problema: "Error de conexión a la base de datos"

**Solución:**
1. Verifica que el archivo `.env` existe
2. Verifica que las credenciales son correctas
3. Verifica que Supabase está activo

### Problema: "No puedo crear más empleados"

**Solución:**
- El plan LITE permite máximo 5 empleados (incluyendo admin)
- Si necesitas más, actualiza el plan a PRO en la base de datos:
  ```sql
  UPDATE client SET plan = 'pro' WHERE slug = 'patacones-de-mi-tierra';
  ```

---

## 📚 Documentación Adicional

- **INSTRUCCIONES_RAPIDAS.txt**: Empieza aquí para configuración rápida
- **SETUP_PATACONES.md**: Guía detallada de configuración
- **GUIA_PRUEBAS_PATACONES.md**: 19 pruebas para verificar funcionalidad
- **requirements.txt**: Dependencias de Python necesarias

---

## 🎨 Personalización

### Cambiar colores del cliente

Edita en la base de datos:

```sql
UPDATE client
SET
    primary_color = '#TU_COLOR_PRINCIPAL',
    secondary_color = '#TU_COLOR_SECUNDARIO'
WHERE slug = 'patacones-de-mi-tierra';
```

### Añadir logo

1. Sube el logo a Supabase Storage (bucket: `Justificantes/logos/`)
2. Actualiza la URL:

```sql
UPDATE client
SET logo_url = 'https://gqesfclbingbihakiojm.supabase.co/storage/v1/object/public/Justificantes/logos/patacones-de-mi-tierra.png'
WHERE slug = 'patacones-de-mi-tierra';
```

---

## 📞 Soporte

Si encuentras problemas:

1. Revisa la **GUIA_PRUEBAS_PATACONES.md**
2. Verifica los logs de la aplicación
3. Consulta la documentación de Time Pro
4. Contacta al equipo de desarrollo

---

## 📜 Licencia

Este cliente está configurado bajo la misma licencia que Time Pro.

---

## 🙏 Créditos

Cliente configurado para: **Patacones de mi tierra**
Fecha: Noviembre 2025
Plan: LITE
Generado con: Claude Code

---

**¡Listo para empezar!** 🚀

Ejecuta `python create_patacones_client.py` y en menos de 1 minuto tendrás todo configurado.
