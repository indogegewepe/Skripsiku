<script setup>
import { ref, onMounted } from 'vue'
import useApi from '~/composables/useApi'
import ExcelJS from 'exceljs'
import { saveAs } from 'file-saver'

const dataJadwal = ref([])
const { fetchData } = useApi()

onMounted(async () => {
  dataJadwal.value = await fetchData('schedule')
})

async function exportPivotToExcel() {
  const days = [...new Set(dataJadwal.value.map(item => item.hari))]
  const rooms = [...new Set(dataJadwal.value.map(item => item.ruang))]
  const slots = [...new Set(dataJadwal.value.map(item => item.jam_mulai + ' - ' + item.jam_selesai))]

  const workbook = new ExcelJS.Workbook()
  const worksheet = workbook.addWorksheet('JadwalPivot')

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
  let colIndex = 1 // Mulai dari 1 karena kolom pertama untuk slot

  for (const day of days) {
    for (const room of rooms) {
      const result = findJadwal(day, slot, room)
      row.push(result.display)
      matchMap[colIndex + 1] = result.status // +1 karena array 0-based tapi ExcelJS kolom 1-based
      colIndex++
    }
    row.push("") // kolom kosong separator antar hari
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


  // Simpan
  const buffer = await workbook.xlsx.writeBuffer()
  saveAs(new Blob([buffer]), 'jadwal_pivot.xlsx')
}

// Fungsi cari jadwal (dan status)
function findJadwal(day, slot, room) {
  const [mulai, selesai] = slot.split(' - ').map(s => s.trim())
  const match = dataJadwal.value.find(item =>
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
  <div>
    <UButton color="success" trailing-icon="i-lucide-file-spreadsheet" label="Export to Excel" @click="exportPivotToExcel" />
  </div>
</template>
