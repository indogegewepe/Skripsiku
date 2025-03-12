export default defineNuxtConfig({
  runtimeConfig: {
    public: {
      baseUrl: process.env.BASE_URL || 'http://localhost:8000',
    },
  },

  compatibilityDate: '2025-02-23',
  modules: ['compodium', '@nuxt/ui'],
  css: ['~/assets/css/main.css'],
  ui: {
    prefix: 'Nuxt',
    fonts: false,
    colorMode: false,
    theme: {
      colors: ['primary', 'error']
    }
  },

  devtools: {
    timeline: {
      enabled: true,
    },
  },
});