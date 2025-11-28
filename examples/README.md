# Ejemplos - Time Pro

## Importación de Empleados desde CSV

### Archivo de Ejemplo: `empleados_ejemplo.csv`

Este archivo muestra el formato correcto para importar empleados masivamente.

### Formato del CSV

```csv
username,password,full_name,email,weekly_hours,center_name,category_name
juan.perez,pass123,Juan Pérez,juan.perez@ejemplo.com,40,Centro 1,Empleado
maria.gomez,pass456,María Gómez,maria.gomez@ejemplo.com,30,Centro 1,Coordinador
```

### Columnas

| Columna | Obligatoria | Descripción |
|---------|-------------|-------------|
| `username` | ✅ Sí | Nombre de usuario único dentro del cliente |
| `password` | ✅ Sí | Contraseña en texto plano (se hasheará automáticamente) |
| `full_name` | ✅ Sí | Nombre completo del empleado |
| `email` | ✅ Sí | Email único dentro del cliente |
| `weekly_hours` | ❌ No | Horas de trabajo semanales (default: 40) |
| `center_name` | ❌ No | Nombre del centro (debe existir en la BD) |
| `category_name` | ❌ No | Nombre de la categoría (debe existir en la BD) |

### Cómo Usar

1. **Preparar tu archivo CSV**
   - Copia `empleados_ejemplo.csv` y renómbralo
   - Edita el archivo con los datos de tus empleados
   - Asegúrate de que los centros y categorías existan en tu cliente

2. **Ejecutar el script de importación**
   ```bash
   python import_employees_csv.py
   ```

3. **Seguir las instrucciones**
   - Selecciona el cliente
   - Proporciona la ruta al archivo CSV
   - Revisa el preview
   - Confirma la importación

### Validaciones

El script validará automáticamente:
- ✅ Límites de plan (Lite: máx 5 empleados)
- ✅ Campos obligatorios presentes
- ✅ Username único (dentro del cliente)
- ✅ Email único (dentro del cliente)
- ✅ Centro existe (si se especifica)
- ✅ Categoría existe (si se especifica)

Si hay errores, se mostrarán todos y la importación se cancelará sin modificar la base de datos.

### Soporte Excel

El script también acepta archivos Excel (.xlsx, .xls).

**Requisito**: Instalar pandas y openpyxl

```bash
pip install pandas openpyxl
```

Luego puedes usar directamente archivos Excel con el mismo formato de columnas.
