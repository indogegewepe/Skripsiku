<script setup>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';

const dosenList = ref([]);
const router = useRouter();
const config = useRuntimeConfig();

const fetchDosen = async () => {
  try {
    dosenList.value = await $fetch(`${config.public.apiBase}/dosen`);
  } catch (error) {
    console.error('Error fetching data:', error);
  }
};


const handleDelete = async (idDosen, idMkGenap) => {
  if (confirm('Apakah Anda yakin ingin menghapus data ini?')) {
    try {
      await $fetch(`/dosen/${idDosen}/${idMkGenap}`, { method: 'DELETE' });
      fetchDosen();
    } catch (error) {
      console.error('Error deleting data:', error);
    }
  }
};

onMounted(fetchDosen);
</script>

<template>
  <div class="container">
    <div style="display: flex;justify-content: space-between;">
        <h1>Data Dosen</h1>
        <button class="secondary" @click="router.push('/')">Kembali</button>
    </div>
    
    <table border="1">
      <thead>
        <tr>
          <th>Id</th>
          <th>Nama Dosen</th>
          <th>Nama Mata Kuliah</th>
          <th>Kelas</th>
          <th>Action</th>
        </tr>
      </thead>
      <tbody>
        <template v-for="(dosen, i) in dosenList" :key="i">
          <tr v-if="dosen.tbl_data_dosen?.length > 0">
            <td :rowspan="Math.max(1, dosen.tbl_data_dosen?.length+1)">{{ dosen.id_dosen }}</td>
            <td :rowspan="Math.max(1, dosen.tbl_data_dosen?.length+1)">{{ dosen.nama_dosen }}</td>
            <td>{{ dosen.tbl_data_dosen?.[0]?.tbl_mk_genap?.nama_mk_genap || 'Tidak ada data' }}</td>
            <td>{{ dosen.tbl_data_dosen?.[0]?.kelas || 'Tidak ada data' }}</td>
            <td>
              <button @click="handleDelete(dosen.id_dosen, dosen.tbl_data_dosen?.[0]?.id_mk_genap)">
                Hapus
              </button>
            </td>
          </tr>

          <tr v-for="(data, index) in dosen.tbl_data_dosen?.slice(1) || []" :key="`sub-${i}-${index}`">
            <td>{{ data.tbl_mk_genap?.nama_mk_genap || 'Tidak ada data' }}</td>
            <td>{{ data.kelas || 'Tidak ada data' }}</td>
            <td>
              <button @click="handleDelete(dosen.id_dosen, data.id_mk_genap)">Hapus</button>
            </td>
          </tr>

          <tr v-if="dosen.tbl_data_dosen?.length > 0">
            <td colspan="4">
              <button>
                <NuxtLink :to="`/add?id_dosen=${dosen.id_dosen}`">Tambah</NuxtLink>
              </button>
            </td>
          </tr>

          <tr v-else>
            <td>{{ dosen.id_dosen }}</td>
            <td>{{ dosen.nama_dosen }}</td>
            <td colspan="2" style="text-align: center;">Tidak ada mata kuliah</td>
            <td>
                <button style="display: flex;place-self: center;"><NuxtLink :to="`/add?id_dosen=${dosen.id_dosen}`" style="color: white;text-decoration: none;">Tambah</NuxtLink></button>
            </td>
          </tr>
        </template>
      </tbody>
    </table>
  </div>
</template>
