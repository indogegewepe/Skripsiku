<script setup>
import { ref, onMounted } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { useDosen } from '@/composables/useDosen';

const { addDosenData } = useDosen();
const router = useRouter();
const route = useRoute();
const { $supabase } = useNuxtApp();

const idDosen = ref(route.query.id_dosen);
const dsList = ref({});
const mkList = ref([]);
const selectedMk = ref(null);

// 🔹 Ambil daftar mata kuliah
const fetchMk = async () => {
  const { data, error } = await $supabase
    .from('tbl_mk_genap')
    .select('id_mk_genap, nama_mk_genap');

  if (error) console.error('Error fetching mata kuliah:', error);
  else mkList.value = data;
};

// 🔹 Ambil data dosen berdasarkan ID
const fetchDs = async () => {
  const { data, error } = await $supabase
    .from('tbl_dosen')
    .select('id_dosen, nama_dosen')
    .eq('id_dosen', idDosen.value)
    .single(); // Ambil satu data saja

  if (error) console.error('Error fetching dosen:', error);
  else dsList.value = data || {};
};

// 🔹 Cek apakah data sudah ada sebelum insert
const isDuplicateEntry = async (idDosen, idMkGenap) => {
  const { data, error } = await $supabase
    .from('tbl_data_dosen')
    .select('id_dosen, id_mk_genap')
    .eq('id_dosen', idDosen)
    .eq('id_mk_genap', idMkGenap)
    .single();

  if (error && error.code !== 'PGRST116') {
    console.error('Error checking duplicate:', error);
  }

  return !!data;
};

// 🔹 Submit data ke Supabase
const handleSubmit = async () => {
  if (!selectedMk.value) {
    alert('Pilih mata kuliah terlebih dahulu!');
    return;
  }

  try {
    const duplicate = await isDuplicateEntry(idDosen.value, selectedMk.value);
    if (duplicate) {
      alert('Data sudah ada! Tidak boleh duplikat.');
      return;
    }

    const success = await addDosenData(idDosen.value, selectedMk.value);

    if (success) {
      alert('Data berhasil ditambahkan!');
      router.push('/');
    }
  } catch (error) {
    console.error('Gagal menambahkan data:', error);
    alert('Terjadi kesalahan saat menambahkan data!');
  }
};

// 🔹 Inisialisasi data
onMounted(() => {
  fetchMk();
  fetchDs();
});
</script>

<template>
  <div>
    <h1>Tambah Mata Kuliah</h1>

    <form @submit.prevent="handleSubmit">
      <p><strong>Nama Dosen:</strong> {{ dsList.nama_dosen || 'Loading...' }}</p>

      <label for="mk">Pilih Mata Kuliah:</label>
      <select v-model="selectedMk" required>
        <option v-for="mk in mkList" :key="mk.id_mk_genap" :value="mk.id_mk_genap">
          {{ mk.nama_mk_genap }}
        </option>
      </select>

      <br /><br />

      <button type="submit">Submit</button>
      <button type="button" @click="router.push('/')">Kembali</button>
    </form>
  </div>
</template>
