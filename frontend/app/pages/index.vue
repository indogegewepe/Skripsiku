<script setup>
import { useRouter } from 'vue-router';

const router = useRouter();
</script>

<template>
  <div class="min-h-screen flex items-center justify-center ">
    <div class="w-full max-w-screen-md bg-white border border-black rounded-lg shadow-lg p-6">
      <h1 class="font-bold text-7xl text-black text-center mb-6">
        Penjadwalan
      </h1>
      
      <div class="flex justify-center gap-4">
        <UButton
          label="Data Dosen"
          color="primary"
          icon="i-lucide-database"
          class="px-8 py-4 shadow-lg"
          @click="router.push('/dosen')"
        />
        <UButton
          label="Proses"
          color="info"
          icon="i-lucide-arrow-right"
          class="px-8 py-4 shadow-lg"
          @click="router.push('/proses')"
        />
      </div>
    </div>
  </div>
</template>