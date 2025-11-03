# 📎 Sistema de Adjuntos - Documentación Técnica

## ✅ Estado Actual: Backend Completo

### 🎯 Funcionalidades Implementadas

#### 1. **Almacenamiento en Supabase Storage**
- Bucket `justificantes` creado y configurado
- Límite de archivo: 5MB
- Formatos permitidos: PDF, JPG, PNG, JPEG

#### 2. **Base de Datos**
Campos añadidos a las tablas:
- `work_pause`: attachment_url, attachment_filename, attachment_type, attachment_size
- `leave_request`: attachment_url, attachment_filename, attachment_type, attachment_size

#### 3. **Backend - Rutas API**

**Ruta: `/time/pause/start`**
- ✅ Acepta FormData con archivo adjunto
- ✅ Valida tipo MIME y tamaño
- ✅ Sube a Supabase Storage (`pausas/user_{id}/`)
- ✅ Guarda URL en base de datos
- ✅ Compatible con JSON (sin archivo) y FormData (con archivo)

**Ruta: `/time/requests/new`**
- ✅ Acepta FormData con archivo adjunto
- ✅ Auto-aprobación para bajas médicas y ausencias
- ✅ Sube a Supabase Storage (`solicitudes/user_{id}/`)
- ✅ Guarda URL en base de datos

#### 4. **Validaciones de Seguridad**
- ✅ Verificación de tipo MIME real (no solo extensión)
- ✅ Límite de tamaño: 5MB
- ✅ Nombres de archivo sanitizados
- ✅ Solo usuarios autenticados pueden subir
- ✅ Almacenamiento por usuario aislado

---

## 📋 Pendiente: Frontend

### 🔨 Trabajo Restante

#### 1. **Modales del Empleado**

**Modal de Pausas** (`employee_dashboard.html`):
```html
<!-- Añadir input de archivo -->
<input type="file"
       id="pauseAttachment"
       accept=".pdf,.jpg,.jpeg,.png"
       class="hidden">
<label for="pauseAttachment">
  📎 Adjuntar justificante (opcional)
</label>
```

**Modal de Solicitudes**:
- Añadir input de archivo
- Mostrar vista previa del archivo seleccionado
- Enviar FormData en lugar de JSON

#### 2. **Visualización en Admin**

**Tabla de Pausas** (`admin_work_pauses.html`):
- Columna "Justificante" con icono 📎
- Click abre modal con PDF/imagen
- Botón de descarga

**Tabla de Solicitudes** (`admin_leave_requests.html`):
- Columna "Justificante" con icono 📎
- Modal de visualización
- Botón de descarga

**Notificaciones**:
- Mostrar icono 📎 si hay adjunto
- Link directo al archivo

#### 3. **Histórico del Usuario**
- Nueva sección "Justificantes" en perfil
- Lista de todos los archivos del usuario
- Filtros por tipo y fecha

---

## 🔧 Archivos Creados/Modificados

### ✅ Completados:
1. `/migrations/add_attachment_fields.sql` - SQL para Supabase
2. `/config/supabase_config.py` - Configuración de Storage
3. `/utils/file_utils.py` - Utilidades de archivos
4. `/models/models.py` - Modelos actualizados
5. `/routes/time.py` - Rutas con soporte de archivos
6. `.env` - Variables de entorno (SUPABASE_KEY añadida)
7. `requirements.txt` - Dependencias actualizadas

### ⏳ Pendientes:
8. `/src/templates/employee_dashboard.html` - Añadir input de archivo
9. `/src/templates/admin_work_pauses.html` - Visualización
10. `/src/templates/admin_leave_requests.html` - Visualización
11. `/src/templates/admin_dashboard.html` - Icono en notificaciones

---

## 📊 Diagrama de Flujo

```
┌─────────────────────────────────────────────────────────┐
│  EMPLEADO                                               │
│  ┌──────────────────┐                                   │
│  │ Click "Descanso" │                                   │
│  │ → Asuntos médicos│                                   │
│  └────────┬─────────┘                                   │
│           │                                             │
│           ▼                                             │
│  ┌──────────────────┐                                   │
│  │ Modal con input  │                                   │
│  │ de archivo       │                                   │
│  └────────┬─────────┘                                   │
│           │                                             │
│           ▼                                             │
│  ┌──────────────────┐                                   │
│  │ Selecciona PDF/  │                                   │
│  │ foto             │                                   │
│  └────────┬─────────┘                                   │
│           │                                             │
│           ▼                                             │
│  ┌──────────────────┐                                   │
│  │ Envía FormData   │─────┐                            │
│  └──────────────────┘     │                            │
└───────────────────────────┼────────────────────────────┘
                            │
                            │ POST /time/pause/start
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│  BACKEND (Flask)                                        │
│  ┌──────────────────┐                                   │
│  │ Valida archivo   │                                   │
│  │ - Tamaño < 5MB   │                                   │
│  │ - Tipo MIME      │                                   │
│  └────────┬─────────┘                                   │
│           │                                             │
│           ▼                                             │
│  ┌──────────────────┐                                   │
│  │ Sube a Supabase  │                                   │
│  │ Storage          │                                   │
│  └────────┬─────────┘                                   │
│           │                                             │
│           ▼                                             │
│  ┌──────────────────┐                                   │
│  │ Guarda URL en    │                                   │
│  │ work_pause       │                                   │
│  └──────────────────┘                                   │
└─────────────────────────────────────────────────────────┘
                            │
                            │ URL guardada
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│  ADMIN                                                  │
│  ┌──────────────────┐                                   │
│  │ Ve tabla pausas  │                                   │
│  │ con icono 📎     │                                   │
│  └────────┬─────────┘                                   │
│           │                                             │
│           ▼                                             │
│  ┌──────────────────┐                                   │
│  │ Click en icono   │                                   │
│  └────────┬─────────┘                                   │
│           │                                             │
│           ▼                                             │
│  ┌──────────────────┐                                   │
│  │ Modal con PDF/   │                                   │
│  │ imagen           │                                   │
│  └──────────────────┘                                   │
└─────────────────────────────────────────────────────────┘
```

---

## 🚀 Próximos Pasos (Frontend)

1. **Modificar modal de pausas** - Añadir input de archivo
2. **Modificar modal de solicitudes** - Añadir input de archivo
3. **Actualizar JavaScript** - Enviar FormData en lugar de JSON
4. **Añadir visualización en admin** - Iconos y modales
5. **Testing completo** - Probar upload, visualización, descarga

---

## 🔒 Seguridad

- ✅ Archivos aislados por usuario
- ✅ Validación de tipo MIME real
- ✅ Límite de tamaño
- ✅ Bucket privado (requiere autenticación)
- ✅ Service Role Key en .env (no expuesta al cliente)
- ✅ Nombres sanitizados con timestamp

---

## 📝 Notas Importantes

1. **Supabase Key**: Nunca exponer el `SUPABASE_KEY` (Service Role) en el frontend
2. **Bucket**: El bucket "justificantes" debe estar en modo privado
3. **URLs**: Las URLs generadas son públicas pero del bucket privado
4. **Migración a Render**: Todo funcionará igual, solo cambiar `DATABASE_URL`

---

## ✨ Características Extra Opcionales

- [ ] Comprimir imágenes antes de subir
- [ ] Previsualización de PDF en modal
- [ ] Drag & drop para archivos
- [ ] Múltiples archivos por pausa/solicitud
- [ ] Historial de archivos por usuario
- [ ] Estadísticas de uso de almacenamiento

---

**Fecha**: 2025-11-03
**Estado**: Backend Completo ✅ | Frontend Pendiente ⏳
