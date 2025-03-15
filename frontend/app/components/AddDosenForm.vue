<script setup>
import { ref, onMounted, watch } from 'vue';
import { useRouter } from 'vue-router';
import useApi from '~/composables/useApi';

// Router dan Route
const router = useRouter();

// Props
// eslint-disable-next-line vue/require-prop-types
const { idDosen } = defineProps(['idDosen']);

// State
const dosen = ref(null); // Data dosen
const mkList = ref([]); // Daftar mata kuliah
const selectedMk = ref(null); // Mata kuliah yang dipilih
const kelas = ref(''); // Kelas yang dihitung otomatis
const dataDosen = ref([]); // Data dosen dan mata kuliah dari endpoint /data_dosen

// Fetch data dosen
const fetchDosen = async () => {
  try {
    const data = await useApi().fetchData(`dosen/${idDosen}`);
    dosen.value = data;
  } catch (error) {
    console.error('Error fetching dosen:', error);
  }
};

// Fetch data mata kuliah
const fetchMk = async () => {
  try {
    const data = await useApi().fetchData('mk_genap');
    mkList.value = data || [];
  } catch (error) {
    console.error('Error fetching mata kuliah:', error);
  }
};

// Fetch data dosen dan mata kuliah
const fetchDataDosen = async () => {
  try {
    const data = await useApi().fetchData('tbl_data_dosen');
    dataDosen.value = data || [];
  } catch (error) {
    console.error('Error fetching data dosen:', error);
  }
};

// Hitung kelas otomatis
const calculateKelas = () => {
  console.log('Selected MK:', selectedMk.value);

  if (!selectedMk.value) {
    console.log('No selected MK, returning early.');
    return;
  }
  
  const kelasList = dataDosen.value
    .filter(item => item.id_mk_genap === selectedMk.value)
    .map(item => item.kelas);

  console.log('Kelas List:', kelasList);

  let nextKelas = 'A';
  while (kelasList.includes(nextKelas)) {
    nextKelas = String.fromCharCode(nextKelas.charCodeAt(0) + 1);
  }
  console.log('Next Kelas:', nextKelas);

  kelas.value = nextKelas;
};

// Handle submit form
const handleSubmit = async () => {
  if (!selectedMk.value || !kelas.value) {
    alert('Pilih mata kuliah terlebih dahulu!');
    return;
  }

  try {
    await useApi().sendData('data_dosen', 'POST', {
      id_dosen: idDosen,
      id_mk_genap: selectedMk.value,
      kelas: kelas.value
    });
    alert('Data berhasil ditambahkan!');
    router.push('/dosen');
  } catch (error) {
    console.error('Gagal menambahkan data:', error);
    alert('Terjadi kesalahan!');
  }
};

// Fetch data saat komponen dimuat
onMounted(async () => {
  await fetchDosen();
  await fetchMk();
  await fetchDataDosen();
});

// Hitung kelas otomatis saat mata kuliah dipilih
watch(selectedMk, calculateKelas);
</script>

<template>
  <div class="min-h-screen flex items-center justify-center">
    <div class="w-full max-w-screen-md  rounded-lg shadow-lg overflow-hidden bg-white">
      <div class="p-6 bg-blue-500">
        <h1 class="text-2xl font-bold text-black text-center">
          Tambah Mata Kuliah untuk <br>
          <strong>{{ dosen?.nama_dosen }}</strong>
        </h1>
      </div>

      <!-- Form -->
      <form class="p-6 space-y-4" @submit.prevent="handleSubmit">
        <div>
          <label for="mk" class="block text-black mb-2">Pilih Mata Kuliah:</label>
          <select
            id="mk"
            v-model="selectedMk"
            required
            class="w-full p-2 border border-gray-300 rounded text-black"
          >
            <option value="" disabled>Pilih mata kuliah</option>
            <option
              v-for="mk in mkList"
              :key="mk.id_mk_genap"
              :value="mk.id_mk_genap"
            >
              {{ mk.nama_mk_genap }} (SMT: {{ mk.smt }}, SKS: {{ mk.sks }})
            </option>
          </select>
        </div>

        <div>
          <label for="kelas" class="block text-black mb-2">Kelas:</label>
          <input
            id="kelas"
            :value="kelas"
            type="text"
            readonly
            class="w-full p-2 border border-gray-300 rounded text-black"
          >
        </div>

        <div class="flex justify-end space-x-4">
          <UButton 
            type="submit" 
            label="Submit" 
            icon="i-lucide-check"
            color="success" 
          />
          <UButton
            type="button"
            label="Kembali"
            icon="i-lucide-arrow-left"
            color="error"
            @click="router.push('/dosen')"
          />
        </div>
      </form>
    </div>
  </div>
</template>