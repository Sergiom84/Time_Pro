/**
 * Builder.io Integration - Main Export
 *
 * Punto de entrada principal para la integración de Builder.io
 */

export { builderConfig } from './config';
export { registerBuilderComponents } from './builderInit';
export { BuilderModal } from './components/BuilderModal';
export { CustomModal } from './components/CustomModal';
export { ModalManager } from './components/ModalManager';

// Re-export útiles de @builder.io/react
export { BuilderComponent, builder } from '@builder.io/react';
