<script setup>
import { ref, onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';

const router = useRouter();

// State untuk data, loading, dan error
const jadwalData = ref([]);
const pending = ref(true);
const error = ref(null);

// State untuk filtering, sorting, dan pagination
const filterText = ref('');
const sortKey = ref(''); // misalnya: 'hari', 'ruang', 'mata_kuliah', 'jam_mulai'
const sortOrder = ref('asc'); // 'asc' atau 'desc'
const currentPage = ref(0);
const pageSize = ref(12);

// Fungsi untuk mengambil data dari file JSON secara asinkron
const loadJadwalData = async () => {
  try {
    pending.value = true;
    const data = await import('./../../output.json');
    // Misal data.default adalah array objek dengan banyak properti,
    // kita hanya ambil key yang diperlukan: hari, ruang, jam_mulai, jam_selesai, mata_kuliah, sks, kelas, dosen, metode
    jadwalData.value = (data.default || []).map(item => ({
      dosen: item.dosen,
      kelas: item.kelas,
      mata_kuliah: item.mata_kuliah,
      sks: item.sks,
      hari: item.hari,
      ruang: item.ruang,
      jam_mulai: item.jam_mulai,
      jam_selesai: item.jam_selesai,
      metode: item.metode
    }));
    console.log('Jadwal data loaded:', jadwalData.value);
  } catch (err) {
    error.value = err;
    console.error('Error loading jadwal data:', err);
  } finally {
    pending.value = false;
  }
};

// Memuat data saat komponen dimount
onMounted(() => {
  loadJadwalData();
});

// Computed property untuk filtering data (filter berdasarkan hari, ruang, atau mata kuliah)
const filteredData = computed(() => {
  if (!filterText.value) return jadwalData.value;
  return jadwalData.value.filter(item => {
    return (
      (item.hari && item.hari.toLowerCase().includes(filterText.value.toLowerCase())) ||
      (item.mata_kuliah && item.mata_kuliah.toLowerCase().includes(filterText.value.toLowerCase())) ||
      (item.dosen && item.dosen.toLowerCase().includes(filterText.value.toLowerCase()))
    );
  });
});

// Computed property untuk sorting data
const sortedData = computed(() => {
  const data = [...filteredData.value];
  if (sortKey.value) {
    data.sort((a, b) => {
      let valA = a[sortKey.value] || '';
      let valB = b[sortKey.value] || '';
      if (typeof valA === 'string') {
        valA = valA.toLowerCase();
        valB = valB.toLowerCase();
      }
      if (sortOrder.value === 'asc') {
        return valA > valB ? 1 : valA < valB ? -1 : 0;
      } else {
        return valA < valB ? 1 : valA > valB ? -1 : 0;
      }
    });
  }
  return data;
}); 
// Computed property untuk pagination (memotong data sesuai halaman)
const paginatedData = computed(() => {
  const start = currentPage.value * pageSize.value;
  return sortedData.value.slice(start, start + pageSize.value);
});

// Total halaman untuk pagination
const totalPages = computed(() => Math.ceil(sortedData.value.length / pageSize.value));
</script>

<template>
  <div class="container mx-auto p-6 border border-black rounded-lg shadow-lg bg-white">
    <!-- Header Halaman -->
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-2xl font-bold text-black">Tabel Jadwal</h1>
      <UButton
        label="Kembali"
        icon="i-lucide-arrow-left"
        color="error"
        @click="router.push('/')"
      />
    </div>

    <!-- Kontrol Filter -->
    <div class="mb-4">
      <input
        v-model="filterText"
        type="text"
        placeholder="Filter (dosen, mata kuliah, dan hari)"
        class="w-full p-2 text-black border border-gray-800 rounded"
      >
    </div>

    <!-- Kontrol Sorting -->
    <div class="flex items-center mb-4 space-x-2">
      <label for="sortKey" class="font-medium text-black">Sort By:</label>
      <select id="sortKey" v-model="sortKey" class="p-2 text-black border border-gray-800 rounded">
        <option value="">Default</option>
        <option value="hari">Hari</option>
        <option value="ruang">Ruang</option>
        <option value="mata_kuliah">Mata Kuliah</option>
        <option value="jam_mulai">Jam Mulai</option>
      </select>
      <select v-model="sortOrder" class="p-2 text-black border border-gray-800 rounded">
        <option value="asc">Asc</option>
        <option value="desc">Desc</option>
      </select>
    </div>

    <!-- Tampilan Loading atau Error -->
    <div v-if="pending" class="text-center py-4">
      Loading data...
    </div>
    <div v-else-if="error" class="text-center py-4 text-red-500">
      Error: {{ error.message || error }}
    </div>

    <!-- Tabel Data dengan Pagination menggunakan UTable -->
    <UCard v-else class="shadow-md rounded-lg overflow-hidden drop-shadow-lg">
      <UTable class="w-full border-collapse" :data="paginatedData"/>
      <div class="flex justify-between items-center p-4">
        <UButton
          label="Previous"
          :disabled="currentPage === 0"
          @click="currentPage = Math.max(currentPage - 1, 0)"
        />
        <span>Page {{ currentPage + 1 }} of {{ totalPages }}</span>
        <UButton
          label="Next"
          :disabled="currentPage + 1 >= totalPages"
          @click="currentPage = Math.min(currentPage + 1, totalPages - 1)"
        />
      </div>
    </UCard>

  </div>
</template>
