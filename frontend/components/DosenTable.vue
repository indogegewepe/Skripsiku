<script setup>
import { useRouter } from 'vue-router';
import useApi from '~/composables/useApi';

const props = defineProps({
  dosenList: Array,
  pending: Boolean,
  error: Object
});

const { sendData } = useApi();
const router = useRouter();

const handleDelete = async (idDosen, idMkGenap) => {
  if (confirm('Apakah Anda yakin ingin menghapus data ini?')) {
    try {
      await sendData(`data_dosen/${idDosen}/${idMkGenap}`, 'DELETE');
      router.go(0); // Refresh data
    } catch (error) {
      console.error('Error deleting data:', error);
    }
  }
};
</script>

<template>
  <div class="container">
    <div style="display: flex; justify-content: space-between;">
      <h1>Data Dosen</h1>
      <button class="secondary" @click="router.push('/')">Kembali</button>
    </div>

    <div v-if="pending">Loading...</div>
    <div v-else-if="error">Error: {{ error.message }}</div>
    <table v-else border="1">
      <thead>
        <tr>
          <th>Id Dosen</th>
          <th>Nama Dosen</th>
          <th>Nama Mata Kuliah</th>
          <th>Kelas</th>
          <th>Action</th>
        </tr>
      </thead>
      <tbody>
        <template v-for="(dosen, i) in dosenList" :key="i">
          <tr v-if="dosen.mata_kuliah?.length > 0">
            <td :rowspan="Math.max(1, dosen.mata_kuliah?.length + 1)">{{ dosen.id_dosen }}</td>
            <td :rowspan="Math.max(1, dosen.mata_kuliah?.length + 1)">{{ dosen.nama_dosen }}</td>
            <td>{{ dosen.mata_kuliah?.[0]?.nama_mk_genap || 'Tidak ada data' }}</td>
            <td>{{ dosen.mata_kuliah?.[0]?.kelas || 'Tidak ada data' }}</td>
            <td>
              <button @click="handleDelete(dosen.id_dosen, dosen.mata_kuliah?.[0]?.id_mk_genap)">
                Hapus
              </button>
            </td>
          </tr>

          <tr v-for="(mk, index) in dosen.mata_kuliah?.slice(1) || []" :key="`sub-${i}-${index}`">
            <td>{{ mk.nama_mk_genap || 'Tidak ada data' }}</td>
            <td>{{ mk.kelas || 'Tidak ada data' }}</td>
            <td>
              <button @click="handleDelete(dosen.id_dosen, mk.id_mk_genap)">Hapus</button>
            </td>
          </tr>

          <tr v-if="dosen.mata_kuliah?.length > 0">
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
              <button>
                <NuxtLink :to="`/add?id_dosen=${dosen.id_dosen}`">
                  Tambah
                </NuxtLink>
              </button>
            </td>
          </tr>
        </template>
      </tbody>
    </table>
  </div>
</template>