/**
 * Builder.io Configuration
 *
 * Este archivo contiene la configuración central para Builder.io
 *
 * Para obtener tu API key:
 * 1. Ve a https://builder.io
 * 2. Crea una cuenta o inicia sesión
 * 3. Ve a Settings > API Keys
 * 4. Copia tu Public API Key
 * 5. Reemplaza 'YOUR_BUILDER_IO_API_KEY' con tu clave
 */

export const builderConfig = {
  // Reemplaza esto con tu API key de Builder.io
  apiKey: process.env.VITE_BUILDER_IO_API_KEY || 'YOUR_BUILDER_IO_API_KEY',

  // Modelos de contenido personalizados
  models: {
    modal: 'modal',
    notification: 'notification',
    form: 'form',
  },

  // Configuración de temas para sincronizar con tu sistema actual
  themes: {
    'dark-turquoise': {
      accentPrimary: '#00bcd4',
      bgPrimary: '#0a0e27',
      bgSecondary: '#1a1f3a',
      bgCard: '#242b4a',
      textPrimary: '#ffffff',
      textSecondary: '#94a3b8',
      borderColor: '#2d3b5f',
    },
    'light-minimal': {
      accentPrimary: '#2563eb',
      bgPrimary: '#ffffff',
      bgSecondary: '#f8fafc',
      bgCard: '#ffffff',
      textPrimary: '#0f172a',
      textSecondary: '#64748b',
      borderColor: '#e2e8f0',
    },
    'turquoise-gradient': {
      accentPrimary: '#06b6d4',
      bgPrimary: '#0f172a',
      bgSecondary: '#1e293b',
      bgCard: '#1e293b',
      textPrimary: '#f1f5f9',
      textSecondary: '#94a3b8',
      borderColor: '#334155',
    },
  },
};

export default builderConfig;
