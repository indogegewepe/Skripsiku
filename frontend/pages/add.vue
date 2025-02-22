<script setup>
import { useRoute } from 'vue-router';
import AddDosenForm from '@/components/AddDosenForm.vue';

const route = useRoute();
const idDosen = route.query.id_dosen;
</script>

<template>
  <div class="container" style="height: 100vh;align-content: center;">
    <h1>Tambah Mata Kuliah</h1>
    <AddDosenForm :idDosen="idDosen" />
  </div>
</template>
