<script setup>
const props = defineProps({
  dosenList: Array,
  pending: Boolean,
  error: Object
});

const { sendData } = useApi();
const router = useRouter();

const handleDelete = async (idDosen: number, idMkGenap: number) => {
  if (confirm('Apakah Anda yakin ingin menghapus data ini?')) {
    await sendData(`dosen/${idDosen}/${idMkGenap}`, 'DELETE');
    router.go(0); // Refresh data
  }
};
</script>

<!-- Template tetap sama -->