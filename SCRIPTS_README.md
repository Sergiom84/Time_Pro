# Scripts de Gestión - Time Pro

## Scripts para Creación de Clientes y Empleados

### 📋 Crear Nuevo Cliente

```bash
python create_client.py
```

**Qué hace:**
- Crea un nuevo cliente (empresa)
- Crea el centro inicial
- Crea el usuario administrador con rol `super_admin`

**Datos que solicita:**
- Nombre de la empresa
- Plan (lite/pro)
- Nombre del centro inicial
- Username del administrador
- Contraseña del administrador

**NO solicita:**
- Logo (se puede agregar después desde la UI)
- Colores personalizados (usa defaults: #0ea5e9, #06b6d4)

---

### 👤 Crear Empleado Individual

```bash
python add_employee.py
```

**Qué hace:**
- Permite crear empleados uno por uno de forma interactiva
- Selecciona cliente existente
- Valida límites de plan (Lite: máx 5 empleados)
- Asigna centro y categoría

**Datos que solicita:**
- Username
- Contraseña
- Nombre completo
- Email
- Horas semanales
- Centro (si existen)
- Categoría (si existen)

---

### 📊 Importar Empleados Masivamente (CSV/Excel)

```bash
python import_employees_csv.py
```

**Qué hace:**
- Importa múltiples empleados desde archivo CSV o Excel
- Valida todos los datos antes de importar
- Importación atómica (todo o nada)

**Formato CSV:**
```csv
username,password,full_name,email,weekly_hours,center_name,category_name
juan.perez,pass123,Juan Pérez,juan@ejemplo.com,40,Centro 1,Empleado
```

**Ver archivo de ejemplo:** `examples/empleados_ejemplo.csv`

**Soporte Excel:**
Para usar archivos Excel (.xlsx, .xls):
```bash
pip install pandas openpyxl
```

---

## Scripts Utilitarios

### 🔍 Inspeccionar Clientes

```bash
python check_clients.py
```

Muestra todos los clientes con estadísticas:
- Número de usuarios (admins y empleados)
- Número de centros
- Número de categorías

### 🔐 Generar Hash de Contraseña

```bash
python generate_password_hash.py
```

Genera un hash de contraseña para inserciones manuales en la BD.

---

## Scripts de Administración (Uso Ocasional)

### Configurar Categorías

```bash
python direct_setup_categories.py
```

Crea categorías por defecto para un cliente:
- Coordinador
- Empleado
- Gestor

### Configurar Centros

```bash
python direct_setup_centers.py
```

Migra datos de centros legacy o crea centros iniciales.

### Verificar Centros

```bash
python verify_and_setup_centers.py
```

Verifica estructura de la tabla `center` y agrega centros faltantes.

---

## Diferencias entre Planes

### Plan LITE
- ✅ Máximo 5 empleados
- ✅ 1 solo centro
- ✅ Reportes básicos
- ✅ Fichajes y pausas
- ✅ Solicitudes de permisos

### Plan PRO
- ✅ Empleados ilimitados
- ✅ Centros ilimitados
- ✅ Reportes avanzados
- ✅ Todas las funcionalidades

---

## Flujo Típico para Nuevo Cliente

1. **Crear cliente y admin:**
   ```bash
   python create_client.py
   ```

2. **Crear categorías (opcional):**
   ```bash
   python direct_setup_categories.py
   ```

3. **Agregar empleados:**

   **Opción A - Uno por uno:**
   ```bash
   python add_employee.py
   ```

   **Opción B - Importación masiva:**
   ```bash
   python import_employees_csv.py
   ```

4. **Verificar creación:**
   ```bash
   python check_clients.py
   ```

---

## Archivos de Ejemplo

En la carpeta `examples/`:
- `empleados_ejemplo.csv` - Ejemplo de CSV para importación masiva
- `README.md` - Documentación detallada del formato CSV

---

## Notas Importantes

- ✅ Los scripts usan transacciones seguras (rollback en caso de error)
- ✅ Validación de unicidad (username y email por cliente)
- ✅ Contraseñas hasheadas automáticamente con Werkzeug
- ✅ Aislamiento multi-tenant (cada cliente ve solo sus datos)
- ❌ NO ejecutar scripts de migración ya aplicados
- ❌ NO modificar manualmente la BD (usar scripts o UI)
