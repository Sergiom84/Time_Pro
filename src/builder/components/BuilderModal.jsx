/**
 * BuilderModal Component
 *
 * Componente de modal que integra Builder.io para contenido editable
 * Puede ser usado para reemplazar o mejorar los modales existentes
 */

import React, { useEffect, useState } from 'react';
import { BuilderComponent, builder } from '@builder.io/react';
import { builderConfig } from '../config';

export function BuilderModal({
  isOpen,
  onClose,
  modelName = 'modal',
  entryId = null,
  contentUrl = null,
  fallbackContent = null,
  className = '',
  style = {},
}) {
  const [content, setContent] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!isOpen) return;

    async function fetchContent() {
      try {
        setLoading(true);
        setError(null);

        // Construir la consulta basada en los parámetros
        let query = { model: modelName };

        if (entryId) {
          query.id = entryId;
        } else if (contentUrl) {
          query.url = contentUrl;
        }

        const builderContent = await builder.get(modelName, query).promise();

        if (builderContent) {
          setContent(builderContent);
        } else {
          setError('No se encontró contenido en Builder.io');
        }
      } catch (err) {
        console.error('Error loading Builder.io content:', err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }

    fetchContent();
  }, [isOpen, modelName, entryId, contentUrl]);

  if (!isOpen) return null;

  return (
    <div
      className={`fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4 ${className}`}
      onClick={onClose}
      style={style}
    >
      <div
        className="rounded-2xl p-8 max-w-2xl w-full max-h-[90vh] overflow-y-auto"
        style={{
          backgroundColor: 'var(--bg-card)',
          border: '2px solid var(--border-color)',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {loading && (
          <div className="text-center py-8">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-4 border-solid border-current border-r-transparent" style={{ color: 'var(--accent-primary)' }}></div>
            <p className="mt-4" style={{ color: 'var(--text-secondary)' }}>Cargando contenido...</p>
          </div>
        )}

        {error && (
          <div className="text-center py-8">
            <p className="text-red-500 mb-4">Error: {error}</p>
            {fallbackContent && (
              <div>
                <p style={{ color: 'var(--text-secondary)' }} className="mb-4">Mostrando contenido alternativo:</p>
                {fallbackContent}
              </div>
            )}
            <button
              onClick={onClose}
              className="mt-4 px-6 py-2 rounded-lg"
              style={{ backgroundColor: 'var(--accent-primary)', color: 'white' }}
            >
              Cerrar
            </button>
          </div>
        )}

        {!loading && !error && content && (
          <BuilderComponent
            model={modelName}
            content={content}
            context={{ onClose }}
          />
        )}
      </div>
    </div>
  );
}

export default BuilderModal;
