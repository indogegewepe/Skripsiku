<script setup>
import { useRoute } from 'vue-router';
import AddDosenForm from '~/components/AddDosenForm.vue';

const route = useRoute();
const idDosen = route.query.id_dosen; // Ambil id_dosen dari query parameter
</script>

<template>
    <AddDosenForm :idDosen="idDosen" />
</template>