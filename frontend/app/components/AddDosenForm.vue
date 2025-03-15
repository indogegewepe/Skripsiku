<script setup>
import { ref, onMounted, watch } from 'vue';
import { useRouter } from 'vue-router';
import useApi from '~/composables/useApi';

const router = useRouter();

const { idDosen } = defineProps({
  idDosen: {
    type: Number,
    required: true
  }
});

const dosen = ref(null); // Data dosen
const mklist = ref([]); // This will hold the array of items for the select
const selectedMk = ref(null);
const kelas = ref(''); // Kelas yang dihitung otomatis
const dataDosen = ref([]); // Data dosen dan mata kuliah dari endpoint /data_dosen

const toast = useToast();

// Fetch data dosen
const fetchDosen = async () => {
  try {
    const data = await useApi().fetchData(`dosen/${idDosen}`);
    dosen.value = data;
  } catch (error) {
    console.error('Error fetching dosen:', error);
  }
};

// Fetch data function
const fetchMk = async () => {
  try {
    const data = await useApi().fetchData('mk_genap');
    mklist.value = (data || []).map(item => ({
      value: item.id_mk_genap,
      label: item.nama_mk_genap
    }));
  } catch (error) {
    console.error('Error fetching mata kuliah:', error);
  }
};

// Rest of your code remains the same
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

function ToastBerhasil() {
  toast.add({
    title: 'Data berhasil ditambahkan',
    icon: 'i-lucide-check-circle',
    duration: 5000,
    color: 'success'
  })
}

function ToastMasukkanMataKuliah() {
  toast.add({
    title: 'Masukkan mata kuliah terlebih dahulu',
    icon: 'i-lucide-error-circle',
    duration: 5000,
    color: 'error'
  })
}

function ToastTerjadiKesalahan(err) {
  toast.add({
    title: 'Terjadi kesalahan!',
    description: `Matakuliah sudah ditambahkan sebelumnya \n${err}`,
    icon: 'i-lucide-error-circle',
    duration: 5000,
    color: 'error'
  })
}

// Handle submit form
const handleSubmit = async () => {
  if (!selectedMk.value || !kelas.value) {
    ToastMasukkanMataKuliah()
    return;
  }

  try {
    await useApi().sendData('data_dosen', 'POST', {
      id_dosen: idDosen,
      id_mk_genap: selectedMk.value,
      kelas: kelas.value
    });
    ToastBerhasil()
  } catch (error) {
    ToastTerjadiKesalahan(error)
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
    <UCard class="shadow-lg bg-white container max-w-4xl" variant="soft">
        <h1 class="text-2xl font-bold text-black text-center">
          Tambah Mata Kuliah untuk <br>
          <strong>{{ dosen?.nama_dosen }}</strong>
        </h1>

      <!-- Form -->
      <form class="p-6 space-y-4" @submit.prevent="handleSubmit">
        <div>
          <label for="mk" class="block text-black mb-2">Pilih Mata Kuliah:</label>
          <USelect
            id="mk"
            v-model="selectedMk"
            size="xl"
            :items="mklist"
            placeholder="Pilih mata kuliah"
            required
            class="w-full"
          />
        </div>
        
        <div>
          <label for="kelas" class="block text-black mb-2">Kelas:</label>
          <UInput
            id="kelas"
            :value="kelas"
            disabled
            type="text"
            class="w-full"
          />
        </div>

        <div class="flex justify-end space-x-4">
          <UButton 
            type="submit" 
            label="Submit" 
            icon="i-lucide-check"
            color="success" 
            size="lg"
          />
          <UButton
            type="button"
            label="Kembali"
            icon="i-lucide-arrow-left"
            color="error"
            size="lg"
            @click="router.push('/dosen')"
          />
        </div>
      </form>
    </UCard>
  </div>
</template>