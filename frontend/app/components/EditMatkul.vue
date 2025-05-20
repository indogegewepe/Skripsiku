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

const dataMKGenapList = ref([])
const pending = ref(true)
const error = ref(null)
const searchMKGenap = ref('')

const toast = useToast()

const fetchMKGenapData = async () => {
  try {
    pending.value = true
    const response = await fetchData(`mk_genap`)
    dataMKGenapList.value = response || []
  } catch (err) {
    error.value = err
    console.error('Error fetching data:', err)
  } finally {
    pending.value = false
  }
}

const form = ref({
  id_mk_genap: '',
  nama_mk_genap: '',
  smt: '',
  sks: '',
  sifat: '',
  kategori: '',
  metode: ''
})

async function handleSubmit() {
  try {
    const idMK = parseInt(form.value.id_mk_genap)
    if (
      isNaN(idMK) || !form.value.nama_mk_genap ||
      isNaN(parseInt(form.value.smt)) || isNaN(parseInt(form.value.sks))
    ) {
      showToastError('Data tidak lengkap', 'Pastikan semua kolom mata kuliah terisi dengan benar')
      return
    }

    const exists = dataMKGenapList.value.some(mk => mk.id_mk_genap === idMK)
    if (exists) {
      showToastError('ID Mata Kuliah sudah terdaftar', 'Tidak dapat menyimpan data dengan ID yang sama')
      return
    }

    const payload = {
      id_mk_genap: idMK,
      nama_mk_genap: form.value.nama_mk_genap,
      smt: parseInt(form.value.smt),
      sks: parseInt(form.value.sks),
      sifat: form.value.sifat,
      kategori: form.value.kategori,
      metode: form.value.metode
    }

    await sendData('mk_genap', 'POST', payload)
    await fetchMKGenapData()
    ToastBerhasil('Mata kuliah berhasil disimpan')
    form.value = {
      id_mk_genap: '',
      nama_mk_genap: '',
      smt: '',
      sks: '',
      sifat: '',
      kategori: '',
      metode: ''
    }
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

function showToastError(err) {
  toast.add({
    title: 'Uh oh! Something went wrong.',
    description: `Error deleting data: ${err}`,
    icon: 'i-lucide-error-circle',
    duration: 5000,
    color: 'error'
  })
}

const handleDelete = async (idMkGenap) => {
  if (confirm('Apakah Anda yakin ingin menghapus data ini?')) {
    try {
      const endpoint = `mk_genap/${idMkGenap}`;
      await sendData(endpoint, 'DELETE');
      await fetchMKGenapData();
      ToastBerhasil('Mata kuliah berhasil dihapus') 
    } catch (err) {
      showToastError(err)
    }
  }
}

const filteredSortedData = computed(() => {
  const searchTerm = searchMKGenap.value.toLowerCase()
  return dataMKGenapList.value
    .filter(mk => mk.nama_mk_genap.toLowerCase().includes(searchTerm))
    .sort((a, b) => a.nama_mk_genap.localeCompare(b.nama_mk_genap))
})

const tableData = computed(() => {
  try {
    const data = []
    filteredSortedData.value.forEach((mk) => {
      const baseData = { 
        id_mk: mk.id_mk_genap,
        nama_mk: mk.nama_mk_genap,
        smt: mk.smt,
        sks: mk.sks,
        sifat: mk.sifat,
        metode: mk.metode,
        kategori: mk.kategori
      }
      data.push(baseData)
    })
    return data
  } catch (error) {
    showToastError(error)
    return []
  }
});

const columns = [
  {
    accessorKey: 'id_mk',
    header: 'ID',
    cell: ({ row }) => {
      return h('span', row.original.id_mk)
    }
  },
  {
    accessorKey: 'nama_mk',
    header: 'Nama Mata Kuliah',
    cell: ({ row }) => {
      return h('span', row.original.nama_mk)
    }
  },
  {
    accessorKey: 'smt',
    header: 'Semester',
    cell: ({ row }) => {
      return h('span', row.original.smt)
    }
  },
  {
    accessorKey: 'sks',
    header: 'SKS',
    cell: ({ row }) => {
      return h('span', row.original.sks)
    }
  },
  {
    accessorKey: 'sifat',
    header: 'Sifat',
    cell: ({ row }) => {
      return h('span', row.original.sifat)
    }
  },
  {
    accessorKey: 'kategori',
    header: 'Kategori',
    cell: ({ row }) => {
      return h('span', row.original.kategori)
    }
  },
  {
    accessorKey: 'metode',
    header: 'Metode',
    cell: ({ row }) => {
      return h('span', row.original.metode)
    }
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
          onClick: () => router.push(`/diredit/mk${row.original.id_mk}`)
        }),
        h(UButton, {
          label: 'Hapus',
          color: 'error',
          size: 'lg',
          icon: 'i-lucide-trash',
          onClick: () => handleDelete(row.original.id_mk)
        })
      ])
    },
    pin: 'right'
  }
]

onMounted(() => {
  fetchMKGenapData()
})
const metode = ref(['Online', 'Offline'])
const sifat = ref(['Wajib', 'Pilihan'])
const kategori = ref(['-', 'Sistem Cerdas', 'Relata'])
</script>

<template>
  <div class="container mx-auto p-4 lg:p-6">
    <UCard variant="soft" class="shadow-lg">
        <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 p-4 ">
          <h1 class="text-2xl font-bold">Data Mata Kuliah</h1>
          <div class="flex gap-2 w-full sm:w-auto">
            <UInput
              v-model="searchMKGenap"
              placeholder="Cari mata kuliah..."
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
              title="Tambah Mata Kuliah"
              :close="{
                color: 'error',
                class: 'rounded-md'
              }"
              >
              <UButton label="Tambah Mata Kuliah" icon="i-lucide-plus" color="success"/>
              <template #body>
                <form class="space-y-4" @submit.prevent="handleSubmit">
                    <label for="id_mk_genap">ID Mata Kuliah: </label>
                    <UInput
                      id="id_mk_genap"
                      v-model="form.id_mk_genap"
                      label="ID Mata Kuliah"
                      type="number"
                      class="w-full"
                      size="lg"
                      placeholder="Masukkan ID Mata Kuliah"
                      required
                    />
                    <label for="nama_mk_genap">Nama Mata Kuliah: </label>
                    <UInput
                      id="nama_mk_genap"
                      v-model="form.nama_mk_genap"
                      label="Nama Mata Kuliah"
                      class="w-full"
                      size="lg"
                      placeholder="Masukkan Nama Mata Kuliah"
                      required
                    />
                    <label for="smt">Semester : </label>
                    <UInput
                      id="smt"
                      v-model="form.smt"
                      label="Semester"
                      type="number"
                      class="w-full"
                      size="lg"
                      placeholder="Masukkan Semester"
                      required
                    />
                    <label for="sks">SKS : </label>
                    <UInput
                      id="sks"
                      v-model="form.sks"
                      label="SKS"
                      type="number"
                      class="w-full"
                      size="lg"
                      placeholder="Masukkan jumlah SKS"
                      required
                    />
                    <label for="sifat">Sifat : </label>
                    <USelect
                      id="sifat"
                      v-model="form.sifat"
                      label="Sifat"
                      :items="sifat"
                      class="w-full"
                      size="lg"
                      placeholder="Masukkan sifat"
                      required
                    />
                    <label for="kategori">Kategori : </label>
                    <USelect
                      id="kategori"
                      v-model="form.kategori"
                      label="Kategori"
                      :items="kategori"
                      class="w-full"
                      size="lg"
                      placeholder="Masukkan kategori"
                      required
                    />
                    <label for="metode">Metode : </label>
                    <USelect
                      id="metode"
                      v-model="form.metode"
                      label="Metode"
                      :items="metode"
                      class="w-full"
                      size="lg"
                      placeholder="Masukkan metode"
                      required
                    />
                  <div class="flex justify-end">
                    <UButton type="submit" label="Simpan" icon="i-lucide-save" color="primary" />
                  </div>
                </form>
              </template>
            </UModal>

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