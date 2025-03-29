<!-- eslint-disable vue/require-prop-types -->
<script setup>
import { ref, onMounted, watch, computed, h } from 'vue';
import { useRouter } from 'vue-router';
import useApi from '~/composables/useApi';

const router = useRouter();
const { idDosen } = defineProps(['idDosen']);

// eslint-disable-next-line @typescript-eslint/no-unused-vars
const { sendData, fetchData } = useApi();

const UButton = resolveComponent('UButton')
const dosen = ref(null);
const mklist = ref([]); 
const selectedMk = ref(null);
const kelas = ref(''); 
const dataDosen = ref([]); 
const toast = useToast();

function ToastBerhasil(msg) {
  toast.add({
    title: 'Berhasil!',
    description: msg,
    icon: 'i-lucide-check-circle',
    duration: 5000,
    color: 'success'
  })
}

function ToastWarning(msg) {
  toast.add({
    title: 'Peringatan!',
    description: msg,
    icon: 'i-lucide-error-circle',
    duration: 5000,
    color: 'warning'
  })
}

function ToastErr(err) {
  toast.add({
    title: 'Terjadi kesalahan!',
    description: err,
    icon: 'i-lucide-error-circle',
    duration: 5000,
    color: 'error'
  })
}

const fetchDosen = async () => {
  try {
    const data = await useApi().fetchData(`dosen/${idDosen}`);
    dosen.value = data;
  } catch (error) {
    ToastErr('Error fetching dosen: ' + error)
  }
};

const fetchMk = async () => {
  try {
    const data = await useApi().fetchData('mk_genap');
      mklist.value = (data || []).map(item => ({
      value: item.id_mk_genap,
      label: item.nama_mk_genap
    }));
  } catch (error) {
    ToastErr('Error fetching mk: ' + error)
  }
};

const fetchDataDosen = async () => {
  try {
    const data = await useApi().fetchData('tbl_data_dosen');
    dataDosen.value = data;
  } catch (error) {
    ToastErr('Error fetching data dosen: ' + error)
  }
};

const calculateKelas = () => {
  if (!selectedMk.value) {
    return;
  }
  const kelasList = dataDosen.value
    .filter(item => item.id_mk_genap === selectedMk.value)
    .map(item => item.kelas);
  let nextKelas = 'A';
  while (kelasList.includes(nextKelas)) {
    nextKelas = String.fromCharCode(nextKelas.charCodeAt(0) + 1);
  }
  kelas.value = nextKelas;
};

const handleSubmit = async () => {
  if (!selectedMk.value || !kelas.value) {
    ToastWarning('Pilih mata kuliah dan kelas terlebih dahulu');
    return;
  }

  try {
    await useApi().sendData('data_dosen', 'POST', {
      id_dosen: idDosen,
      id_mk_genap: selectedMk.value,
      kelas: kelas.value
    });
    await fetchDataDosen();
    ToastBerhasil('Data berhasil ditambahkan');
  } catch (error) {
    ToastErr('Error adding data: ' + error)
  }
};

const tableData = computed(() => {
  return dataDosen.value
    .filter((item) => item.id_dosen == idDosen)
    .map((item) => {
      const matchingCourse = mklist.value.find(
        mk => mk.value === item.id_mk_genap
      );
      
      return {
        id_dosen: item.id_dosen,  
        id_mk_genap: item.id_mk_genap, 
        kelas: item.kelas,
        mk: matchingCourse ? matchingCourse.label : (item.id_mk_genap || '-')
      };
    });
});

const showConfirm = ref(false);
const confirmPromiseResolve = ref(null);

const openConfirmDialog = () => {
  showConfirm.value = true;
  return new Promise((resolve) => {
    confirmPromiseResolve.value = resolve;
  });
};

const confirmDialog = () => {
  showConfirm.value = false;
  if (confirmPromiseResolve.value) confirmPromiseResolve.value(true);
};

const cancelDialog = () => {
  showConfirm.value = false;
  if (confirmPromiseResolve.value) confirmPromiseResolve.value(false);
};

const handleDelete = async (idDosen, idMkGenap) => {
  const confirmed = await openConfirmDialog();
  if (confirmed) {
    try {
      const endpoint = `data_dosen/${idDosen}/${idMkGenap}`;
      await sendData(endpoint, 'DELETE');
      await fetchDataDosen();
      ToastBerhasil('Data berhasil dihapus');
    } catch (err) {
      ToastErr('Error deleting data: ' + err)
    }
  }
};

const columns = computed(() => {
  return [
    { accessorKey: 'mk', header: 'Mata Kuliah' },
    { accessorKey: 'kelas', header: 'Kelas' },
    {
      id: 'actions',
      header: 'Action',
      cell: ({ row }) => { 
        return h(UButton, {
          label: 'Hapus',
          icon: 'i-lucide-trash',
          color: 'error',
          class: 'text-sm',
          onClick: () => handleDelete(row.original.id_dosen, row.original.id_mk_genap)
        });
      }
    }
  ];
});

onMounted(async () => {
  await fetchDosen();
  await fetchMk();
  await fetchDataDosen();
});

watch(selectedMk, calculateKelas);
</script>

<template>
  <div class="min-h-screen flex items-center justify-center">
    <UCard variant="soft" class="shadow-lg container max-w-4xl">
        <h1 class="text-2xl font-bold text-center">
          Tambah Mata Kuliah untuk <br>
          <strong>{{ dosen?.nama_dosen }}</strong>
        </h1>

      <!-- Form -->
      <form class="p-6 space-y-4" @submit.prevent="handleSubmit">
        <div>
          <label for="mk" class="block  mb-2">Pilih Mata Kuliah:</label>
          <USelect
            id="mk"
            v-model="selectedMk"
            size="xl"
            :items="mklist"
            placeholder="Pilih mata kuliah"
            required
            class="w-full"
          />
        </div>
        
        <div>
          <label for="kelas" class="block mb-2">Kelas:</label>
          <UInput
            id="kelas"
            size="xl"
            :value="kelas"
            disabled
            type="text"
            class="w-full"
          />
        </div>

        <UCard class="mt-6">
          <h2 class="text-lg font-semibold mb-2">Mata Kuliah Terdaftar untuk {{ dosen?.nama_dosen }}:</h2>
          <UTable 
            :data="tableData"
            :columns="columns"
          />
        </UCard>

        <div class="flex justify-end space-x-4">
          <UButton 
            type="submit" 
            label="Submit" 
            icon="i-lucide-check"
            color="success" 
            size="lg"
          />
          <UButton
            type="button"
            label="Kembali"
            icon="i-lucide-arrow-left"
            color="error"
            size="lg"
            @click="router.push('/dosen')"
          />
        </div>
      </form>
    </UCard>
    <UAlert
      v-if="showConfirm"
      title="Konfirmasi"
      description="Apakah Anda yakin ingin menghapus data ini?"
      color="warning"
      variant="subtle"
      class="absolute w-2/3 backdrop-blur-md"
      :actions="[
        { label: 'Batal', onClick: cancelDialog, color: 'error' },
        { label: 'Konfirmasi', onClick: confirmDialog, color: 'success' }
      ]"
    />
  </div>
</template>