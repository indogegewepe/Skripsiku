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

// Fungsi untuk menghapus data
const handleDelete = async (idDosen, idMkGenap) => {
  if (confirm('Apakah Anda yakin ingin menghapus data ini?')) {
    try {
      await sendData(`data_dosen/${idDosen}/${idMkGenap}`, 'DELETE')
      window.location.reload()
    } catch (err) {
      console.error('Error deleting data:', err)
    }
  }
}

const filteredSortedData = computed(() => {
  const searchTerm = searchNamaDosen.value.toLowerCase()
  return dataDosenList.value
    .filter(dosen => dosen.nama_dosen.toLowerCase().includes(searchTerm))
    .sort((a, b) => a.nama_dosen.localeCompare(b.nama_dosen))
})

// Siapkan data untuk tabel
const tableData = computed(() => {
  const data = []
  filteredSortedData.value.forEach((dosen) => {
    const baseData = { 
      id_dosen: dosen.id_dosen,
      nama_dosen: dosen.nama_dosen
    }

    if (dosen.mata_kuliah && dosen.mata_kuliah.length > 0) {
      const courseCount = dosen.mata_kuliah.length
      // Buat baris untuk setiap mata kuliah
      const courseRows = dosen.mata_kuliah.map((mk, index) => ({
        ...baseData,
        id_mk_genap: mk.id_mk_genap,
        nama_mk_genap: mk.nama_mk_genap,
        kelas: mk.kelas,
        // Baris pertama mendapat rowspan untuk mencakup semua baris (mata kuliah + baris extra)
        rowSpan: index === 0 ? courseCount + 1 : 0,
        isExtraRow: false
      }))
      // Tambahkan baris extra untuk tombol "Tambah Data"
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
        rowSpan: 1,
        isExtraRow: false
      })
    }
  })
  return data
})

// Definisi kolom tabel
const columns = [
  {
    accessorKey: 'no',
    header: 'No.',
    width: 50,
    cell: ({ row }) => row.index + 1
  },
  {
    accessorKey: 'nama_dosen',
    header: 'Nama Dosen',
    class: 'font-semibold min-w-[200px]',
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
            color: 'primary',
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
    header: 'Aksi',
    width: 180,
    cell: ({ row }) => {
      return h('div', { class: 'flex gap-2' },
        row.original.kelas === 'Tidak ada data'
          ? [
              h(UButton, {
                label: 'Tambah Data',
                icon: 'i-lucide-plus',
                color: 'primary',
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
    }
  }
]

// Panggil fungsi ambil data saat komponen dimuat
onMounted(() => {
  fetchDosenData()
})
</script>


<template>
  <div class="container mx-auto p-4 lg:p-6">
    <UCard class="shadow-lg border-0">
      <template #header>
        <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 p-4">
          <h1 class="text-2xl font-bold">Data Pengajaran Dosen</h1>
          <div class="flex gap-2 w-full sm:w-auto">
            <UInput
              v-model="searchNamaDosen"
              placeholder="Cari nama dosen..."
              icon="i-lucide-search"
              class="flex-grow"
            />
            <UButton
              label="Kembali"
              icon="i-lucide-arrow-left"
              color="info"
              @click="router.push('/')"
            />
          </div>
        </div>
      </template>

      <!-- Loading state -->
      <div v-if="pending" class="p-8 text-center text-gray-500">
        <span>Memuat data...</span>
      </div>

      <!-- Error state -->
      <div v-else-if="error" class="p-4 bg-red-50 border border-red-200 text-red-600 rounded-md m-4">
        <p>Error: {{ error.message }}</p>
      </div>

      <!-- Tabel data -->
      <div v-else>
        <UTable 
          :data="tableData"
          :columns="columns"
          :th-class="'bg-gray-50 text-gray-700 font-semibold'"
          :td-class="'text-gray-600'"
          :row-class="index => index % 2 === 0 ? 'bg-white' : 'bg-gray-50'"
        />
      </div>
    </UCard>
  </div>
</template>
