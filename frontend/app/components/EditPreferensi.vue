<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue'
import { useRouter } from 'vue-router'
import useApi from '~/composables/useApi'

const toast = useToast();
const router = useRouter();
const { fetchData } = useApi();

const dosen = ref([]);
const dosenList = ref(null);
const preferensi = ref([]);
const hari = ref([]);
const jam = ref([]);

// Untuk range slider jam
const jamRange = ref([0, 0]);
const jamAwalIndex = computed(() => jamRange.value[0]);
const jamAkhirIndex = computed(() => jamRange.value[1]);

const jamAwal = computed(() => jam.value.length > 0 ? jam.value[jamAwalIndex.value] : null);
const jamAkhir = computed(() => jam.value.length > 0 ? jam.value[jamAkhirIndex.value] : null);

// Menyimpan hari yang dipilih dalam bentuk array
const selectedHari = ref<number[]>([]);

function showToast(message: string) {
  toast.add({
    title: 'Terjadi kesalahan!',
    description: message,
    icon: 'i-lucide-error-circle',
    duration: 5000,
    color: 'error'
  })
}

const fetchDosen = async () => {
  try {
    const data = await fetchData('data_dosen');
    dosen.value = (data || []).map((item: { id_dosen: number; nama_dosen: string }) => ({
      value: item.id_dosen,
      label: item.nama_dosen
    }));
  } catch (error) {
    console.error('Error fetching dosen:', error);
  }
};

const fetchPreferensi = async () => {
  try {
    const data = await fetchData('preferensi_dosen');
    const filtered = data.filter((item: { id_dosen: number }) => item.id_dosen === dosenList.value);
    preferensi.value = filtered.map((item: { type: string; value: string }) => ({
      type: item.type,
      value: item.value
    }));
  } catch (error) {
    console.error('Error fetching preferensi:', error);
    showToast(String(error));
  }
};

const fetchHari = async () => {
  try {
    const data = await fetchData('hari');
    hari.value = (data || []).map((item: { id_hari: number; nama_hari: string }) => ({
      value: item.id_hari,
      label: item.nama_hari
    }));
  } catch (error) {
    console.error('Error fetching hari:', error);
    showToast('Gagal memuat data hari');
  }
};

const fetchJam = async () => {
  try {
    const data = await fetchData('jam');
    jam.value = (data || []).map((item: { id_jam: number; jam_awal: string; jam_akhir: string }) => ({
      value: item.id_jam,
      label: `${item.jam_awal} - ${item.jam_akhir}`,
      jam_awal: item.jam_awal,
      jam_akhir: item.jam_akhir
    }));
    
    // Inisialisasi range default
    if (jam.value.length > 0) {
      jamRange.value = [0, jam.value.length - 1];
    }
  } catch (error) {
    console.error('Error fetching jam:', error);
    showToast('Gagal memuat data jam');
  }
};

const toggleHari = (hariId: number) => {
  const index = selectedHari.value.indexOf(hariId);
  if (index === -1) {
    selectedHari.value.push(hariId);
  } else {
    selectedHari.value.splice(index, 1);
  }
};

const isHariSelected = (hariId: number) => {
  return selectedHari.value.includes(hariId);
};

const savePreferensi = () => {
  try {
    if (!dosenList.value) {
      showToast('Pilih dosen terlebih dahulu');
      return;
    }
    
    if (selectedHari.value.length === 0) {
      showToast('Pilih minimal satu hari');
      return;
    }
    
    // Implementasi logika penyimpanan preferensi
    // Contoh data yang akan disimpan:
    const dataToSave = {
      dosen_id: dosenList.value,
      hari: selectedHari.value,
      jam_mulai: jamAwal.value?.value,
      jam_selesai: jamAkhir.value?.value,
      rentang_waktu: `${jamAwal.value?.jam_awal} - ${jamAkhir.value?.jam_akhir}`
    };
    
    console.log('Data to save:', dataToSave);
    
    toast.add({
      title: 'Berhasil!',
      description: 'Preferensi berhasil disimpan',
      icon: 'i-lucide-check-circle',
      duration: 5000,
      color: 'success'
    });
  } catch (error) {
    console.error('Error saving preferensi:', error);
    showToast('Gagal menyimpan preferensi');
  }
};

onMounted(() => {
  fetchDosen();
  fetchHari();
  fetchJam();
});

watch(dosenList, (newVal) => {
  if (newVal) {
    fetchPreferensi();
    // Reset pilihan ketika dosen berubah
    selectedHari.value = [];
    if (jam.value.length > 0) {
      jamRange.value = [0, jam.value.length - 1];
    }
  } else {
    preferensi.value = [];
  }
});
</script>

<template>
  <div class="min-h-screen flex flex-col items-center justify-center space-y-6">
    <UCard class="shadow-lg bg-white container max-w-4xl p-4" variant="soft">
      <h1 class="text-2xl font-semibold text-black">Edit Preferensi</h1>
      <USelect
        v-model="dosenList"
        :items="dosen"
        class="w-full mb-4"
        placeholder="Pilih Dosen"
      />
      
      <!-- Hari checklist section -->
      <div class="mt-4">
        <h2 class="text-lg font-medium mb-2">Pilih Hari</h2>
        <div v-if="hari.length === 0" class="flex justify-center py-4">
          <ULoader />
        </div>
        <div v-else class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2">
          <UCheckbox
            v-for="item in hari"
            :key="item.value"
            :label="item.label"
            :model-value="isHariSelected(item.value)"
            @update:model-value="toggleHari(item.value)"
            class="mb-2"
          />
        </div>
        <div v-if="selectedHari.length > 0" class="mt-2 text-sm text-gray-600">
          Hari terpilih: {{ selectedHari.length }} hari
        </div>
      </div>

      <!-- Jam range slider section -->
      <div class="mt-6">
        <h2 class="text-lg font-medium mb-2">Pilih Rentang Jam Mengajar</h2>
        
        <div v-if="jam.length === 0" class="flex justify-center py-4">
          <ULoader />
        </div>
        
        <div v-else>
          <div class="mb-3 bg-gray-50 p-3 rounded-md border">
            <div class="font-medium text-sm mb-1">Rentang waktu yang dipilih:</div>
            <div class="text-base text-primary">{{ jamAwal?.jam_awal }} - {{ jamAkhir?.jam_akhir }}</div>
          </div>
          
          <URangeSlider
            v-model="jamRange"
            :min="0"
            :max="jam.length - 1"
            :step="1"
            class="mb-4"
          />
          
          <div class="flex justify-between text-xs text-gray-500">
            <span>{{ jam.length > 0 ? jam[0].jam_awal : '' }}</span>
            <span>{{ jam.length > 0 ? jam[jam.length - 1].jam_akhir : '' }}</span>
          </div>
          
          <div class="mt-4 p-4 border rounded-md bg-gray-50">
            <p class="font-medium">Detail Rentang Jam:</p>
            <div class="grid grid-cols-2 gap-4 mt-1">
              <div>
                <p class="text-sm text-gray-600">Jam Mulai:</p>
                <p>{{ jamAwal?.jam_awal }} (ID: {{ jamAwal?.value }})</p>
              </div>
              <div>
                <p class="text-sm text-gray-600">Jam Selesai:</p>
                <p>{{ jamAkhir?.jam_akhir }} (ID: {{ jamAkhir?.value }})</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Preferred time slots section -->
      <div class="mt-6">
        <h2 class="text-lg font-medium mb-2">Preferensi Waktu yang Disimpan</h2>
        <div v-if="preferensi.length > 0" class="border rounded-md p-2">
          <UTable :rows="preferensi" :columns="[
            { key: 'type', label: 'Tipe' },
            { key: 'value', label: 'Nilai' }
          ]" />
        </div>
        <div v-else class="text-gray-500 italic">
          Belum ada preferensi waktu yang disimpan
        </div>
      </div>
    </UCard>

    <div class="w-full max-w-4xl">
      <div class="mt-4 flex justify-between">
        <UButton
          type="button"
          color="success"
          label="Simpan"
          @click="savePreferensi"
        />
        <UButton
          type="button"
          label="Kembali"
          color="error"
          @click="router.push('/')"
        />
      </div>
    </div>
  </div>
</template>