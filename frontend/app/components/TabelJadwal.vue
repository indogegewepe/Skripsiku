<script setup>
import { ref, onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import useApi from '~/composables/useApi'
import ExcelJS from 'exceljs'
import { saveAs } from 'file-saver'

const router = useRouter();
const { fetchData } = useApi()
const dataJadwal = ref([])

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
      mata_kuliah: item.mata_kuliah,
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
  const keyValuePattern = /(\w+):\s*(.+)/g;

  const matches = [...search.matchAll(keyValuePattern)];

  if (matches.length > 0) {
    return jadwalData.value.filter(item => {
      return (
        item.hari.toLowerCase().includes(search) ||
        item.ruang.toLowerCase().includes(search) ||
        item.mata_kuliah.toLowerCase().includes(search) ||
        item.dosen.toLowerCase().includes(search) ||
        item.kelas.toLowerCase().includes(search) ||
        item.semester.toLowerCase().includes(search) ||
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
      item.semester,
      item.status
    ].join(' ').toLowerCase();
    return combinedText.includes(search);
  });
});

const sortedData = computed(() => {
  const data = [...filteredData.value];
  if (!sortKey.value) return data;

  return data.sort((a, b) => {
    const valA = typeof a[sortKey.value] === 'string' ? a[sortKey.value].trim() : a[sortKey.value];
    const valB = typeof b[sortKey.value] === 'string' ? b[sortKey.value].trim() : b[sortKey.value];

    if (!valA && !valB) return 0;
    if (!valA) return 1;
    if (!valB) return -1;

    if (sortKey.value === 'sks') {
      return sortOrder.value === 'asc'
        ? Number(valA) - Number(valB)
        : Number(valB) - Number(valA);
    }

    if (sortKey.value === 'semester') {
      function convertSemester(val) {
        return Number(val) || 0;
      }
      const aVal = convertSemester(valA);
      const bVal = convertSemester(valB);
      return sortOrder.value === 'asc' ? aVal - bVal : bVal - aVal;
    }

    // Default string sort
    return sortOrder.value === 'asc'
      ? String(valA).localeCompare(String(valB), undefined, { numeric: true })
      : String(valB).localeCompare(String(valA), undefined, { numeric: true });
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
  { value: 'mata_kuliah', label: 'Mata Kuliah' },
  { value: 'semester', label: 'Semester' },
  { value: 'status', label: 'Status' }
];

onMounted(async () => {
  loadJadwalData();
  dataJadwal.value = await fetchData('schedule')
});

async function exportPivotToExcel() {
  const semesters = [...new Set(dataJadwal.value.map(item => item.semester))]

  const workbook = new ExcelJS.Workbook()

  for (const semester of semesters) {
    const filteredData = dataJadwal.value.filter(item => item.semester === semester)

    const days = [...new Set(filteredData.map(item => item.hari))]
    const rooms = [...new Set(filteredData.map(item => item.ruang))]
    const slots = [...new Set(filteredData.map(item => item.jam_mulai + ' - ' + item.jam_selesai))]

    const worksheet = workbook.addWorksheet(`Semester ${semester}`)

    // Baris Header 1: Hari (merge)
    const headerRow1 = [""]
    for (const _day of days) {
      headerRow1.push(_day)
      for (let i = 1; i < rooms.length; i++) headerRow1.push("")
      headerRow1.push("")
    }
    worksheet.addRow(headerRow1)

    // Merge header hari
    let colOffset = 2
    for (const _day of days) {
      worksheet.mergeCells(1, colOffset, 1, colOffset + rooms.length - 1)
      colOffset += rooms.length + 1
    }

    // Baris Header 2: Ruang
    const headerRow2 = [""]
    for (const _day of days) {
      headerRow2.push(...rooms)
      headerRow2.push("")
    }
    worksheet.addRow(headerRow2)

    // Gaya untuk Header
    const headerRows = [worksheet.getRow(1), worksheet.getRow(2)]
    headerRows.forEach(row => {
      row.height = 20
      row.eachCell(cell => {
        cell.font = { bold: true }
        cell.alignment = { vertical: 'middle', horizontal: 'center' }
        cell.fill = {
          type: 'pattern',
          pattern: 'solid',
          fgColor: { argb: 'FFBFBFBF' }
        }
        cell.border = {
          top: { style: 'thin' },
          left: { style: 'thin' },
          bottom: { style: 'thin' },
          right: { style: 'thin' }
        }
      })
    })

    // Baris Data
    slots.forEach((slot) => {
      const row = [slot]
      const matchMap = {}
      let colIndex = 1

      for (const day of days) {
        for (const room of rooms) {
          const result = findJadwalFiltered(filteredData, day, slot, room)
          row.push(result.display)
          matchMap[colIndex + 1] = result.status
          colIndex++
        }
        row.push("")
        colIndex++
      }

      const addedRow = worksheet.addRow(row)

      addedRow.eachCell((cell, colNumber) => {
        const status = matchMap[colNumber]

        if (status) {
          cell.fill = {
            type: 'pattern',
            pattern: 'solid',
            fgColor: { argb: getStatusColor(status) }
          }
        }

        cell.border = {
          top: { style: 'thin' },
          left: { style: 'thin' },
          bottom: { style: 'thin' },
          right: { style: 'thin' }
        }

        cell.alignment = { vertical: 'middle', horizontal: 'center', wrapText: true }
      })
    })
  }

  // Simpan
  const buffer = await workbook.xlsx.writeBuffer()
  saveAs(new Blob([buffer]), 'jadwal_pivot_per_semester.xlsx')
}

// Fungsi cari jadwal pada data terfilter
function findJadwalFiltered(data, day, slot, room) {
  const [mulai, selesai] = slot.split(' - ').map(s => s.trim())
  const match = data.find(item =>
    item.hari === day &&
    item.ruang === room &&
    item.jam_mulai === mulai &&
    item.jam_selesai === selesai
  )
  if (match) {
    const parts = [match.mata_kuliah, match.kelas, match.dosen].filter(Boolean)
    return {
      display: parts.join('/'),
      status: match.status || null
    }
  }
  return { display: '', status: null }
}


// Fungsi warna berdasarkan status
function getStatusColor(status) {
  switch (status.toLowerCase()) {
    case 'red': return 'FFFFC7CE' // merah muda
    case 'yellow': return 'FFFFFF99' // kuning
    default: return 'FFEEEEEE'
  }
}
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
      <UTable :data="paginatedData">
        <template #status-cell="{ getValue, row }">
          <td
            class="px-2 py-1 rounded"
            :class="{
              'bg-red-500 text-black': getValue(row) === 'red',
              'bg-yellow-500 text-black': getValue(row) === 'yellow'
            }"
          >
            {{ getValue(row) === 'red' ? 'Hard' : getValue(row) === 'yellow' ? 'Soft' : getValue(row) }}
          </td>
        </template>
      </UTable>

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