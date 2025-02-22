<script setup>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useDosen } from '@/composables/useDosen';

const props = defineProps({
  idDosen: String
});

const { addDosenData } = useDosen();
const router = useRouter();

const mkList = ref([]);
const selectedMk = ref(null);

const fetchMk = async () => {
  try {
    mkList.value = await $fetch("http://127.0.0.1:8000/mk_genap");
  } catch (error) {
    console.error("Error fetching mata kuliah:", error);
  }
};

const handleSubmit = async () => {
  if (!selectedMk.value) {
    alert('Pilih mata kuliah terlebih dahulu!');
    return;
  }

  try {
    await addDosenData(props.idDosen, selectedMk.value);
    alert("Data berhasil ditambahkan!");
    router.push("/dosen");
  } catch (error) {
    console.error("Gagal menambahkan data:", error);
    alert("Terjadi kesalahan!");
  }
};

onMounted(fetchMk);
</script>

<template>
  <form @submit.prevent="handleSubmit">
    <label>Pilih Mata Kuliah:</label>
    <select v-model="selectedMk" required>
      <option v-for="mk in mkList" :key="mk.id_mk_genap" :value="mk.id_mk_genap">
        {{ mk.nama_mk_genap }}
      </option>
    </select>
    <button type="submit">Submit</button>
    <button class="secondary" @click="router.push('/dosen')">Kembali</button>
  </form>
</template>
