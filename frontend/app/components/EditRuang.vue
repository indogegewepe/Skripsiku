<script setup>
import { ref, computed, onMounted, h, resolveComponent } from 'vue'
import { useRouter } from 'vue-router'
import useApi from '~/composables/useApi'

const router = useRouter()
const { fetchData, sendData } = useApi()

// Resolve component yang digunakan
const UTable = resolveComponent('UTable')
const UButton = resolveComponent('UButton')
const UInput = resolveComponent('UInput')
const UCard = resolveComponent('UCard')
const UModal = resolveComponent('UModal')

const dataRuangList = ref([])
const pending = ref(true)
const error = ref(null)
const searchRuang = ref('')

const toast = useToast()

// Fungsi untuk mengambil data ruang dari endpoint /ruang
const fetchRuangData = async () => {
  try {
    pending.value = true
    const response = await fetchData('ruang')
    dataRuangList.value = response || []
  } catch (err) {
    error.value = err
    console.error('Error fetching data:', err)
  } finally {
    pending.value = false
  }
}

// Form untuk tambah/edit data ruang
const form = ref({
  id_ruang: '',
  nama_ruang: ''
})

// Fungsi untuk menangani submit form tambah/edit
async function handleSubmit() {
  try {
    const payload = {
      id_ruang: parseInt(form.value.id_ruang),
      nama_ruang: form.value.nama_ruang
    }
    // Jika id_ruang sudah ada, lakukan update (PUT), jika tidak lakukan create (POST)
    let response
    if (form.value.id_ruang && dataRuangList.value.find(r => r.id_ruang === parseInt(form.value.id_ruang))) {
      response = await sendData(`ruang/${form.value.id_ruang}`, 'PUT', payload)
    } else {
      response = await sendData('ruang', 'POST', payload)
    }
    await fetchRuangData()
    ToastBerhasil('Ruang berhasil disimpan', response)
    // Reset form setelah submit
    form.value = { id_ruang: '', nama_ruang: '' }
  } catch (err) {
    showToastError('Terjadi kesalahan saat menyimpan data', err)
  }
}

function ToastBerhasil(msg) {
  toast.add({
    title: msg,
    icon: 'i-lucide-check-circle',
    duration: 5000,
    color: 'success'
  })
}

function showToastError(msg, err) {
  toast.add({
    title: msg,
    description: `Error: ${err}`,
    icon: 'i-lucide-error-circle',
    duration: 5000,
    color: 'error'
  })
}

// Fungsi untuk menghapus data ruang
const handleDelete = async (idRuang) => {
  if (confirm('Apakah Anda yakin ingin menghapus data ini?')) {
    try {
      await sendData(`ruang/${idRuang}`, 'DELETE')
      await fetchRuangData()
      ToastBerhasil('Ruang berhasil dihapus')
    } catch (err) {
      showToastError('Terjadi kesalahan saat menghapus data', err)
    }
  }
}

// Fungsi untuk mengisi form agar dapat diedit
const handleEdit = (ruang) => {
  form.value = { ...ruang }
}

// Filter dan sorting data berdasarkan pencarian
const filteredSortedData = computed(() => {
  const searchTerm = searchRuang.value.toLowerCase()
  return dataRuangList.value
    .filter(ruang => ruang.nama_ruang.toLowerCase().includes(searchTerm))
    .sort((a, b) => a.nama_ruang.localeCompare(b.nama_ruang))
})

// Data untuk ditampilkan pada tabel
const tableData = computed(() => {
  return filteredSortedData.value.map(ruang => ({
    id_ruang: ruang.id_ruang,
    nama_ruang: ruang.nama_ruang
  }))
})

// Definisi kolom untuk UTable
const columns = [
  {
    accessorKey: 'id_ruang',
    header: 'ID',
    cell: ({ row }) => h('span', row.original.id_ruang)
  },
  {
    accessorKey: 'nama_ruang',
    header: 'Nama Ruang',
    cell: ({ row }) => h('span', row.original.nama_ruang)
  },
  {
    id: 'actions',
    header: 'Actions',
    cell: ({ row }) => {
      return h('div', { class: 'flex gap-2' }, [
        h(UButton, {
          label: 'Edit',
          color: 'warning',
          size: 'lg',
          icon: 'i-lucide-edit',
          onClick: () => router.push(`/diredit/r${row.original.id_ruang}`)
        }),
        h(UButton, {
          label: 'Hapus',
          color: 'error',
          size: 'lg',
          icon: 'i-lucide-trash',
          onClick: () => handleDelete(row.original.id_ruang)
        })
      ])
    },
    pin: 'right'
  }
]

onMounted(() => {
  fetchRuangData()
})
</script>

<template>
  <div class="container mx-auto p-4 lg:p-6">
    <UCard variant="soft" class="shadow-lg">
      <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 p-4">
        <h1 class="text-2xl font-bold">Data Ruang</h1>
        <div class="flex gap-2 w-full sm:w-auto">
          <UInput
            v-model="searchRuang"
            placeholder="Cari ruang..."
            size="lg"
            icon="i-lucide-search"
          />
          <UButton
            label="Kembali"
            icon="i-lucide-arrow-left"
            color="error"
            size="lg"
            @click="router.push('/')"
          />
          <UModal
            title="Tambah Ruang"
            :close="{ color: 'error', class: 'rounded-md' }"
          >
            <UButton label="Tambah Ruang" icon="i-lucide-plus" color="success"/>
            <template #body>
              <form class="space-y-4" @submit.prevent="handleSubmit">
                <label for="id_ruang">ID Ruang:</label>
                <UInput
                  id="id_ruang"
                  v-model="form.id_ruang"
                  label="ID Ruang"
                  type="number"
                  class="w-full"
                  size="lg"
                  placeholder="Masukkan ID Ruang"
                  required
                />
                <label for="nama_ruang">Nama Ruang:</label>
                <UInput
                  id="nama_ruang"
                  v-model="form.nama_ruang"
                  label="Nama Ruang"
                  class="w-full"
                  size="lg"
                  placeholder="Masukkan Nama Ruang"
                  required
                />
                <div class="flex justify-end">
                  <UButton type="submit" label="Simpan" icon="i-lucide-save" color="primary"/>
                </div>
              </form>
            </template>
          </UModal>
        </div>
      </div>

      <div v-if="pending" class="p-8 text-center text-gray-500">
        <UButton loading label="Loading..." icon="i-lucide-sync"/>
      </div>

      <!-- Tampilan Error -->
      <div v-else-if="error" class="p-4 bg-red-50 border border-red-200 text-red-600 rounded-md m-4">
        <p>Error: {{ error.message }}</p>
      </div>

      <!-- Tabel Data -->
      <UCard v-else variant="soft" class="shadow-lg">
        <UTable
          :column-pinning="{ right: ['actions'] }"
          :data="tableData"
          :columns="columns"
          :row-class="index => index % 2 === 0 ? 'bg-white' : 'bg-gray-50'"
        />
      </UCard>
    </UCard>
  </div>
</template>
