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
  id_hari: null,
  nama_hari: ''
})

const isLoading = ref(true)
const isSubmitting = ref(false)

onMounted(async () => {
  try {
    const data = await fetchData(`hari/${id}`)
    form.value = {
      id_hari: id,
      nama_hari: data.nama_hari
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
      id_hari: parseInt(id),
      nama_hari: form.value.nama_hari
    }
    await sendData(`hari/${id}`, 'PUT', payload)
    ToastBerhasil('Data hari berhasil diperbarui')
    goToEdit('hari')
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
        <h2 class="text-2xl font-bold">Edit Hari</h2>
      </template>

      <form @submit.prevent="handleSubmit">
        <div class="space-y-4">
          <label for="id_hari">ID Hari</label>
          <UInput id="id_hari" v-model="id" class="w-full" disabled />

          <label for="nama_hari">Nama Hari</label>
          <UInput 
            id="nama_hari" 
            v-model="form.nama_hari" 
            class="w-full"
            placeholder="Contoh: Senin"
            required 
          />
        </div>

        <div class="mt-6 flex justify-end gap-3">
          <UButton type="button" label="Batal" color="error" @click="goToEdit('hari')" />
          <UButton type="submit" label="Simpan Perubahan" :loading="isSubmitting" />
        </div>
      </form>
    </UCard>
  </div>
</template>