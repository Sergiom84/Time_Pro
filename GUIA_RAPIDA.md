# Guía Rápida - Time Pro (WSL/Linux)

## ✅ Pre-requisitos
- Terminal WSL abierta
- Python 3 instalado
- Entorno virtual activado: `source venv/bin/activate`

---

## 🚀 Uso Simple

### Iniciar Versión Lite:
```bash
bash run_lite.sh
```

### Iniciar Versión Pro:
```bash
bash run_pro.sh
```

### Detener todas las instancias:
```bash
bash stop_app.sh
```

### Ver estado:
```bash
bash check_status.sh
```

---

## 📋 Flujo Completo

```bash
# 1. Ir al directorio
cd /mnt/c/Users/Sergio/Desktop/Time_Pro

# 2. Activar entorno virtual (si no está activado)
source venv/bin/activate

# 3. Ver estado
bash check_status.sh

# 4. Detener instancias previas (si hay)
bash stop_app.sh

# 5. Iniciar Lite
bash run_lite.sh
```

**Resultado esperado:**
```
🛑 Deteniendo instancias anteriores...
✅ Instancias detenidas
🚀 Iniciando Time Pro LITE...
✓ Time Pro iniciado con plan: LITE
  - Límite de empleados: 5
  - Múltiples centros: No
Usando BD: postgresql://...
```

---

## 🔧 Cambiar de versión

**Desde Lite a Pro:**
1. Presiona `Ctrl+C` en la terminal donde corre Lite
2. Ejecuta: `bash run_pro.sh`

**Desde Pro a Lite:**
1. Presiona `Ctrl+C` en la terminal donde corre Pro
2. Ejecuta: `bash run_lite.sh`

---

## 📝 Comandos Manuales (sin scripts)

### Versión Pro:
```bash
export APP_PLAN=pro
python3 main.py
```

### Versión Lite:
```bash
export APP_PLAN=lite
python3 main.py
```

### Detener (Ctrl+C no funciona):
```bash
pkill -9 -f "python.*main.py"
```

---

## 🌐 Acceder a la App

Una vez iniciada:
- Abre el navegador
- Ve a: `http://localhost:5000`

---

## 🐛 Problemas Comunes

### Error: "SSL connection closed"
**Causa:** Múltiples instancias corriendo
**Solución:**
```bash
bash stop_app.sh
sleep 3
bash run_lite.sh
```

### Error: "Port 5000 already in use"
**Causa:** Ya hay una instancia corriendo
**Solución:**
```bash
bash stop_app.sh
```

### Error: "ModuleNotFoundError: No module named 'flask'"
**Causa:** Entorno virtual no activado
**Solución:**
```bash
source venv/bin/activate
```

### Error: "Permission denied"
**Causa:** Scripts sin permisos de ejecución
**Solución:**
```bash
chmod +x run_lite.sh run_pro.sh stop_app.sh check_status.sh
```

---

## ✅ Verificar que todo funciona

```bash
# Test rápido
python3 -c "import plan_config; print('✅ OK')"

# Ver configuración
python3 -c "import plan_config; print(f'Plan: {plan_config.get_plan()}')"

# Test completo
python3 test_plan_system.py
```

---

## 📁 Archivos Importantes

- `run_lite.sh` → Iniciar Lite
- `run_pro.sh` → Iniciar Pro
- `stop_app.sh` → Detener todo
- `check_status.sh` → Ver estado
- `plan_config.py` → Configuración de planes
- `test_plan_system.py` → Tests automatizados

---

## 🎯 Desde VS Code Terminal

En VS Code, abre una terminal WSL:
1. `Ctrl+Shift+`` (backtick) para abrir terminal
2. Selecciona "Ubuntu" o "WSL" en el dropdown
3. Ejecuta los comandos bash normalmente

---

## 🔄 Workflow Recomendado

```bash
# Abrir VS Code en el proyecto
cd /mnt/c/Users/Sergio/Desktop/Time_Pro
code .

# En la terminal integrada de VS Code (WSL):
source venv/bin/activate
bash check_status.sh
bash run_lite.sh

# Para detener: Ctrl+C
# Para cambiar: bash run_pro.sh
```

---

¡Listo! Usa `bash run_lite.sh` para empezar.
