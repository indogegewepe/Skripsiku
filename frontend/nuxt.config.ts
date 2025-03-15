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
      BASE_URL: 'http://0.0.0.0:8000',
    },
  }
})