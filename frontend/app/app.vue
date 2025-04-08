<script setup>
useSeoMeta({
  title: 'Skripsi Penjadwalan',
  description: 'Ini adalah deskripsi halaman utama untuk meningkatkan SEO situs Penjadwalan.',
  ogTitle: 'Halaman Utama | Penjadwalan',
  ogDescription: 'Temukan jadwal dan informasi penting seputar penjadwalan di sini.',
  ogImage: 'https://kinsta.com/wp-content/uploads/2022/05/nuxt-js-logo.jpeg',  // Ganti dengan URL gambar Open Graph yang valid
  twitterTitle: 'Halaman Utama | Penjadwalan',
  twitterDescription: 'Temukan informasi lengkap tentang penjadwalan di situs kami.',
  twitterImage: 'https://kinsta.com/wp-content/uploads/2022/05/nuxt-js-logo.jpeg', // Ganti dengan URL gambar Twitter yang valid
  twitterCard: 'summary_large_image'
})

useHead({
  htmlAttrs: {
    lang: 'en'
  },
  titleTemplate: (title) => (title ? `${title} | Penjadwalan` : 'Skripsi')
})
</script>

<template>
  <UApp>
    <NuxtPage />
  </UApp>
</template>
