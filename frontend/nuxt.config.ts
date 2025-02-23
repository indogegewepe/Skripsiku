export default defineNuxtConfig({
  runtimeConfig: {
    public: {
      baseUrl: process.env.BASE_URL || 'http://localhost:8000',
    },
  },

  compatibilityDate: '2025-02-23',
});