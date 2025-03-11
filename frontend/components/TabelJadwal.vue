<script setup>
import { ref, onMounted, computed } from 'vue';

// State untuk data jadwal
const jadwalData = ref([]);
const pending = ref(true);
const error = ref(null);

// Fungsi untuk membaca file JSON
const loadJadwalData = async () => {
    try {
        pending.value = true;
        // Menggunakan dynamic import untuk membaca file JSON
        const data = await import('../../data/output.json');
        jadwalData.value = data.default || [];
        console.log('Jadwal data loaded:', jadwalData.value);
    } catch (err) {
        error.value = err;
        console.error('Error loading jadwal data:', err);
    } finally {
        pending.value = false;
    }
};

// Computed property untuk menyusun data berdasarkan hari dan ruangan
const jadwalByDayAndRoom = computed(() => {
    const result = {};
    
    jadwalData.value.forEach(item => {
        const day = item.hari || 'Tidak Diketahui';
        const room = item.ruang || 'Tidak Diketahui';
        
        if (!result[day]) {
            result[day] = {};
        }
        
        if (!result[day][room]) {
            result[day][room] = [];
        }
        
        result[day][room].push(item);
    });
    
    // Sort each room's schedule by time
    for (const day in result) {
        for (const room in result[day]) {
            result[day][room].sort((a, b) => {
                const timeA = a.jam ? a.jam.split('-')[0].trim() : '';
                const timeB = b.jam ? b.jam.split('-')[0].trim() : '';
                return timeA.localeCompare(timeB);
            });
        }
    }
    
    return result;
});

// Get days sorted
const allDays = computed(() => Object.keys(jadwalByDayAndRoom.value));

// Load data saat komponen dimount
onMounted(() => {
    loadJadwalData();
});
</script>

<template>
        <h1>Tabel Jadwal</h1>

        <div v-if="pending">Loading jadwal...</div>
        <div v-else-if="error">Error: {{ error.message }}</div>
        <div v-else>
            <!-- Group by day -->
            <div v-for="day in allDays" :key="day" class="day-section">
                <div class="shadow">
                    <h2>{{ day }}</h2>
                
                    <!-- Group by room -->
                    <div v-for="(schedules, room) in jadwalByDayAndRoom[day]" :key="room" class="room-section">
                        <h3>Ruang: {{ room }}</h3>
                        
                        <table border="1">
                            <thead>
                                <tr>
                                    <th colspan="2">Jam</th>
                                    <th>Mata Kuliah</th>
                                    <th>SKS</th>
                                    <th>Kelas</th>
                                    <th>Dosen</th>
                                    <th>Metode</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr v-for="(item, index) in schedules" :key="index">
                                    <td :style="item.status === 'code_red' ? { backgroundColor: 'red', color: 'black' } : {}">
  {{ item.jam_mulai || '-' }}
</td>
<td :style="item.status === 'code_red' ? { backgroundColor: 'red', color: 'black' } : {}">
  {{ item.jam_selesai }}
</td>
<td :style="item.status === 'code_red' ? { backgroundColor: 'red', color: 'black' } : {}">
  {{ item.mata_kuliah || '-' }}
</td>
<td :style="item.status === 'code_red' ? { backgroundColor: 'red', color: 'black' } : {}">
  {{ item.sks || '-' }}
</td>
<td :style="item.status === 'code_red' ? { backgroundColor: 'red', color: 'black' } : {}">
  {{ item.kelas || '-' }}
</td>
<td :style="item.status === 'code_red' ? { backgroundColor: 'red', color: 'black' } : {}">
  {{ item.dosen || '-' }}
</td>
<td :style="item.status === 'code_red' ? { backgroundColor: 'red', color: 'black' } : {}">
  {{ item.metode || '-' }}
</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
</template>

<style scoped>
.day-section {
    margin-bottom: 30px;
}

.room-section {
    margin-bottom: 20px;
}

table {
    width: 100%;
    border-collapse: collapse;
}

th, td {
    padding: 8px;
    text-align: left;
}

.shadow{
    box-shadow: rgba(0, 0, 0, 0.3) 0px 19px 38px, rgba(0, 0, 0, 0.22) 0px 15px 12px;
    padding: 50px;
    border-radius: 50px;
}
</style>
