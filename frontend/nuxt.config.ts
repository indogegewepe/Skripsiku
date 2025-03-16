export default defineNuxtConfig({
  devtools: { enabled: true },

  modules: [
    '@nuxt/ui',
    '@nuxt/eslint'
  ],

  css: ['~/assets/css/main.css'],

  future: {
    compatibilityVersion: 4
  },

  runtimeConfig: {
    public: {
      // BASE_URL: 'http://0.0.0.0:8000',
      BASE_URL: 'https://backend-jadwal.vercel.app',
    },
  },

  compatibilityDate: '2025-03-15'
})