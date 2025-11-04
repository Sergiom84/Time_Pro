/**
 * ModalManager Component
 *
 * Gestor de modales que puede ser montado en el DOM desde templates Jinja2
 * Permite controlar modales desde JavaScript vanilla
 */

import React, { useState, useEffect } from 'react';
import { CustomModal } from './CustomModal';
import { BuilderModal } from './BuilderModal';

// Instancia global para controlar el ModalManager desde fuera de React
let modalManagerInstance = null;

export function ModalManager() {
  const [modals, setModals] = useState([]);

  useEffect(() => {
    // Registrar la instancia globalmente
    modalManagerInstance = {
      open: (modalConfig) => {
        const id = `modal-${Date.now()}-${Math.random()}`;
        setModals(prev => [...prev, { ...modalConfig, id, isOpen: true }]);
        return id;
      },
      close: (id) => {
        setModals(prev => prev.filter(modal => modal.id !== id));
      },
      closeAll: () => {
        setModals([]);
      },
    };

    // Exponer en window para acceso desde JavaScript vanilla
    window.BuilderModalManager = modalManagerInstance;

    return () => {
      window.BuilderModalManager = null;
      modalManagerInstance = null;
    };
  }, []);

  const handleClose = (id) => {
    setModals(prev => prev.filter(modal => modal.id !== id));
  };

  return (
    <>
      {modals.map((modal) => {
        if (modal.type === 'builder') {
          return (
            <BuilderModal
              key={modal.id}
              isOpen={modal.isOpen}
              onClose={() => handleClose(modal.id)}
              modelName={modal.modelName}
              entryId={modal.entryId}
              contentUrl={modal.contentUrl}
              fallbackContent={modal.fallbackContent}
              className={modal.className}
              style={modal.style}
            />
          );
        }

        return (
          <CustomModal
            key={modal.id}
            isOpen={modal.isOpen}
            onClose={() => handleClose(modal.id)}
            title={modal.title}
            subtitle={modal.subtitle}
            size={modal.size}
            showCloseButton={modal.showCloseButton}
            className={modal.className}
          >
            {modal.content}
          </CustomModal>
        );
      })}
    </>
  );
}

export default ModalManager;
