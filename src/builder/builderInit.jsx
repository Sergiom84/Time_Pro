/**
 * Builder.io Initialization
 *
 * Este archivo inicializa Builder.io y registra componentes personalizados
 */

import { builder } from '@builder.io/react';
import { builderConfig } from './config';

// Inicializar Builder.io con tu API key
builder.init(builderConfig.apiKey);

// Registrar componentes personalizados para usar en el Visual Editor
export function registerBuilderComponents() {
  // Aquí puedes registrar componentes personalizados que quieres
  // que estén disponibles en el Builder.io Visual Editor

  // Ejemplo: Registrar un componente de botón personalizado
  builder.registerComponent(
    {
      name: 'Modal Header',
      inputs: [
        {
          name: 'title',
          type: 'string',
          defaultValue: 'Modal Title',
        },
        {
          name: 'subtitle',
          type: 'string',
        },
        {
          name: 'showCloseButton',
          type: 'boolean',
          defaultValue: true,
        },
      ],
    },
    (props) => {
      return (
        <div className="flex justify-between items-start mb-6">
          <div>
            <h2
              className="text-2xl font-bold mb-2"
              style={{ color: 'var(--text-primary)' }}
            >
              {props.title}
            </h2>
            {props.subtitle && (
              <p
                className="text-sm"
                style={{ color: 'var(--text-secondary)' }}
              >
                {props.subtitle}
              </p>
            )}
          </div>
          {props.showCloseButton && (
            <button
              onClick={props.onClose}
              className="text-2xl font-light hover:opacity-70 transition-opacity"
              style={{ color: 'var(--text-secondary)' }}
            >
              ×
            </button>
          )}
        </div>
      );
    }
  );

  builder.registerComponent(
    {
      name: 'Form Field',
      inputs: [
        {
          name: 'label',
          type: 'string',
          defaultValue: 'Field Label',
        },
        {
          name: 'type',
          type: 'string',
          enum: ['text', 'email', 'password', 'number', 'date', 'textarea'],
          defaultValue: 'text',
        },
        {
          name: 'placeholder',
          type: 'string',
        },
        {
          name: 'required',
          type: 'boolean',
          defaultValue: false,
        },
        {
          name: 'name',
          type: 'string',
          required: true,
        },
      ],
    },
    (props) => {
      const InputComponent = props.type === 'textarea' ? 'textarea' : 'input';

      return (
        <div className="mb-4">
          <label
            className="block text-sm font-semibold mb-2"
            style={{ color: 'var(--text-primary)' }}
          >
            {props.label}
            {props.required && <span className="text-red-500 ml-1">*</span>}
          </label>
          <InputComponent
            type={props.type !== 'textarea' ? props.type : undefined}
            name={props.name}
            placeholder={props.placeholder}
            required={props.required}
            className="w-full px-4 py-3 rounded-xl border-2 focus:outline-none focus:ring-2 transition-all"
            style={{
              backgroundColor: 'var(--bg-secondary)',
              borderColor: 'var(--border-color)',
              color: 'var(--text-primary)',
            }}
          />
        </div>
      );
    }
  );

  builder.registerComponent(
    {
      name: 'Action Button',
      inputs: [
        {
          name: 'text',
          type: 'string',
          defaultValue: 'Click me',
        },
        {
          name: 'variant',
          type: 'string',
          enum: ['primary', 'secondary', 'danger', 'success'],
          defaultValue: 'primary',
        },
        {
          name: 'fullWidth',
          type: 'boolean',
          defaultValue: false,
        },
        {
          name: 'action',
          type: 'string',
          enum: ['submit', 'button', 'reset'],
          defaultValue: 'button',
        },
      ],
    },
    (props) => {
      const getButtonStyles = () => {
        const base = 'px-6 py-3 rounded-xl font-semibold transition-all transform hover:scale-105 active:scale-95';

        const variants = {
          primary: 'text-white shadow-lg',
          secondary: 'border-2',
          danger: 'bg-red-500 text-white hover:bg-red-600',
          success: 'bg-green-500 text-white hover:bg-green-600',
        };

        const width = props.fullWidth ? 'w-full' : '';

        return `${base} ${variants[props.variant] || variants.primary} ${width}`;
      };

      const getInlineStyles = () => {
        if (props.variant === 'primary') {
          return {
            background: 'linear-gradient(135deg, var(--accent-primary) 0%, var(--accent-secondary, var(--accent-primary)) 100%)',
          };
        }
        if (props.variant === 'secondary') {
          return {
            borderColor: 'var(--accent-primary)',
            color: 'var(--accent-primary)',
          };
        }
        return {};
      };

      return (
        <button
          type={props.action}
          className={getButtonStyles()}
          style={getInlineStyles()}
          onClick={props.onClick}
        >
          {props.text}
        </button>
      );
    }
  );

  console.log('✅ Builder.io components registered successfully');
}

export default registerBuilderComponents;
