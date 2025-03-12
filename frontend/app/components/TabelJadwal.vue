<script setup>
import { ref, onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';
const router = useRouter();

const jadwalData = ref([]);
const pending = ref(true);
const error = ref(null);

const loadJadwalData = async () => {
    try {
        pending.value = true;
        const data = await import('./../output.json');
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
    <div class="container mx-auto max-w-screen-md p-6 border border-black rounded-lg shadow-lg bg-white">
      <!-- Header halaman -->
      <div class="flex justify-between items-center mb-6">
        <h1 class="text-2xl font-bold text-black">Tabel Jadwal</h1>
        <UButton
          label="Kembali"
          icon="i-lucide-arrow-left"
          color="info"
          @click="router.push('/')"
        />
      </div>
      <!-- Konten Jadwal -->
      <NCard  class="shadow-md rounded-lg overflow-hidden">
        <!-- Grouping berdasarkan hari -->
        <div v-for="day in allDays" :key="day" class="mb-6">
          <div class="p-4 bg-blue-500 border border-black">
            <h2 class="text-xl font-bold text-black">{{ day }}</h2>
          </div>
  
          <!-- Grouping berdasarkan ruangan dalam setiap hari -->
          <div v-for="(schedules, room) in jadwalByDayAndRoom[day]" :key="room" class="mb-4">
            <div class="p-4 bg-blue-300 border border-black">
              <h3 class="text-lg font-semibold text-black">Ruang: {{ room }}</h3>
            </div>
            <NTable class="w-full border-collapse">
              <thead class="bg-blue-500 text-black border border-gray-8800">
                <tr>
                  <th class="p-3 text-left">Jam Mulai</th>
                  <th class="p-3 text-left">Jam Selesai</th>
                  <th class="p-3 text-left">Mata Kuliah</th>
                  <th class="p-3 text-left">SKS</th>
                  <th class="p-3 text-left">Kelas</th>
                  <th class="p-3 text-left">Dosen</th>
                  <th class="p-3 text-left">Metode</th>
                </tr>
              </thead>
              <tbody class="text-black">
                <tr
                  v-for="(item, index) in schedules"
                  :key="index"
                  class="border border-gray-2800"
                >
                  <td
                    :class="item.status === 'code_red' ? 'bg-red-500 text-black' : ''"
                    class="p-3"
                  >
                    {{ item.jam_mulai || '-' }}
                  </td>
                  <td
                    :class="item.status === 'code_red' ? 'bg-red-500 text-black' : ''"
                    class="p-3"
                  >
                    {{ item.jam_selesai || '-' }}
                  </td>
                  <td
                    :class="item.status === 'code_red' ? 'bg-red-500 text-black' : ''"
                    class="p-3"
                  >
                    {{ item.mata_kuliah || '-' }}
                  </td>
                  <td
                    :class="item.status === 'code_red' ? 'bg-red-500 text-black' : ''"
                    class="p-3"
                  >
                    {{ item.sks || '-' }}
                  </td>
                  <td
                    :class="item.status === 'code_red' ? 'bg-red-500 text-black' : ''"
                    class="p-3"
                  >
                    {{ item.kelas || '-' }}
                  </td>
                  <td
                    :class="item.status === 'code_red' ? 'bg-red-500 text-black' : ''"
                    class="p-3"
                  >
                    {{ item.dosen || '-' }}
                  </td>
                  <td
                    :class="item.status === 'code_red' ? 'bg-red-500 text-black' : ''"
                    class="p-3"
                  >
                    {{ item.metode || '-' }}
                  </td>
                </tr>
              </tbody>
            </NTable>
          </div>
        </div>
      </NCard>
    </div>
  </template>
  