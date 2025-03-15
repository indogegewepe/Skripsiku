<script setup>
import { ref, onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import useApi from '~/composables/useApi'
const router = useRouter();
const { fetchData } = useApi()

// State untuk data, loading, dan error
const jadwalData = ref([]);
const pending = ref(true);
const error = ref(null);

// State untuk filtering, sorting, dan pagination
const filterText = ref('');
const sortKey = ref(null);
const sortOrder = ref('asc'); // 'asc' atau 'desc'
const currentPage = ref(0);
const pageSize = ref(12);

// Fungsi untuk mengambil data dari file JSON secara asinkron
const loadJadwalData = async () => {
  try {
    pending.value = true;
    const data = await fetchData('schedule');
    jadwalData.value = (data || []).map(item => ({
      dosen: item.dosen,
      kelas: item.kelas,
      "Mata Kuliah": item.mata_kuliah,
      sks: item.sks,
      hari: item.hari,
      ruang: item.ruang,
      "Jam Mulai": item.jam_mulai,
      "Jam Selesai": item.jam_selesai,
      metode: item.metode,
      status: item.status
    }));
  } catch (err) {
    error.value = err;
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
  
  const search = filterText.value.toLowerCase().trim();
  const keyValuePattern = /(\w+):\s*(.+)/g; // Pola pencarian key-value yang mendukung multi-kriteria

  const matches = [...search.matchAll(keyValuePattern)];

  if (matches.length > 0) {
    return jadwalData.value.filter(item => {
      return (
        item.hari.toLowerCase().includes(search) ||
        item.ruang.toLowerCase().includes(search) ||
        item.mata_kuliah.toLowerCase().includes(search) ||
        item.dosen.toLowerCase().includes(search) ||
        item.kelas.toLowerCase().includes(search) ||
        item.status.toLowerCase().includes(search)
      );
    });
  }

  // Jika tidak sesuai format key-value, lakukan pencarian umum
  return jadwalData.value.filter(item => {
    const combinedText = [
      item.dosen,
      item.kelas,
      item.hari,
      item.ruang,
      item.mata_kuliah,
      item.status
    ].join(' ').toLowerCase();
    return combinedText.includes(search);
  });
});


// Computed property untuk sorting data
const sortedData = computed(() => {
  const data = [...filteredData.value];
  if (!sortKey.value) return data;

  return data.sort((a, b) => {
    let valA = a[sortKey.value]?.trim() || '';
    let valB = b[sortKey.value]?.trim() || '';

    // Menempatkan data kosong di akhir
    if (!valA && !valB) return 0;
    if (!valA) return 1;
    if (!valB) return -1;

    // Sorting numerik untuk SKS
    if (sortKey.value === 'sks') {
      valA = Number(valA);
      valB = Number(valB);
      return sortOrder.value === 'asc' ? valA - valB : valB - valA;
    }

    // Sorting string dengan metode yang lebih baik
    return sortOrder.value === 'asc'
      ? valA.localeCompare(valB, undefined, { numeric: true })
      : valB.localeCompare(valA, undefined, { numeric: true });
  });
});

const paginatedData = computed(() => {
  const start = currentPage.value * pageSize.value;
  return sortedData.value.slice(start, start + pageSize.value);
});

// Total halaman untuk pagination
const totalPages = computed(() => Math.ceil(sortedData.value.length / pageSize.value));

const sortKeyOptions = [
  { value: null, label: 'Default' },
  { value: 'dosen', label: 'Dosen' }, 
  { value: 'kelas', label: 'Kelas' },
  { value: 'hari', label: 'Hari' },
  { value: 'ruang', label: 'Ruang' },
  { value: 'Mata Kuliah', label: 'Mata Kuliah' },
  { value: 'status', label: 'Status' }
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
        @click="router.push('/proses')"
      />
    </div>

    <!-- Kontrol Filter -->
    <div class="mb-2">
      <UInput
        v-model="filterText"
        type="text"
        size="lg"
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
    </div>

    <!-- Tampilan Loading atau Error -->
    <div v-if="pending" class="text-center py-4 text-black">
      Loading data...
    </div>
    <div v-else-if="error" class="text-center py-4 text-red-500">
      Error: {{ error.message || error }}
    </div>

    <!-- Tabel Data dengan Pagination menggunakan UTable -->
    <UCard v-else class="shadow-md rounded-lg overflow-hidden drop-shadow-lg">
      <UTable class="w-full border-collapse" :data="paginatedData" />
      <template #row="{ row }">
        <tr>
          <td
            v-for="(value, key) in row"
            :key="key"
            class="p-2 border"
            :class="{
              'bg-red-500 text-black': row.status === 'code_red' && key !== 'status'
            }"
          >
            {{ value }}
          </td>
        </tr>
      </template>
      <div class="flex justify-between items-center p-4">
        <UButton
          label="Previous"
          color="success"
          :disabled="currentPage === 0"
          @click="currentPage = Math.max(currentPage - 1, 0)"
        />
        <span>Page {{ currentPage + 1 }} of {{ totalPages }}</span>
        <UButton
          label="Next"
          color="success"
          :disabled="currentPage + 1 >= totalPages"
          @click="currentPage = Math.min(currentPage + 1, totalPages - 1)"
        />
      </div>
    </UCard>
  </div>
</template>