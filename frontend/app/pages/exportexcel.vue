<script setup>
import { ref, onMounted } from 'vue'
import useApi from '~/composables/useApi'
import * as XLSX from 'xlsx'

// State untuk menyimpan data jadwal
const dataJadwal = ref([])

// Ambil fungsi fetchData dari composable
const { fetchData } = useApi()

// Fungsi memuat data jadwal dari endpoint /schedule
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

// Fungsi untuk mencari data jadwal yang cocok di cell (hari, slot, ruang)
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

// Panggil fetch saat komponen dimuat
onMounted(() => {
  fetchJadwalData()
})
</script>

<template>
  <div>
    <UButton color="success" trailing-icon="i-lucide-file-spreadsheet" label="Export to Excel" @click="exportPivotToExcel" />
  </div>
</template>
