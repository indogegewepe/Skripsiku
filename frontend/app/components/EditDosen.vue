<template>
    <div>
      <h2>Edit Dosen</h2>
      <form @submit.prevent="submitForm">
        <label>Nama Dosen:</label>
        <input v-model="dosen.nama" placeholder="Masukkan nama dosen" />
  
        <label>Mata Kuliah:</label>
        <input v-model="dosen.mataKuliah" placeholder="Masukkan mata kuliah" />
  
        <button type="submit">Simpan</button>
      </form>
    </div>
  </template>
  
  <script setup>
  import { ref } from 'vue'
  
  const dosen = ref({
    nama: '',
    mataKuliah: ''
  })
  
  const submitForm = () => {
    console.log('Data Dosen:', dosen.value)
  }
  </script>
  