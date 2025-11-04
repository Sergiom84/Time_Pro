# Builder.io Integration for Time Pro

Esta carpeta contiene la integración completa de Builder.io para gestionar y mejorar modales y ventanas en la aplicación Time Pro.

## 📋 Contenido

### Archivos principales

- **config.js**: Configuración central de Builder.io (API key, modelos, temas)
- **builderInit.jsx**: Inicialización y registro de componentes personalizados
- **index.js**: Exportaciones principales del módulo

### Componentes

- **BuilderModal.jsx**: Modal que carga contenido dinámico desde Builder.io
- **CustomModal.jsx**: Modal personalizado compatible con el sistema de temas
- **ModalManager.jsx**: Gestor global de modales accesible desde JavaScript vanilla

## 🚀 Configuración Inicial

### 1. Obtener API Key de Builder.io

1. Ve a [builder.io](https://builder.io) y crea una cuenta
2. Navega a **Settings > API Keys**
3. Copia tu **Public API Key**
4. Crea un archivo `.env` en la raíz del proyecto:

```bash
cp .env.example .env
```

5. Edita `.env` y añade tu API key:

```env
VITE_BUILDER_IO_API_KEY=tu-api-key-aqui
```

### 2. Crear modelos en Builder.io

Ve a tu dashboard de Builder.io y crea los siguientes modelos:

#### Modelo: `modal`
- **Name**: Modal
- **Type**: Page
- **URL Pattern**: /modals/*

Este modelo se usará para crear contenido de modales editable visualmente.

#### Modelo: `notification`
- **Name**: Notification
- **Type**: Data
- Campos personalizados según necesites

## 📖 Uso

### Opción 1: Usar desde React

```jsx
import { CustomModal, BuilderModal } from '@/builder';

function MyComponent() {
  const [showModal, setShowModal] = useState(false);

  return (
    <>
      <button onClick={() => setShowModal(true)}>
        Abrir Modal
      </button>

      {/* Modal personalizado con contenido estático */}
      <CustomModal
        isOpen={showModal}
        onClose={() => setShowModal(false)}
        title="Mi Modal"
        subtitle="Descripción del modal"
        size="default"
      >
        <p>Contenido del modal aquí</p>
      </CustomModal>

      {/* Modal con contenido de Builder.io */}
      <BuilderModal
        isOpen={showModal}
        onClose={() => setShowModal(false)}
        modelName="modal"
        contentUrl="/modals/mi-modal"
      />
    </>
  );
}
```

### Opción 2: Usar desde JavaScript Vanilla (Templates Jinja2)

El `ModalManager` está disponible globalmente a través de `window.BuilderModalManager`:

```javascript
// Abrir un modal personalizado
const modalId = window.BuilderModalManager.open({
  type: 'custom',
  title: 'Título del Modal',
  subtitle: 'Subtítulo opcional',
  size: 'default', // 'small', 'default', 'large', 'full'
  showCloseButton: true,
  content: '<div>Contenido HTML aquí</div>',
  className: 'mi-clase-custom',
});

// Abrir un modal con contenido de Builder.io
const builderId = window.BuilderModalManager.open({
  type: 'builder',
  modelName: 'modal',
  entryId: 'abc123', // O usa contentUrl
  contentUrl: '/modals/mi-modal',
  fallbackContent: '<p>Contenido alternativo si falla</p>',
});

// Cerrar un modal específico
window.BuilderModalManager.close(modalId);

// Cerrar todos los modales
window.BuilderModalManager.closeAll();
```

### Ejemplo en Template Jinja2

```html
<!-- En tu template Jinja2 -->
<script>
  function abrirModalPersonalizado() {
    if (window.BuilderModalManager) {
      window.BuilderModalManager.open({
        type: 'custom',
        title: 'Nueva Solicitud',
        subtitle: 'Completa el formulario',
        size: 'large',
        content: document.getElementById('mi-formulario').innerHTML,
      });
    } else {
      console.error('BuilderModalManager no está disponible');
    }
  }

  function abrirModalBuilder() {
    if (window.BuilderModalManager) {
      window.BuilderModalManager.open({
        type: 'builder',
        modelName: 'modal',
        contentUrl: '/modals/solicitud-vacaciones',
      });
    }
  }
</script>

<button onclick="abrirModalPersonalizado()">
  Abrir Modal Personalizado
</button>

<button onclick="abrirModalBuilder()">
  Abrir Modal de Builder.io
</button>

<!-- Contenido que se mostrará en el modal -->
<div id="mi-formulario" style="display: none;">
  <form>
    <!-- Tu formulario aquí -->
  </form>
</div>
```

## 🎨 Componentes Personalizados Registrados

Los siguientes componentes están disponibles en el Visual Editor de Builder.io:

### 1. Modal Header
- **title**: Título del modal
- **subtitle**: Subtítulo opcional
- **showCloseButton**: Mostrar botón de cerrar

### 2. Form Field
- **label**: Etiqueta del campo
- **type**: text, email, password, number, date, textarea
- **placeholder**: Texto placeholder
- **required**: Campo requerido
- **name**: Nombre del campo

### 3. Action Button
- **text**: Texto del botón
- **variant**: primary, secondary, danger, success
- **fullWidth**: Ocupar todo el ancho
- **action**: submit, button, reset

## 🎨 Sistema de Temas

La integración respeta el sistema de temas existente usando CSS Variables:

```javascript
// Los temas se sincronizan automáticamente
- var(--accent-primary)
- var(--bg-card)
- var(--bg-secondary)
- var(--text-primary)
- var(--text-secondary)
- var(--border-color)
```

## 🔧 Personalización

### Añadir nuevos componentes personalizados

Edita `builderInit.jsx` y registra componentes adicionales:

```jsx
builder.registerComponent(
  {
    name: 'Mi Componente',
    inputs: [
      {
        name: 'miProp',
        type: 'string',
        defaultValue: 'Valor por defecto',
      },
    ],
  },
  (props) => {
    return <div>{props.miProp}</div>;
  }
);
```

### Modificar estilos de modales

Los modales usan las variables CSS del tema actual. Puedes personalizar editando:
- `CustomModal.jsx` para cambiar la estructura
- `BuilderModal.jsx` para cambiar el comportamiento de carga

## 📚 Recursos

- [Builder.io Documentation](https://www.builder.io/c/docs/developers)
- [React SDK](https://github.com/BuilderIO/builder/tree/main/packages/react)
- [Visual Editor](https://www.builder.io/c/docs/editing-basics)

## 🐛 Troubleshooting

### El ModalManager no está disponible

Asegúrate de que:
1. El script de React se ha cargado correctamente
2. `main.jsx` incluye la inicialización del ModalManager
3. El DOM se ha cargado completamente antes de usar `window.BuilderModalManager`

### Los modales no se ven correctamente

Verifica que:
1. Las variables CSS del tema están cargadas
2. TailwindCSS está compilado correctamente
3. No hay conflictos de z-index con otros elementos

### No se carga el contenido de Builder.io

Comprueba:
1. Que la API key está configurada correctamente en `.env`
2. Que el modelo existe en Builder.io
3. Que el contenido está publicado (no en draft)
4. La consola del navegador para errores de red

## 📝 Notas

- El ModalManager se monta automáticamente al cargar la aplicación
- Los modales se integran perfectamente con el sistema de temas existente
- Puedes combinar modales personalizados con contenido de Builder.io
- El sistema es compatible con la arquitectura Flask + Jinja2 + React existente
