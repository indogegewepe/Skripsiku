<script setup>
import { useDosen } from '@/composables/useDosen';

const { dosenList, fetchDosen, deleteDosenData } = useDosen();

onMounted(fetchDosen);

const handleDelete = async (idDosen, idMkGenap) => {
  if (confirm('Apakah Anda yakin ingin menghapus data ini?')) {
    await deleteDosenData(idDosen, idMkGenap);
  }
};
</script>

<template>
  <div>
    <h1>Data Dosen</h1>
    
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
          <tr v-if="dosen.tbl_data_dosen && dosen.tbl_data_dosen.length > 0">
            <td :rowspan="dosen.tbl_data_dosen.length+1">{{ dosen.id_dosen }}</td>
            <td :rowspan="dosen.tbl_data_dosen.length+1">{{ dosen.nama_dosen }}</td>
            <td>{{ dosen.tbl_data_dosen[0]?.tbl_mk_genap?.nama_mk_genap || 'Tidak ada data' }}</td>
            <td>{{ dosen.tbl_data_dosen[0]?.kelas || 'Tidak ada data' }}</td>
            <td>
              <button @click="handleDelete(dosen.id_dosen, dosen.tbl_data_dosen[0]?.id_mk_genap)">Hapus</button>
            </td>
          </tr>

          <tr v-for="(data, index) in dosen.tbl_data_dosen?.slice(1) || []" :key="`sub-${i}-${index}`">
            <td>{{ data.tbl_mk_genap?.nama_mk_genap || 'Tidak ada data' }}</td>
            <td>{{ data.kelas }}</td>
            <td>
              <button @click="handleDelete(dosen.id_dosen, data.id_mk_genap)">Hapus</button>
            </td>
          </tr>

          <tr v-if="dosen.tbl_data_dosen && dosen.tbl_data_dosen.length > 0">
            <td colspan="3">
              <NuxtLink :to="`/add?id_dosen=${dosen.id_dosen}`">Tambah</NuxtLink>
            </td>
          </tr>

          <tr v-else>
            <td>{{ dosen.id_dosen }}</td>
            <td>{{ dosen.nama_dosen }}</td>
            <td colspan="2" style="text-align: center;">Tidak ada mata kuliah</td>
            <td>
              <NuxtLink :to="`/add?id_dosen=${dosen.id_dosen}`">Tambah</NuxtLink>
            </td>
          </tr>
        </template>
      </tbody>
    </table>
  </div>
</template>
