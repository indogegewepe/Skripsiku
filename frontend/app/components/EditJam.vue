<template>
    <div>
      <h2>Edit Jam</h2>
      <form @submit.prevent="submitForm">
        <label>Jam Awal:</label>
        <input v-model="jam.awal" type="time" />
  
        <label>Jam Akhir:</label>
        <input v-model="jam.akhir" type="time" />
  
        <button type="submit">Simpan</button>
      </form>
    </div>
  </template>
  
  <script setup>
  import { ref } from 'vue'
  
  const jam = ref({
    awal: '',
    akhir: ''
  })
  
  const submitForm = () => {
    console.log('Data Jam:', jam.value)
  }
  </script>
  