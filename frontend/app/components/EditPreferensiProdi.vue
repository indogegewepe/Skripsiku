<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import useApi from '~/composables/useApi'

const toast = useToast();
const router = useRouter();
const { fetchData, sendData } = useApi();

const preferensi = ref(null);

const daysOptions = ref([]);
const timeOptions = ref([]);

const selectedHari = ref([]);
const timeRange = ref([0, 24]);

function showToast(message: string) {
  toast.add({
    title: 'Terjadi kesalahan!',
    description: message,
    icon: 'i-lucide-error-circle',
    duration: 5000,
    color: 'error'
  });
}

const fetchHari = async () => {
  try {
    const data = await fetchData('hari');
    if (Array.isArray(data) && data.length > 0) {
      daysOptions.value = data.map((item: { id_hari: number; nama_hari: string }) => ({
        id_hari: item.id_hari,
        nama_hari: item.nama_hari
      }));
    } else {
      daysOptions.value = [];
      console.warn('Data hari kosong atau tidak berbentuk array');
    }
  } catch (error) {
    console.error('Error fetching hari:', error);
    showToast('Gagal mengambil data hari');
  }
};

const minTimeValue = ref(1);
const maxTimeValue = ref(12);

const fetchJam = async () => {
  try {
    const data = await fetchData('jam');
    if (Array.isArray(data) && data.length > 0) {
      timeOptions.value = data.map((item: { id_jam: number; jam_awal: string }) => ({
        id: item.id_jam,
        label: item.jam_awal
      }));

      // Update nilai minimal dan maksimal untuk slider dari data jam
      minTimeValue.value = timeOptions.value[0].id;
      maxTimeValue.value = timeOptions.value[timeOptions.value.length - 1].id;

      // Set nilai default slider jika belum ada preferensi
      if (!timeRange.value || timeRange.value.length !== 2) {
        timeRange.value = [minTimeValue.value, maxTimeValue.value];
      }
    } else {
      timeOptions.value = [];
      console.warn('Data jam kosong atau tidak berbentuk array, menggunakan nilai default');
    }
  } catch (error) {
    console.error('Error fetching jam:', error);
    showToast('Gagal mengambil data jam');
  }
};

const fetchPreferensi = async () => {
  try {
    // 1. Gunakan endpoint yang benar sesuai implementasi backend
    const data = await fetchData('prodi');
    
    // 2. Ambil ID secara dinamis (contoh menggunakan reactive variable)
    const targetId = 1; // Ganti dengan sumber ID yang sesuai
    
    // 3. Cari data yang sesuai (asumsi data berupa array)
    const preferensiData = data.find(
      (item: { id: number }) => item.id === targetId
    );

    if (preferensiData) {
      // 4. Handle data hari: pastikan selalu berupa array dan unique
      selectedHari.value = Array.isArray(preferensiData.hari)
        ? [...new Set(preferensiData.hari)]
        : [];

      // 5. Handle nilai default untuk waktu
      timeRange.value = [
        preferensiData.jam_mulai_id || minTimeValue.value,
        preferensiData.jam_selesai_id || maxTimeValue.value
      ];

      // 6. Simpan data lengkap jika diperlukan
      preferensi.value = preferensiData;
    } else {
      // 7. Reset state jika tidak ada data
      preferensi.value = null;
      selectedHari.value = [];
      timeRange.value = [minTimeValue.value, maxTimeValue.value];
    }
  } catch (error) {
    console.error('Gagal mengambil preferensi:', error);
    toast.add({
      title: 'Error!',
      description: 'Gagal memuat data preferensi',
      color: 'error',
      icon: 'i-lucide-alert-triangle'
    });
  }
};

// Fungsi pembantu untuk mendapatkan label jam berdasarkan ID
const getTimeLabel = (id: number) => {
  const timeSlot = timeOptions.value.find(time => time.id === id);
  return timeSlot ? timeSlot.label : `Jam ${id}`;
};

onMounted(() => {
  fetchPreferensi();
  fetchHari();
  fetchJam();
});

const savePreferensi = async () => {
  const hariPayload =
    selectedHari.value.length === 0
      ? null
      : selectedHari.value.length === 1
      ? selectedHari.value[0]
      : selectedHari.value;

  const payload = {
    id: 1,
    hari: hariPayload,
    jam_mulai_id: timeRange.value ? timeRange.value[0] : null,
    jam_selesai_id: timeRange.value ? timeRange.value[1] : null
  };

  try {
    await sendData('prodi', 'PUT', payload);
    
    toast.add({
      title: 'Berhasil!',
      description: 'Preferensi berhasil diperbarui.',
      icon: 'i-lucide-check-circle',
      duration: 5000,
      color: 'success'
    });
  } catch (error) {
    console.error('Error:', error);
    toast.add({
      title: 'Gagal!',
      description: `Gagal update: ${error.message}`,
      icon: 'i-lucide-x-circle',
      color: 'error'
    });
  }
};
</script>

<template>
  <div class="min-h-screen flex flex-col items-center justify-center space-y-6">
    <UCard variant="soft" class="shadow-lg container max-w-4xl p-4">
      <h1 class="text-2xl font-semibold ">Edit Preferensi Program Studi</h1>
        <div class="mb-6">
          <h2 class="text-lg font-medium my-2">Preferensi Hari</h2>
          <div class="flex flex-wrap gap-3">
            <div v-for="option in daysOptions" :key="option.id_hari">
              <UCheckbox
                size="xl"
                :model-value="selectedHari.includes(option.id_hari)"
                :value="option.id_hari"
                :label="option.nama_hari"
                @update:model-value="checked => {
                  if (checked) {
                    selectedHari.push(option.id_hari);
                  } else {
                    const index = selectedHari.indexOf(option.id_hari);
                    if (index > -1) {
                      selectedHari.splice(index, 1);
                    }
                  }
                }"
              />
            </div>
          </div>
        </div>

        <div>
          <h2 class="text-lg font-medium mb-2 ">Preferensi Waktu</h2>
          <USlider
            v-model="timeRange"
            size="xl"
            :min="minTimeValue"
            :max="maxTimeValue"
            :step="1"
            :range="true"
          />
          <div v-if="timeRange" class="mt-2 ">
            Dari jam: <strong>{{ getTimeLabel(timeRange[0]) }}</strong> sampai jam: <strong>{{ getTimeLabel(timeRange[1]) }}</strong>
          </div>
        </div>
        <div class="w-full max-w-4xl flex justify-between">
        <UButton
          type="button"
          color="success"
          label="Simpan"
          icon="i-lucide-save"
          @click="savePreferensi"
        />
        <UButton
          type="button"
          label="Kembali"
          color="error"
          icon="i-lucide-arrow-left"
          @click="router.push('/')"
        />
      </div>
    </UCard>
  </div>
</template>