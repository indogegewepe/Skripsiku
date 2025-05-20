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

const dataJamList = ref([])
const pending = ref(true)
const error = ref(null)
const searchJam = ref('')

const toast = useToast()

const fetchJamData = async () => {
  try {
    pending.value = true
    const response = await fetchData('jam')
    dataJamList.value = response || []
  } catch (err) {
    error.value = err
    console.error('Error fetching data:', err)
  } finally {
    pending.value = false
  }
}

const form = ref({
  id_jam: '',
  jam_awal: '',
  jam_akhir: ''
})

async function handleSubmit() {
  try {
    const idJam = parseInt(form.value.id_jam)
    if (isNaN(idJam) || !form.value.jam_awal || !form.value.jam_akhir) {
      showToastError('Data tidak lengkap', 'ID, Jam Awal, dan Jam Akhir wajib diisi')
      return
    }

    const exists = dataJamList.value.some(j => j.id_jam === idJam)
    if (exists) {
      showToastError('ID Jam sudah terdaftar', 'Tidak dapat menyimpan data dengan ID yang sama')
      return
    }

    const payload = {
      id_jam: idJam,
      jam_awal: form.value.jam_awal,
      jam_akhir: form.value.jam_akhir
    }

    await sendData('jam', 'POST', payload)
    await fetchJamData()
    ToastBerhasil('Jam berhasil disimpan')
    form.value = { id_jam: '', jam_awal: '', jam_akhir: '' }
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

const handleDelete = async (idJam) => {
  if (confirm('Apakah Anda yakin ingin menghapus data ini?')) {
    try {
      await sendData(`jam/${idJam}`, 'DELETE')
      await fetchJamData()
      ToastBerhasil('Jam berhasil dihapus')
    } catch (err) {
      showToastError('Terjadi kesalahan saat menghapus data', err)
    }
  }
}

const filteredSortedData = computed(() => {
  const searchTerm = searchJam.value.toLowerCase()
  return dataJamList.value
    .filter(jam => 
      jam.jam_awal.toLowerCase().includes(searchTerm) ||
      jam.jam_akhir.toLowerCase().includes(searchTerm)
    )
    .sort((a, b) => a.id_jam - b.id_jam)
})

const tableData = computed(() => {
  return filteredSortedData.value.map(jam => ({
    id_jam: jam.id_jam,
    jam_awal: jam.jam_awal,
    jam_akhir: jam.jam_akhir
  }))
})

const columns = [
  {
    accessorKey: 'id_jam',
    header: 'ID',
    cell: ({ row }) => h('span', row.original.id_jam)
  },
  {
    accessorKey: 'jam_awal',
    header: 'Jam Awal',
    cell: ({ row }) => h('span', row.original.jam_awal)
  },
  {
    accessorKey: 'jam_akhir',
    header: 'Jam Akhir',
    cell: ({ row }) => h('span', row.original.jam_akhir)
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
          onClick: () => router.push(`/diredit/j${row.original.id_jam}`)
        }),
        h(UButton, {
          label: 'Hapus',
          color: 'error',
          size: 'lg',
          icon: 'i-lucide-trash',
          onClick: () => handleDelete(row.original.id_jam)
        })
      ])
    },
    pin: 'right'
  }
]

onMounted(() => {
  fetchJamData()
})
</script>

<template>
  <div class="container mx-auto p-4 lg:p-6">
    <UCard variant="soft" class="shadow-lg">
      <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 p-4">
        <h1 class="text-2xl font-bold">Data Jam</h1>
        <div class="flex gap-2 w-full sm:w-auto">
          <UInput
            v-model="searchJam"
            placeholder="Cari jam..."
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
            title="Tambah Jam"
            :close="{ color: 'error', class: 'rounded-md' }"
          >
            <UButton label="Tambah Jam" icon="i-lucide-plus" color="success"/>
            <template #body>
              <form class="space-y-4" @submit.prevent="handleSubmit">
                <label for="id_jam">ID Jam:</label>
                <UInput
                  id="id_jam"
                  v-model="form.id_jam"
                  label="ID Jam"
                  type="number"
                  class="w-full"
                  size="lg"
                  placeholder="Masukkan ID Jam"
                  required
                />
                <label for="jam_awal">Jam Awal:</label>
                <UInput
                  id="jam_awal"
                  v-model="form.jam_awal"
                  label="Jam Awal"
                  class="w-full"
                  size="lg"
                  placeholder="HH:MM:SS"
                  required
                />
                <label for="jam_akhir">Jam Akhir:</label>
                <UInput
                  id="jam_akhir"
                  v-model="form.jam_akhir"
                  label="Jam Akhir"
                  class="w-full"
                  size="lg"
                  placeholder="HH:MM:SS"
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