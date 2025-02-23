export default defineNuxtConfig({
  runtimeConfig: {
    public: {
      baseUrl: process.env.BASE_URL || 'http://localhost:8000',
    },
  },
});