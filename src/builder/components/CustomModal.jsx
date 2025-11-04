/**
 * CustomModal Component
 *
 * Modal personalizado que puede mostrar contenido estático o de Builder.io
 * Compatible con el sistema de temas existente
 */

import React from 'react';
import { BuilderComponent } from '@builder.io/react';

export function CustomModal({
  isOpen,
  onClose,
  title,
  subtitle,
  children,
  builderContent = null,
  showCloseButton = true,
  size = 'default', // 'small', 'default', 'large', 'full'
  className = '',
}) {
  if (!isOpen) return null;

  const sizeClasses = {
    small: 'max-w-md',
    default: 'max-w-2xl',
    large: 'max-w-4xl',
    full: 'max-w-6xl',
  };

  return (
    <div
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
      onClick={onClose}
    >
      <div
        className={`rounded-2xl p-8 ${sizeClasses[size] || sizeClasses.default} w-full max-h-[90vh] overflow-y-auto ${className}`}
        style={{
          backgroundColor: 'var(--bg-card)',
          border: '2px solid var(--border-color)',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        {(title || showCloseButton) && (
          <div className="flex justify-between items-start mb-6">
            <div>
              {title && (
                <h2
                  className="text-2xl font-bold mb-2"
                  style={{ color: 'var(--text-primary)' }}
                >
                  {title}
                </h2>
              )}
              {subtitle && (
                <p
                  className="text-sm"
                  style={{ color: 'var(--text-secondary)' }}
                >
                  {subtitle}
                </p>
              )}
            </div>
            {showCloseButton && (
              <button
                onClick={onClose}
                className="text-2xl font-light hover:opacity-70 transition-opacity ml-4"
                style={{ color: 'var(--text-secondary)' }}
              >
                ×
              </button>
            )}
          </div>
        )}

        {/* Content */}
        <div>
          {builderContent ? (
            <BuilderComponent
              model={builderContent.model || 'modal'}
              content={builderContent}
              context={{ onClose }}
            />
          ) : (
            children
          )}
        </div>
      </div>
    </div>
  );
}

export default CustomModal;
