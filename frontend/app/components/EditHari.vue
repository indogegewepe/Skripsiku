<template>
    <div>
      <h2>Edit Hari</h2>
      <form @submit.prevent="submitForm">
        <label>Nama Hari:</label>
        <input v-model="hari.nama" placeholder="Masukkan nama hari" />
  
        <button type="submit">Simpan</button>
      </form>
    </div>
  </template>
  
  <script setup>
  import { ref } from 'vue'
  
  const hari = ref({
    nama: ''
  })
  
  const submitForm = () => {
    console.log('Data Hari:', hari.value)
  }
  </script>
  