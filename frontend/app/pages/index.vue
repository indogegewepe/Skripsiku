<script setup>
import { useRouter } from 'vue-router';

const router = useRouter();
</script>

<template>
  <div class="min-h-screen flex items-center justify-center">
    <div class="w-full max-w-screen-md bg-white border border-black rounded-lg shadow-lg p-6">
      <h1 class="font-bold text-7xl text-black text-center mb-6">
        Penjadwalan
      </h1>
      
      <!-- Tombol Utama -->
      <div class="flex justify-center gap-4 mb-6">
        <UButton
          label="Data Dosen"
          color="success"
          icon="i-lucide-database"
          class="px-8 py-4 shadow-lg"
          @click="router.push('/dosen')"
        />
        <UButton
          label="Proses"
          color="info"
          icon="i-lucide-cpu"
          class="px-8 py-4 shadow-lg"
          @click="router.push('/proses')"
        />
      </div>
      <div class="flex flex-wrap justify-center gap-4">
        <UButton
          label="Edit Dosen"
          color="secondary"
          icon="i-lucide-edit"
          class="px-8 py-4 shadow-lg"
          @click="router.push('/edit-dosen')"
        />
        <UButton
          label="Data Mata Kuliah"
          color="warning"
          icon="i-lucide-book-open"
          class="px-8 py-4 shadow-lg"
          @click="router.push('/mata-kuliah')"
        />
        <UButton
          label="Data Ruang"
          color="success"
          icon="i-lucide-building"
          class="px-8 py-4 shadow-lg"
          @click="router.push('/ruang')"
        />
        <UButton
          label="Edit Jam"
          color="error"
          icon="i-lucide-clock"
          class="px-8 py-4 shadow-lg"
          @click="router.push('/edit-jam')"
        />
        <UButton
          label="Edit Hari"
          color="info"
          icon="i-lucide-calendar"
          class="px-8 py-4 shadow-lg"
          @click="router.push('/edit-hari')"
        />
      </div>
    </div>
  </div>
</template>
