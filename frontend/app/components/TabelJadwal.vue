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
const sortKey = ref('default'); // misalnya: 'hari', 'ruang', 'mata_kuliah', 'dosen'
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
      item.hari.toLowerCase().includes(filterText.value.toLowerCase()) ||
      item.ruang.toLowerCase().includes(filterText.value.toLowerCase()) ||
      item.mata_kuliah.toLowerCase().includes(filterText.value.toLowerCase() ||
      item.dosen.toLowerCase().includes(filterText.value.toLowerCase())
      )
    );
  });
});

// Computed property untuk sorting data
const sortedData = computed(() => {
  const data = [...filteredData.value];
  if (sortKey.value) {
    data.sort((a, b) => {
      let valA = a[sortKey.value];
      let valB = b[sortKey.value];
      
      // Handle sorting numerik untuk SKS
      if (sortKey.value === 'sks') {
        valA = Number(valA);
        valB = Number(valB);
      } else if (typeof valA === 'string') {
        valA = valA.toLowerCase();
        valB = valB.toLowerCase();
      }

      return sortOrder.value === 'asc' 
        ? valA > valB ? 1 : -1 
        : valA < valB ? 1 : -1;
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

const sortKeyOptions = [
  { value: null, label: 'Default' },  // Gunakan null sebagai value default
  { value: 'hari', label: 'Hari' },
  { value: 'ruang', label: 'Ruang' },
  { value: 'mata_kuliah', label: 'Mata Kuliah' },
  { value: 'dosen', label: 'Dosen' }
];

const sortOrderOptions = [
  { value: 'asc', label: 'Asc' },
  { value: 'desc', label: 'Desc' }
];
</script>

<template>
  <div class="container mx-auto p-6 border border-black rounded-lg shadow-lg bg-white">
    <!-- Header Halaman -->
    <div class="flex justify-between items-center mb-4">
      <h1 class="text-2xl font-bold text-black">Tabel Jadwal</h1>
      <UButton
        label="Kembali"
        icon="i-lucide-arrow-left"
        color="error"
        @click="router.push('/')"
      />
    </div>

    <!-- Kontrol Filter -->
    <div class="mb-2">
      <UInput
        v-model="filterText"
        type="text"
        placeholder="Filter (dosen, mata kuliah, dan hari)"
        class="w-full h-12"
      />
    </div>

    <!-- Kontrol Sorting (Diperbaiki) -->
    <div class="flex flex-col sm:flex-row items-start sm:items-center mb-4 space-y-2 sm:space-y-0 sm:space-x-4">
      <label for="sortKey" class="font-medium text-black">Urut Berdasarkan:</label>
      <USelect
        id="sortKey"
        v-model="sortKey"
        :items="sortKeyOptions"
        class="w-32"
        placeholder="Default"
      />
      <USelect
        id="sortOrder"
        v-model="sortOrder"
        :items="sortOrderOptions"
        class="w-24"
        placeholder="Asc/Desc"
      />
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
      <UTable class="w-full border-collapse" :data="paginatedData" />
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
