<script setup>
import { useRouter } from 'vue-router';

const router = useRouter();
</script>

<template>
  <div>
    <button class="secondary" @click="router.push('/dosen')">Data Dosen</button>
  </div>
  <div>
    <button class="secondary" @click="router.push('/proses')">Proses</button>
  </div>

</template>
