<template>
    <div>
      <h2>Edit Mata Kuliah</h2>
      <form @submit.prevent="submitForm">
        <label>Nama Mata Kuliah:</label>
        <input v-model="matkul.nama" placeholder="Masukkan nama mata kuliah" />
  
        <label>SKS:</label>
        <input v-model="matkul.sks" type="number" placeholder="Masukkan jumlah SKS" />
  
        <button type="submit">Simpan</button>
      </form>
    </div>
  </template>
  
  <script setup>
  import { ref } from 'vue'
  
  const matkul = ref({
    nama: '',
    sks: ''
  })
  
  const submitForm = () => {
    console.log('Data Mata Kuliah:', matkul.value)
  }
  </script>
  