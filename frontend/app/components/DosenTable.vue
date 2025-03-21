<script setup>
import { ref, computed, onMounted, h, resolveComponent } from 'vue'
import { useRouter } from 'vue-router'
import useApi from '~/composables/useApi'

const router = useRouter()
const { fetchData, sendData } = useApi()

// Resolusi komponen
const UTable = resolveComponent('UTable')
const UButton = resolveComponent('UButton')
const UInput = resolveComponent('UInput')
const UCard = resolveComponent('UCard')

// State data
const dataDosenList = ref([])
const pending = ref(true)
const error = ref(null)
const searchNamaDosen = ref('')

const toast = useToast()

// Fungsi untuk mengambil data dosen
const fetchDosenData = async () => {
  try {
    pending.value = true
    const response = await fetchData(`data_dosen`)
    dataDosenList.value = response || []
  } catch (err) {
    error.value = err
    console.error('Error fetching data:', err)
  } finally {
    pending.value = false
  }
}

function showToast() {
  toast.add({
    title: 'Data berhasil dihapus',
    icon: 'i-lucide-check-circle',
    duration: 5000,
    color: 'success'
  })
}

function showToastError(err) {
  toast.add({
    title: 'Uh oh! Something went wrong.',
    description: `Error deleting data: ${err}`,
    icon: 'i-lucide-error-circle',
    duration: 5000,
    color: 'error'
  })
}

const handleDelete = async (idDosen, idMkGenap) => {
  if (confirm('Apakah Anda yakin ingin menghapus data ini?')) {
    try {
      const endpoint = `data_dosen/${idDosen}/${idMkGenap}`;
      await sendData(endpoint, 'DELETE');
      await fetchDosenData();
      showToast()
    } catch (err) {
      showToastError(err)
    }
  }
}

const filteredSortedData = computed(() => {
  const searchTerm = searchNamaDosen.value.toLowerCase()
  return dataDosenList.value
    .filter(dosen => dosen.nama_dosen.toLowerCase().includes(searchTerm))
    .sort((a, b) => a.nama_dosen.localeCompare(b.nama_dosen))
})

const tableData = computed(() => {
  const data = []
  filteredSortedData.value.forEach((dosen) => {
    const baseData = { 
      id_dosen: dosen.id_dosen,
      nama_dosen: dosen.nama_dosen
    }

    if (dosen.mata_kuliah && dosen.mata_kuliah.length > 0) {
      const courseRows = dosen.mata_kuliah.map((mk, index) => ({
        ...baseData,
        id_mk_genap: mk.id_mk_genap,
        nama_mk_genap: mk.nama_mk_genap,
        kelas: mk.kelas,
        rowSpan: index === 0 ? dosen.mata_kuliah.length + 1 : 0,
        isExtraRow: false
      }))
      
      courseRows.push({
        ...baseData,
        isExtraRow: true
      })
      data.push(...courseRows)
    } else {
      data.push({
        ...baseData,
        nama_mk_genap: 'Tidak ada mata kuliah',
        kelas: 'Tidak ada data',
        isExtraRow: false
      })
    }
  })
  return data
})

const columns = [
  {
    accessorKey: 'no',
    header: 'No.',
    width: 50,
    cell: ({ row }) => {
      if (row.original.isExtraRow || row.original.rowSpan === 0) return ''
      return dataDosenList.value.findIndex(dosen => dosen.id_dosen === row.original.id_dosen) + 1
    }
  },
  {
    accessorKey: 'nama_dosen',
    header: 'Nama Dosen',
    cell: ({ row }) => {
      if (row.original.isExtraRow || row.original.rowSpan === 0) return ''
      return h('span', { rowspan: row.original.rowSpan }, row.original.nama_dosen)
    }
  },
  {
    accessorKey: 'nama_mk_genap',
    header: 'Mata Kuliah',
    cell: ({ row }) => {
      if (row.original.isExtraRow || !row.original.nama_mk_genap) {
        return h('div', [
          h(UButton, {
            label: 'Tambah Data',
            icon: 'i-lucide-plus',
            color: 'success',
            class: 'text-sm',
            onClick: () => router.push(`/add?id_dosen=${row.original.id_dosen}`)
          })
        ])
      }
      return row.original.nama_mk_genap
    }
  },
  {
    accessorKey: 'kelas',
    header: 'Kelas',
    cell: ({ row }) => row.original.kelas
  },
  {
    id: 'actions',
    header: 'Actions',
    cell: ({ row }) => {
      return h('div', { class: 'flex gap-2 justify-center' },
        row.original.kelas === 'Tidak ada data'
          ? [
              h(UButton, {
                label: 'Tambah Data',
                icon: 'i-lucide-plus',
                color: 'success',
                class: 'text-sm',
                onClick: () => router.push(`/add?id_dosen=${row.original.id_dosen}`)
              })
            ] : row.original.isExtraRow === true ? [] : [
              h(UButton,
                {
                label: 'Hapus',
                icon: 'i-lucide-trash',
                color: 'error',
                class: 'text-sm',
                onClick: () => handleDelete(row.original.id_dosen, row.original.id_mk_genap)
              })
            ]
      )
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
        <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 p-4 ">
          <h1 class="text-2xl font-bold">Data Dosen</h1>
          <div class="flex gap-2 w-full sm:w-auto">
            <UInput
              v-model="searchNamaDosen"
              placeholder="Cari nama dosen..."
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
          </div>
        </div>

      <!-- Loading state -->
      <div v-if="pending" class="p-8 text-center text-gray-500">
        <UButton loading label="Loading..." icon="i-lucide-sync"/>
      </div>

      <!-- Error state -->
      <div v-else-if="error" class="p-4 bg-red-50 border border-red-200 text-red-600 rounded-md m-4">
        <p>Error: {{ error.message }}</p>
      </div>

      <!-- Tabel data -->
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