<script setup>
import { ref, onMounted, watch } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import useApi from '~/composables/useApi';

// Router dan Route
const router = useRouter();
const route = useRoute();

// Props
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
    router.push('/dosen'); // Redirect ke halaman dosen
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
  <div class="container">
    <h1>Tambah Mata Kuliah untuk <br> <strong>{{ dosen?.nama_dosen }} </strong></h1>
    <form @submit.prevent="handleSubmit">
      <div>
        <label for="mk">Pilih Mata Kuliah:</label>
        <select v-model="selectedMk" id="mk" required>
          <option v-for="mk in mkList" :key="mk.id_mk_genap" :value="mk.id_mk_genap">
            {{ mk.nama_mk_genap }} (SMT: {{ mk.smt }}, SKS: {{ mk.sks }})
          </option>
        </select>
      </div>

      <div>
        <input :value="kelas" id="kelas" type="text" readonly />
      </div>

      <button type="submit">Submit</button>
      <button type="button" @click="router.push('/dosen')">Kembali</button>
    </form>
  </div>
</template>

<style scoped>
.container {
  margin: 0 auto;
  padding: 2rem;
}

h1 {
  margin-bottom: 1.5rem;
  text-align: center;
  letter-spacing: 2px;
}

form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

label {
  font-weight: bold;
}

select, input {
  width: 100%;
  padding: 0.5rem;
  margin-top: 0.5rem;
}

button {
  padding: 0.5rem 1rem;
  cursor: pointer;
}

button.secondary {
  background-color: #ccc;
}
</style>