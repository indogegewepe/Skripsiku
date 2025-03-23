<script setup>
import { ref, onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import useApi from '~/composables/useApi'
import * as XLSX from 'xlsx';

const router = useRouter();
const { fetchData } = useApi()

// State untuk data, loading, dan error
const jadwalData = ref([]);
const pending = ref(true);
const error = ref(null);

// State untuk filtering, sorting, dan pagination
const filterText = ref('');
const sortKey = ref(null);
const sortOrder = ref('asc');
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
      semester: item.semester,
      hari: item.hari,
      ruang: item.ruang,
      "Jam Mulai": item.jam_mulai,
      "Jam Selesai": item.jam_selesai,
      metode: item.metode,
      status: item.status
    }));
    pending.value = false;
  } catch (err) {
    error.value = err;
  } finally {
    pending.value = false;
  }
};

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

const dataJadwal = ref([])

const fetchJadwalData = async () => {
  try {
    dataJadwal.value = await fetchData('schedule')
  } catch (error) {
    console.error('Gagal memuat data jadwal:', error)
  }
}

// Fungsi untuk mengekspor data ke Excel dalam bentuk pivot
function exportPivotToExcel() {
  // 1. Kumpulkan semua "hari" unik
  const days = [...new Set(dataJadwal.value.map(item => item.hari))]

  // 2. Kumpulkan semua "ruang" unik
  const rooms = [...new Set(dataJadwal.value.map(item => item.ruang))]

  // 3. Kumpulkan semua "slot waktu" unik (gabungan jam_mulai + jam_selesai)
  //    Misalnya format "07:00:00 - 07:50:00" atau "1. 07.00 - 07.50"
  const slots = [...new Set(
    dataJadwal.value.map(item => item.jam_mulai + ' - ' + item.jam_selesai)
  )]

  // 4. Siapkan array-of-arrays (AOA) untuk worksheet
  const wsData = []

  // -- Row 0: Header Hari (merge agar 1 kata "Senin" menutupi beberapa kolom "ruang") --
  const row0 = [];
  row0.push("");                  // Kolom kosong di kiri
  for (let i = 0; i < days.length; i++) {
    row0.push(days[i]);            // Nama hari
    // Isi rooms.length - 1 kolom kosong (untuk merge)
    for (let j = 1; j < rooms.length; j++) {
      row0.push("");
    }
    // Tambahkan 1 kolom kosong sebagai pemisah (separator)
    row0.push("");
  }
  wsData.push(row0);

  // -- Row 1: Sub-header Ruang --
  const row1 = [];
  row1.push("");
  for (let i = 0; i < days.length; i++) {
    row1.push(...rooms);
    // Setelah rooms, tambahkan 1 kolom kosong separator
    row1.push("");
  }
  wsData.push(row1);

  // -- Row 2 ke bawah: Timeslot + isian jadwal --
  // Satu baris per slot
  for (const slot of slots) {
    const row = [];
    // Kolom pertama = slot waktu (misalnya "07:00:00 - 07:50:00")
    row.push(slot);

    // Sekarang isi data pivot per hari+ruang, lalu kolom kosong
    for (const day of days) {
      // Tambahkan data untuk semua room
      for (const room of rooms) {
        const cellValue = findJadwal(day, slot, room);
        row.push(cellValue);
      }
      // Kolom kosong pemisah
      row.push("");
    }
    wsData.push(row);
  }

  // 5. Definisikan merges untuk Row 0 (Hari) 
  //    Masing-masing hari menutupi "rooms.length" kolom
  const merges = [];
    let offset = 1; // Mulai dari kolom 1 karena kolom 0 sudah dipakai sebagai kolom kosong
    for (let i = 0; i < days.length; i++) {
    merges.push({
        s: { r: 0, c: offset },
        e: { r: 0, c: offset + (rooms.length - 1) }
    });
    offset += (rooms.length + 1);
    }

  // 6. Buat worksheet dari AOA
  const ws = XLSX.utils.aoa_to_sheet(wsData)

  // Masukkan info merges
  ws['!merges'] = merges

  // 7. Buat workbook dan append worksheet
  const wb = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(wb, ws, 'JadwalPivot')

  // 8. Simpan file
  XLSX.writeFile(wb, 'jadwal_pivot.xlsx')
}

function findJadwal(day, slot, room) {
  // 1) Pisahkan slot jadi jam_mulai & jam_selesai
  //    Jika slot format "07:00:00 - 07:50:00", kita bisa split:
  const [mulai, selesai] = slot.split(' - ').map(s => s.trim())

  // 2) Filter dataJadwal sesuai:
  //    - item.hari === day
  //    - item.ruang === room
  //    - item.jam_mulai === mulai
  //    - item.jam_selesai === selesai
  const match = dataJadwal.value.find(item =>
    item.hari === day &&
    item.ruang === room &&
    item.jam_mulai === mulai &&
    item.jam_selesai === selesai
  )

  // 3) Jika ketemu, return string "MataKuliah/Kelas/Dosen"
  if (match) {
  // Ambil value yang tidak kosong saja
  const parts = [match.mata_kuliah, match.kelas, match.dosen].filter(Boolean);
  return parts.join('/');
}

  // 4) Jika tidak ada, kosongkan
  return ''
}

onMounted(() => {
  loadJadwalData();
  fetchJadwalData();
});
</script>

<template>
  <UCard class="container mx-auto rounded-lg shadow-lg" variant="soft">
    <div class="flex justify-between items-center mb-4">
      <h1 class="text-2xl font-bold ">Tabel Jadwal</h1>
      <UButton
        label="Kembali"
        icon="i-lucide-arrow-left"
        color="error"
        @click="router.push('/proses')"
      />
    </div>
    <div class="mb-2">
      <UInput
        v-model="filterText"
        type="text"
        color="success"
        icon="i-lucide-search"
        size="lg"
        placeholder="Filter by Dosen"
        class="w-full h-12"
      />
    </div>
    <div class="flex flex-col sm:flex-row items-start sm:items-center mb-4 space-y-2 sm:space-y-0 sm:space-x-4">
      <label for="sortKey" class="font-medium ">Urut Berdasarkan:</label>
      <USelect
        id="sortKey"
        v-model="sortKey"
        color="success"
        size="lg"
        :items="sortKeyOptions"
        class="w-32"
        placeholder="Default"
      />
      <UButton
        label="Export to Excel"
        color="success"
        trailing-icon="i-lucide-file-spreadsheet"
        size="lg"
        class="ml-auto"
        @click="exportPivotToExcel"
      />
    </div>
    <div v-if="pending" class="text-center py-4">
      Loading data...
    </div>
    <div v-else-if="error" class="text-center py-4 text-red-500">
      Error: {{ error.message || error }}
    </div>
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
          icon="i-lucide-arrow-left"
          :disabled="currentPage === 0"
          @click="currentPage = Math.max(currentPage - 1, 0)"
        />
        <span>Page {{ currentPage + 1 }} of {{ totalPages }}</span>
        <UButton
          label="Next"
          color="success"
          trailing-icon="i-lucide-arrow-right"
          :disabled="currentPage + 1 >= totalPages"
          @click="currentPage = Math.min(currentPage + 1, totalPages - 1)"
        />
      </div>
    </UCard>
  </UCard>
</template>