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
const UAlert = resolveComponent('UAlert')

// State data
const dataDosenList = ref([])
const pending = ref(true)
const error = ref(null)
const searchNamaDosen = ref('')

const toast = useToast()

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

function ToastBerhasil(msg) {
  toast.add({
    title: 'Berhasil!',
    description: msg,
    icon: 'i-lucide-check-circle',
    duration: 5000,
    color: 'success'
  })
}

function ToastErr(err) {
  toast.add({
    title: 'Terjadi kesalahan!',
    description: err,
    icon: 'i-lucide-error-circle',
    duration: 5000,
    color: 'error'
  })
}

const showConfirm = ref(false);
const confirmPromiseResolve = ref(null);

const openConfirmDialog = () => {
  showConfirm.value = true;
  return new Promise((resolve) => {
    confirmPromiseResolve.value = resolve;
  });
};

const confirmDialog = () => {
  showConfirm.value = false;
  if (confirmPromiseResolve.value) confirmPromiseResolve.value(true);
};

const cancelDialog = () => {
  showConfirm.value = false;
  if (confirmPromiseResolve.value) confirmPromiseResolve.value(false);
};

const handleDelete = async (idDosen, idMkGenap, kelas) => {
  const confirmed = await openConfirmDialog();
  if (confirmed) {
    try {
      const endpoint = `data_dosen/${idDosen}/${idMkGenap}/${kelas}`;
      await sendData(endpoint, 'DELETE');
      await fetchDosenData();
      ToastBerhasil('Data berhasil dihapus');
    } catch (err) {
      ToastErr('Error deleting data: ' + err)
    }
  }
};

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
    cell: ({ table, row }) => {
      if (row.original.isExtraRow || row.original.rowSpan === 0) return ''

      const visibleRows = table.getRowModel().rows
        .filter(r => !(r.original.isExtraRow || r.original.rowSpan === 0))

      const index = visibleRows.findIndex(r => r.original.id_dosen === row.original.id_dosen)
      return index >= 0 ? index + 1 : ''
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
                onClick: () => handleDelete(row.original.id_dosen, row.original.id_mk_genap, row.original.kelas)
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
          <h1 class="text-2xl font-bold text-nowrap">Data Dosen</h1>
          <div class="flex gap-2 w-full justify-end">
            <UInput
              v-model="searchNamaDosen"
              placeholder="Cari nama dosen..."
              size="lg"
              class="flex-grow lg:flex-none"
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
      <UCard v-else variant="subtle" class="shadow-lg">
        <UTable
          :column-pinning="{ right: ['actions'] }"
          :data="tableData"
          :columns="columns"
          :row-class="index => index % 2 === 0 ? 'bg-white' : 'bg-gray-50'"
        />
      </UCard>
    </UCard>
    <div v-if="showConfirm" class="fixed inset-0 flex items-center justify-center z-50">
      <UAlert
        title="Konfirmasi"
        description="Apakah Anda yakin ingin menghapus data ini?"
        color="warning"
        variant="subtle"
        class="w-2/3 backdrop-blur-md"
        :actions="[
          { label: 'Batal', onClick: cancelDialog, color: 'error' },
          { label: 'Konfirmasi', onClick: confirmDialog, color: 'success' }
        ]"
      />
    </div>
  </div>
</template>