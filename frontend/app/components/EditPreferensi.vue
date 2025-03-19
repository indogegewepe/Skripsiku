<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import useApi from '~/composables/useApi'

const toast = useToast();
const router = useRouter()
const { fetchData } = useApi()

function ShowToast() {
  toast.add({
    title: 'Terjadi kesalahan!',
    icon: 'i-lucide-error-circle',
    duration: 5000,
    color: 'error'
  })
}

const { data: dosen } = await useFetch('dosen'), {
  method: 'GET',
  headers: {
    'Content-Type': 'application
  }
}


</script>

<template>
  <div class="min-h-screen flex items-center justify-center">
    <UCard class="shadow-lg bg-white container max-w-4xl" variant="soft">
        <h1 class="text-2xl font-semibold text-black">Edit Preferensi</h1>
        
        
        <USelect :items="dosen.value" />


          <UButton 
            type="button"
            color="success"
            label="Simpan" 
            @click="ShowToast()"
          />
          <UButton
            type="button"
            label="Kembali"
            color="error"
            @click="router.push('/')"
          />
    </UCard>
  </div>
</template>