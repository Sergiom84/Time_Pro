import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App.jsx';
import './index.css';
import { registerBuilderComponents } from './builder/builderInit';
import { ModalManager } from './builder/components/ModalManager';

// Inicializar componentes de Builder.io
registerBuilderComponents();

// Renderizar la aplicación principal
ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);

// Montar el ModalManager en un elemento separado para uso global
const modalRoot = document.createElement('div');
modalRoot.id = 'builder-modal-root';
document.body.appendChild(modalRoot);

ReactDOM.createRoot(modalRoot).render(
  <React.StrictMode>
    <ModalManager />
  </React.StrictMode>
);