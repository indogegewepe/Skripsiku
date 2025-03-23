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
      <div class="flex flex-wrap justify-center gap-4 mb-6">
        <UButton
          label="Data Dosen"
          color="secondary"
          icon="i-lucide-database"
          class="px-8 py-4 shadow-lg"
          @click="router.push('/dosen')"
        />
        <UButton
          label="Proses"
          color="success"
          trailing-icon="i-lucide-arrow-right"
          class="px-8 py-4 shadow-lg"
          @click="router.push('/proses')"
        />
      </div>
      <div class="flex flex-wrap justify-center gap-4 mb-6">
        <UButton
          label="Edit Preferensi Dosen"
          color="warning"
          icon="i-lucide-edit"
          class="px-8 py-4 shadow-lg"
          @click="goToEdit('preferensiDosen')"
        />
        <UButton
          label="Edit Preferensi Prodi"
          color="error"
          icon="i-lucide-users"
          class="px-8 py-4 shadow-lg"
          @click="goToEdit('preferensiProdi')"
        />
      </div>
      <div class="flex flex-wrap justify-center gap-4">
        
        <UButton
          label="Data Mata Kuliah"
          color="success"
          icon="i-lucide-book-open"
          class="px-8 py-4 shadow-lg"
          @click="goToEdit('matkul')"
        />
        <UButton
          label="Data Ruang"
          color="info"
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
          color="warning"
          icon="i-lucide-calendar"
          class="px-8 py-4 shadow-lg"
          @click="goToEdit('hari')"
        />
        <UButton
          label="Edit Dosen"
          color="success"
          icon="i-lucide-user"
          class="px-8 py-4 shadow-lg"
          @click="goToEdit('dosen')"
        />
        
      </div>
    </UCard>
  </div>
</template>