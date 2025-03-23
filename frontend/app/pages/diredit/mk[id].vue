<script setup>
import useApi from '~/composables/useApi'
import { useRouter } from 'vue-router';

const router = useRouter();
const route = useRoute()
const { id } = route.params
const toast = useToast()
const { fetchData, sendData } = useApi()

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
  });
}

const showToastError = (message, error) => {
  toast.add({
    title: 'Gagal',
    message: message + ': ' + error,
    icon: 'i-lucide-close-circle',
    duration: 5000,
    color: 'red'
  });
}

const form = ref({
  id_mk_genap: null,
  nama_mk_genap: '',
  smt: null,
  sks: null,
  sifat: '',
  metode: '',
  kategori: ''
})

const isSubmitting = ref(false)
const isLoading = ref(true)

onMounted(async () => {
  try {
    const data = await fetchData(`mk_genap/${id}`)
    form.value = {
      id_mk_genap: id,
      nama_mk_genap: data.nama_mk_genap,
      sks: data.sks,
      smt: data.smt,
      sifat: data.sifat,
      metode: data.metode,
      kategori: data.kategori
    }
  } catch (error) {
    showToastError('Terjadi kesalahan', error)
  } finally {
    isLoading.value = false
  }
})

// Handle submit form
const handleSubmit = async () => {
  try {
    isSubmitting.value = true
    
    const payload = {
      id_mk_genap: id,
      nama_mk_genap: form.value.nama_mk_genap,
      sks: form.value.sks,
      smt: form.value.smt,
      sifat: form.value.sifat,
      metode: form.value.metode,
      kategori: form.value.kategori
    }
    await sendData(`mk_genap/${id}`, 'PUT', payload)
    ToastBerhasil('Data mata kuliah berhasil diperbarui')
    goToEdit('matkul')
  } catch (error) {
    showToastError('Terjadi kesalahan', error)
  } finally {
    isSubmitting.value = false
  }
}

const metode = ref(['Online', 'Offline'])
const sifat = ref(['Wajib', 'Pilihan'])
const kategori = ref(['-', 'Sistem Cerdas', 'Relata'])
</script>

<template>
  <div class="p-4">
    <UCard variant="soft">
      <template #header>
        <h2 class="text-2xl font-bold">Edit Mata Kuliah</h2>
      </template>

      <form @submit.prevent="handleSubmit">
        <div class="space-y-4">
          <label for="id_mk_genap">ID Mata Kuliah</label>
          <UInput id="id_mk_genap" v-model="id" class="w-full" disabled/>
          <label for="nama_mk_genap">Nama Mata Kuliah</label>
          <UInput id="nama_mk_genap" v-model="form.nama_mk_genap" class="w-full" required />
          <label for="smt">Semester</label>
          <UInput id="smt" v-model="form.smt" class="w-full" required />
          <label for="sks">SKS</label>
          <UInput id="sks" v-model="form.sks" class="w-full" required />
          <label for="sifat">Sifat</label>
          <USelect id="sifat" v-model="form.sifat" class="w-full" :items="sifat" required />
          <label for="kategori">Kategori</label>
          <USelect id="kategori" v-model="form.kategori" class="w-full" :items="kategori" required />
          <label for="metode">Metode</label>
          <USelect id="metode" v-model="form.metode" class="w-full" :items="metode" required />
        </div>

        <div class="mt-6 flex justify-end gap-3">
          <UButton
            type="button"
            label="Batal"
            color="error"
            @click="goToEdit('matkul')"
          />
          <UButton
            type="submit"
            label="Simpan Perubahan"
            :loading="isSubmitting"
          />
        </div>
      </form>
    </UCard>
  </div>
</template>