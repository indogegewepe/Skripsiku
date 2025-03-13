<script setup>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import useApi from '~/composables/useApi';

const router = useRouter();
const { fetchData, sendData } = useApi();

// State untuk data, loading, dan error
const dataDosenList = ref([]);
const pending = ref(true);
const error = ref(null);

// Fungsi untuk mengambil data dosen
const fetchDosenData = async () => {
  try {
    pending.value = true;
    const response = await fetchData(`data_dosen?timestamp=${new Date().getTime()}`);
    dataDosenList.value = response || [];
  } catch (err) {
    error.value = err;
    console.error('Error fetching data:', err);
  } finally {
    pending.value = false;
  }
};

// Fungsi untuk menghapus data dosen
const handleDelete = async (idDosen, idMkGenap) => {
  if (confirm('Apakah Anda yakin ingin menghapus data ini?')) {
    try {
      await sendData(`data_dosen/${idDosen}/${idMkGenap}`, 'DELETE');
      await fetchDosenData();
    } catch (err) {
      console.error('Error deleting data:', err);
    }
  }
};

onMounted(() => {
  fetchDosenData();
});
</script>

<template>
  <div class="container mx-auto p-6 border border-black rounded-lg shadow-lg bg-white">
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-2xl font-bold text-black">Data Dosen</h1>
      <UButton
          label="Kembali"
          icon="i-lucide-arrow-left"
          color="info"
          @click="router.push('/')"
      />
    </div>

    <div v-if="pending" class="flex justify-center items-center py-10">
      <NSpinner size="large" class="mr-3" />
      <span class="text-black">Memuat data...</span>
    </div>

    <div v-else-if="error" class="p-4 bg-red-100 border border-red-400 text-red-700 rounded-md">
      <p>Error: {{ error.message }}</p>
    </div>

    <NCard v-else class=" shadow-md rounded-lg overflow-hidden">
      <NTable class="w-full border-collapse">
        <thead class="bg-blue-500 text-black">
          <tr>
            <th class="p-3 text-left border border-black">No.</th>
            <th class="p-3 text-left border border-black">Nama Dosen</th>
            <th class="p-3 text-left border border-black">Nama Mata Kuliah</th>
            <th class="p-3 text-left border border-black">Kelas</th>
            <th class="p-3 text-center border border-black">Aksi</th>
          </tr>
        </thead>
        <tbody class="text-black">
          <template v-for="(dosen, i) in dataDosenList" :key="i">
            <tr v-for="(mk, index) in dosen.mata_kuliah || []" :key="`mk-${i}-${index}`">
              <td
                v-if="index === 0"
                :rowspan="dosen.mata_kuliah?.length || 1"
                class="p-3 border border-black"
              >
                {{ dosen.id_dosen }}
              </td>
              <td
                v-if="index === 0"
                :rowspan="dosen.mata_kuliah?.length || 1"
                class="p-3 border border-black"
              >
                {{ dosen.nama_dosen }}
              </td>
              <td class="p-3 border border-black">
                {{ mk?.nama_mk_genap || 'Tidak ada data' }}
              </td>
              <td class="p-3 border border-black">
                {{ mk?.kelas || 'Tidak ada data' }}
              </td>
              <td class="p-3 text-center border border-black">
                <UButton
                  label="Hapus"
                  icon="i-lucide-trash"
                  color="error"
                  @click="handleDelete(dosen.id_dosen, mk.id_mk_genap)"
                />
              </td>
            </tr>
            <tr v-if="dosen.mata_kuliah?.length === 0">
              <td class="p-3 border border-black">{{ dosen.id_dosen }}</td>
              <td class="p-3 border border-black">{{ dosen.nama_dosen }}</td>
              <td colspan="2" class="p-3 text-center border border-black">
                Tidak ada mata kuliah
              </td>
              <td class="p-3 text-center border border-black">
                <UButton
                  label="Tambah"
                  icon="i-lucide-plus"
                  color="primary"
                  @click="router.push(`/add?id_dosen=${dosen.id_dosen}`)"
                />
              </td>
            </tr>
          </template>
        </tbody>
      </NTable>
    </NCard>
  </div>
</template>

