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

const dataHariList = ref([])
const pending = ref(true)
const error = ref(null)
const searchHari = ref('')

const toast = useToast()

const fetchHariData = async () => {
  try {
    pending.value = true
    const response = await fetchData('hari')
    dataHariList.value = response || []
  } catch (err) {
    error.value = err
    console.error('Error fetching data:', err)
  } finally {
    pending.value = false
  }
}

const form = ref({
  id_hari: '',
  nama_hari: ''
})

async function handleSubmit() {
  try {
    const payload = {
      id_hari: parseInt(form.value.id_hari),
      nama_hari: form.value.nama_hari
    }
    
    if (form.value.id_hari && dataHariList.value.find(h => h.id_hari === parseInt(form.value.id_hari))) {
      await sendData(`hari/${form.value.id_hari}`, 'PUT', payload)
    } else {
      await sendData('hari', 'POST', payload)
    }
    
    await fetchHariData()
    ToastBerhasil('Hari berhasil disimpan')
    form.value = { id_hari: '', nama_hari: '' }
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

const handleDelete = async (idHari) => {
  if (confirm('Apakah Anda yakin ingin menghapus data ini?')) {
    try {
      await sendData(`hari/${idHari}`, 'DELETE')
      await fetchHariData()
      ToastBerhasil('Hari berhasil dihapus')
    } catch (err) {
      showToastError('Terjadi kesalahan saat menghapus data', err)
    }
  }
}

const filteredSortedData = computed(() => {
  const searchTerm = searchHari.value.toLowerCase()
  return dataHariList.value
    .filter(hari => hari.nama_hari.toLowerCase().includes(searchTerm))
    .sort((a, b) => a.id_hari - b.id_hari)
})

const tableData = computed(() => {
  return filteredSortedData.value.map(hari => ({
    id_hari: hari.id_hari,
    nama_hari: hari.nama_hari
  }))
})

const columns = [
  {
    accessorKey: 'id_hari',
    header: 'ID',
    cell: ({ row }) => h('span', row.original.id_hari)
  },
  {
    accessorKey: 'nama_hari',
    header: 'Nama Hari',
    cell: ({ row }) => h('span', row.original.nama_hari)
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
          onClick: () => router.push(`/diredit/h${row.original.id_hari}`)
        }),
        h(UButton, {
          label: 'Hapus',
          color: 'error',
          size: 'lg',
          icon: 'i-lucide-trash',
          onClick: () => handleDelete(row.original.id_hari)
        })
      ])
    },
    pin: 'right'
  }
]

onMounted(() => {
  fetchHariData()
})
</script>

<template>
  <div class="container mx-auto p-4 lg:p-6">
    <UCard variant="soft" class="shadow-lg">
      <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 p-4">
        <h1 class="text-2xl font-bold">Data Hari</h1>
        <div class="flex gap-2 w-full sm:w-auto">
          <UInput
            v-model="searchHari"
            placeholder="Cari hari..."
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
            title="Tambah Hari"
            :close="{ color: 'error', class: 'rounded-md' }"
          >
            <UButton label="Tambah Hari" icon="i-lucide-plus" color="success"/>
            <template #body>
              <form class="space-y-4" @submit.prevent="handleSubmit">
                <label for="id_hari">ID Hari:</label>
                <UInput
                  id="id_hari"
                  v-model="form.id_hari"
                  type="number"
                  class="w-full"
                  size="lg"
                  placeholder="Masukkan ID Hari"
                  required
                />
                <label for="nama_hari">Nama Hari:</label>
                <UInput
                  id="nama_hari"
                  v-model="form.nama_hari"
                  class="w-full"
                  size="lg"
                  placeholder="Masukkan Nama Hari"
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