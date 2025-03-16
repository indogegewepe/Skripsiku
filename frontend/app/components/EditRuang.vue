<template>
    <div>
      <h2>Edit Ruang</h2>
      <form @submit.prevent="submitForm">
        <label>Nama Ruang:</label>
        <input v-model="ruang.nama" placeholder="Masukkan nama ruang" />
  
        <button type="submit">Simpan</button>
      </form>
    </div>
  </template>
  
  <script setup>
  import { ref } from 'vue'
  
  const ruang = ref({
    nama: ''
  })
  
  const submitForm = () => {
    console.log('Data Ruang:', ruang.value)
  }
  </script>
  