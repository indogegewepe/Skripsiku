<script setup>
import { ref, computed, onMounted, h, resolveComponent } from 'vue'
import { useRouter } from 'vue-router'
import useApi from '~/composables/useApi'

const router = useRouter()
const { fetchData, sendData } = useApi()

const UTable = resolveComponent('UTable')
const UButton = resolveComponent('UButton')
const UInput = resolveComponent('UInput')
const UCard = resolveComponent('UCard')
const UModal = resolveComponent('UModal')

const dataDosenList = ref([])
const pending = ref(true)
const error = ref(null)
const searchDosen = ref('')

const toast = useToast()

const fetchDosenData = async () => {
  try {
    pending.value = true
    const response = await fetchData('dosen')
    dataDosenList.value = response || []
  } catch (err) {
    error.value = err
    console.error('Error fetching data:', err)
  } finally {
    pending.value = false
  }
}

const form = ref({
  id_dosen: '',
  nama_dosen: ''
})

async function handleSubmit() {
  try {
    const payload = {
      id_dosen: parseInt(form.value.id_dosen),
      nama_dosen: form.value.nama_dosen
    }
    
    if (form.value.id_dosen && dataDosenList.value.find(d => d.id_dosen === parseInt(form.value.id_dosen))) {
      await sendData(`dosen/${form.value.id_dosen}`, 'PUT', payload)
    } else {
      await sendData('dosen', 'POST', payload)
    }
    
    await fetchDosenData()
    ToastBerhasil('Dosen berhasil disimpan')
    form.value = { id_dosen: '', nama_dosen: '' }
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

const handleDelete = async (idDosen) => {
  if (confirm('Apakah Anda yakin ingin menghapus data ini?')) {
    try {
      await sendData(`dosen/${idDosen}`, 'DELETE')
      await fetchDosenData()
      ToastBerhasil('Dosen berhasil dihapus')
    } catch (err) {
      showToastError('Terjadi kesalahan saat menghapus data', err)
    }
  }
}

const filteredSortedData = computed(() => {
  const searchTerm = searchDosen.value.toLowerCase()
  return dataDosenList.value
    .filter(dosen => dosen.nama_dosen.toLowerCase().includes(searchTerm))
    .sort((a, b) => a.id_dosen - b.id_dosen)
})

const tableData = computed(() => {
  return filteredSortedData.value.map(dosen => ({
    id_dosen: dosen.id_dosen,
    nama_dosen: dosen.nama_dosen
  }))
})

const columns = [
  {
    accessorKey: 'id_dosen',
    header: 'ID',
    cell: ({ row }) => h('span', row.original.id_dosen)
  },
  {
    accessorKey: 'nama_dosen',
    header: 'Nama Dosen',
    cell: ({ row }) => h('span', row.original.nama_dosen)
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
          onClick: () => router.push(`/diredit/d${row.original.id_dosen}`)
        }),
        h(UButton, {
          label: 'Hapus',
          color: 'error',
          size: 'lg',
          icon: 'i-lucide-trash',
          onClick: () => handleDelete(row.original.id_dosen)
        })
      ])
    },
    pin: 'right'
  }
]

onMounted(() => {
  fetchDosenData()
})
</script>

<template>
  <div class="container mx-auto p-4 lg:p-6">
    <UCard variant="soft" class="shadow-lg">
      <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 p-4">
        <h1 class="text-2xl font-bold">Data Dosen</h1>
        <div class="flex gap-2 w-full sm:w-auto">
          <UInput
            v-model="searchDosen"
            placeholder="Cari dosen..."
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
            title="Tambah Dosen"
            :close="{ color: 'error', class: 'rounded-md' }"
          >
            <UButton label="Tambah Dosen" icon="i-lucide-plus" color="success"/>
            <template #body>
              <form class="space-y-4" @submit.prevent="handleSubmit">
                <label for="id_dosen">ID Dosen:</label>
                <UInput
                  id="id_dosen"
                  v-model="form.id_dosen"
                  type="number"
                  class="w-full"
                  size="lg"
                  placeholder="Masukkan ID Dosen"
                  required
                />
                <label for="nama_dosen">Nama Dosen:</label>
                <UInput
                  id="nama_dosen"
                  v-model="form.nama_dosen"
                  class="w-full"
                  size="lg"
                  placeholder="Masukkan Nama Dosen"
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

      <div v-else-if="error" class="p-4 bg-red-50 border border-red-200 text-red-600 rounded-md m-4">
        <p>Error: {{ error.message }}</p>
      </div>

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