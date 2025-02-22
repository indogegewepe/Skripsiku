<script setup>
import '@picocss/pico/css/pico.min.css';

useHead({
  titleTemplate: (title) => (title ? `${title} | Penjadwalan` : "Skripsi")
});

</script>

<template>
  <NuxtPage />
</template>

<style>
/* Tambahkan padding ke tabel */
table, th, td {
    border: 1px solid black;
    border-collapse: collapse;
    padding: 8px;
}

/* Perbaiki tampilan tabel */
table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 20px;
}

body{
  padding: 40px 50px;
}

:root:not([data-theme]) {
  --pico-background-color: #232323;
}

button[type=submit], td button{
  background-color: #198654;
  border-color: #198654;
}

td button{
  max-width: 7rem;
  place-content: center;
}

button.secondary{
  background-color: #db3545;
  place-content: center;
}

button a{
  color: white;
  text-decoration: none;
}

select{
  background-color: #000;
}

select:active{
  border-color: #198654;
}
</style>
