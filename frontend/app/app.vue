<script setup>

useSeoMeta({
  description: '[description]',
  ogTitle: '[og:title]',
  ogDescription: '[og:description]',
  ogImage: '[og:image]',
  ogUrl: '[og:url]',
  twitterTitle: '[twitter:title]',
  twitterDescription: '[twitter:description]',
  twitterImage: '[twitter:image]',
  twitterCard: 'summary'
})

useHead({
  htmlAttrs: {
    lang: 'en'
  },
  titleTemplate: (title) => (title ? `${title} | Penjadwalan` : "Skripsi")
})

</script>

<template>
  <UApp>
    <NuxtPage />
  </UApp>
</template>