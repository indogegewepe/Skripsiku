export default {
  modules: [
    '@nuxtjs/axios',
  ],
  axios: {
    baseURL: 'http://localhost:8000', // Sesuaikan dengan base URL FastAPI
  },
}