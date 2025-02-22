<script setup>
const { idDosen } = defineProps(['idDosen']);
const { fetchData, sendData } = useApi();
const router = useRouter();

const mkList = ref([]);
const selectedMk = ref(null);

const fetchMk = async () => {
  mkList.value = await fetchData('mk_genap') || [];
};

const handleSubmit = async () => {
  if (!selectedMk.value) return;
  
  await sendData('data_dosen', 'POST', {
    id_dosen: idDosen,
    id_mk_genap: selectedMk.value
  });
  
  router.push('/dosen');
};

onMounted(fetchMk);
</script>