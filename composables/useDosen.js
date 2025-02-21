import { ref } from 'vue';

export function useDosen() {
  const { $supabase } = useNuxtApp();
  const dosenList = ref([]);

  // Fetch Data Dosen
  const fetchDosen = async () => {
    const { data, error } = await $supabase
      .from('tbl_dosen')
      .select(`
        id_dosen,
        nama_dosen,
        tbl_data_dosen (id_mk_genap, kelas, tbl_mk_genap (nama_mk_genap))
      `)
      .order('id_dosen', { ascending: true });

    if (error) console.error('Error fetching data:', error);
    else dosenList.value = data;
  };

  // Tambah Data Dosen
  const addDosenData = async (idDosen, idMkGenap) => {
    try {
      // Cek apakah data sudah ada
      const { data: existingEntry, error: checkError } = await $supabase
        .from('tbl_data_dosen')
        .select('id_dosen, id_mk_genap', { head: true }) // Menggunakan head: true untuk pengecekan lebih cepat
        .eq('id_dosen', idDosen)
        .eq('id_mk_genap', idMkGenap);

      if (checkError && checkError.code !== 'PGRST116') {
        console.error('Error checking existing data:', checkError);
        return false;
      }

      if (existingEntry) {
        alert('Data sudah ada! Tidak boleh duplikat.');
        return false;
      }

      // Cek kelas terakhir yang sudah ada
      const { data: existingData, error: fetchError } = await $supabase
        .from('tbl_data_dosen')
        .select('kelas')
        .eq('id_mk_genap', idMkGenap)
        .order('kelas', { ascending: false })
        .limit(1);

      if (fetchError) {
        console.error('Error fetching existing class:', fetchError);
        return false;
      }

      let newClass = 'A';
      if (existingData.length > 0) {
        newClass = String.fromCharCode(existingData[0].kelas.charCodeAt(0) + 1);
      }

      // Insert data baru
      const { error: insertError } = await $supabase
        .from('tbl_data_dosen')
        .insert([{ id_dosen: idDosen, id_mk_genap: idMkGenap, kelas: newClass }]);

      if (insertError) {
        console.error('Error adding data:', insertError);
        return false;
      }

      await fetchDosen(); // Refresh data setelah insert
      return true;
    } catch (error) {
      console.error('Unexpected error:', error);
      return false;
    }
  };

  // Hapus Data
  const deleteDosenData = async (idDosen, idMkGenap) => {
    if (!idDosen || !idMkGenap) {
      console.error('ID Dosen atau ID Mata Kuliah tidak valid');
      return;
    }

    const { error } = await $supabase
      .from('tbl_data_dosen')
      .delete()
      .match({ id_dosen: idDosen, id_mk_genap: idMkGenap });

    if (error) {
      console.error('Error deleting data:', error);
    } else {
      console.log('Data berhasil dihapus');
      await fetchDosen(); // Refresh data setelah menghapus
    }
  };

  return { dosenList, fetchDosen, addDosenData, deleteDosenData };
}
