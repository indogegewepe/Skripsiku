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
  id_ruang: null,
  nama_ruang: ''
})

const isLoading = ref(true)
const isSubmitting = ref(false)

onMounted(async () => {
  try {
    const data = await fetchData(`ruang/${id}`)
    form.value = {
      id_ruang: id,
      nama_ruang: data.nama_ruang
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
      id_ruang: id,
      nama_ruang: form.value.nama_ruang
    }
    await sendData(`ruang/${id}`, 'PUT', payload)
    ToastBerhasil('Data ruang berhasil diperbarui')
    goToEdit('ruang')
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
        <h2 class="text-2xl font-bold">Edit Ruang</h2>
      </template>

      <form @submit.prevent="handleSubmit">
        <div class="space-y-4">
          <label for="id_ruang">ID Ruang</label>
          <UInput id="id_ruang" v-model="id" class="w-full" disabled />

          <label for="nama_ruang">Nama Ruang</label>
          <UInput id="nama_ruang" v-model="form.nama_ruang" class="w-full" required />
        </div>

        <div class="mt-6 flex justify-end gap-3">
          <UButton type="button" label="Batal" color="error" @click="goToEdit('ruang')" />
          <UButton type="submit" label="Simpan Perubahan" :loading="isSubmitting" />
        </div>
      </form>
    </UCard>
  </div>
</template>
