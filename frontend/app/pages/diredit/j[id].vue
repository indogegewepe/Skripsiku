<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import useApi from '~/composables/useApi'

const router = useRouter()
const route = useRoute()
const { id } = route.params
const toast = useToast()
const { fetchData, sendData } = useApi()

const form = ref({
  id_jam: null,
  jam_awal: '',
  jam_akhir: ''
})

const isLoading = ref(true)
const isSubmitting = ref(false)

onMounted(async () => {
  try {
    const data = await fetchData(`jam/${id}`)
    form.value = {
      id_jam: id,
      jam_awal: data.jam_awal,
      jam_akhir: data.jam_akhir
    }
  } catch (error) {
    toast.add({
      title: 'Gagal',
      message: 'Terjadi kesalahan: ' + error,
      icon: 'i-lucide-close-circle',
      duration: 5000,
      color: 'error'
    })
  } finally {
    isLoading.value = false
  }
})

const goToEdit = (type) => {
  router.push({ path: '/edit', query: { type } })
}

const ToastBerhasil = (message) => {
  toast.add({
    title: 'Berhasil',
    message: message,
    icon: 'i-lucide-check-circle',
    duration: 5000,
    color: 'success'
  })
}

const handleSubmit = async () => {
  try {
    isSubmitting.value = true
    const payload = {
      id_jam: parseInt(id), // Tambahkan id_jam dari parameter route
      jam_awal: form.value.jam_awal,
      jam_akhir: form.value.jam_akhir
    }
    await sendData(`jam/${id}`, 'PUT', payload)
    ToastBerhasil('Data jam berhasil diperbarui')
    goToEdit('jam')
  } catch (error) {
    toast.add({
      title: 'Gagal',
      message: 'Terjadi kesalahan: ' + error,
      icon: 'i-lucide-close-circle',
      duration: 5000,
      color: 'error'
    })
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <div class="p-4">
    <UCard variant="soft">
      <template #header>
        <h2 class="text-2xl font-bold">Edit Jam</h2>
      </template>

      <form @submit.prevent="handleSubmit">
        <div class="space-y-4">
          <label for="id_jam">ID Jam</label>
          <UInput id="id_jam" v-model="id" class="w-full" disabled />

          <label for="jam_awal">Jam Awal</label>
          <UInput 
            id="jam_awal" 
            v-model="form.jam_awal" 
            class="w-full" 
            placeholder="HH:MM:SS"
            required 
          />

          <label for="jam_akhir">Jam Akhir</label>
          <UInput 
            id="jam_akhir" 
            v-model="form.jam_akhir" 
            class="w-full" 
            placeholder="HH:MM:SS"
            required 
          />
        </div>

        <div class="mt-6 flex justify-end gap-3">
          <UButton type="button" label="Batal" color="error" @click="goToEdit('jam')" />
          <UButton type="submit" label="Simpan Perubahan" :loading="isSubmitting" />
        </div>
      </form>
    </UCard>
  </div>
</template>