import { useDosen } from "@/composables/useDosen";
import { ref } from "vue";

export default function useDosen() {  // ✅ Ekspor default
  const { fetchData } = useApi();
  const dosenList = ref<any[]>([]);

  const fetchDosen = async (): Promise<void> => {
    dosenList.value = await fetchData("dosen");
  };

  const deleteDosenData = async (idDosen: number, idMkGenap: number): Promise<void> => {
    try {
      await $fetch(`http://127.0.0.1:8000/dosen/${idDosen}/${idMkGenap}`, {
        method: "DELETE",
      });
      fetchDosen();
    } catch (error) {
      console.error("Gagal menghapus data:", error);
    }
  };

  const addDosenData = async (idDosen: number, idMkGenap: number): Promise<void> => {
    try {
      await $fetch(`http://127.0.0.1:8000/data_dosen`, {
        method: "POST",
        body: { id_dosen: idDosen, id_mk_genap: idMkGenap },
      });
      fetchDosen();
    } catch (error) {
      console.error("Gagal menambah data:", error);
    }
  };

  return { dosenList, fetchDosen, deleteDosenData, addDosenData };
}
