<script setup>
import { useRouter } from 'vue-router';

const router = useRouter();

const goToEdit = (type) => {
  router.push({ path: '/edit', query: { type } })
}
</script>

<template>
  <div class="min-h-screen flex items-center justify-center">
    <UCard class="w-full max-w-screen-md rounded-lg shadow-lg p-6" variant="soft">
      <h1 class="font-bold sm:text-7xl text-2xl text-center mb-6">
        Penjadwalan
      </h1>
      
      <!-- Tombol Utama -->
      <div class="flex flex-wrap justify-center gap-4 mb-6">
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
          trailing-icon="i-lucide-arrow-right"
          class="px-8 py-4 shadow-lg"
          @click="router.push('/proses')"
        />
      </div>
      <div class="flex flex-wrap justify-center gap-4">
        <UButton
          label="Edit Preferensi Dosen"
          color="secondary"
          icon="i-lucide-edit"
          class="px-8 py-4 shadow-lg"
          @click="goToEdit('dosen')"
        />
        <UButton
          label="Data Mata Kuliah"
          color="warning"
          icon="i-lucide-book-open"
          class="px-8 py-4 shadow-lg"
          @click="goToEdit('matkul')"
        />
        <UButton
          label="Data Ruang"
          color="success"
          icon="i-lucide-building"
          class="px-8 py-4 shadow-lg"
          @click="goToEdit('ruang')"
        />
        <UButton
          label="Edit Jam"
          color="error"
          icon="i-lucide-clock"
          class="px-8 py-4 shadow-lg"
          @click="goToEdit('jam')"
        />
        <UButton
          label="Edit Hari"
          color="info"
          icon="i-lucide-calendar"
          class="px-8 py-4 shadow-lg"
          @click="goToEdit('hari')"
        />
      </div>
    </UCard>
  </div>
</template>