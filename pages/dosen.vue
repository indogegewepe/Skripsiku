<script setup>
import { ref, onMounted } from "vue";
import useApi from "~/composables/useApi";

const { fetchData } = useApi();
const dosenList = ref([]);

onMounted(async () => {
  dosenList.value = await fetchData("dosen");
});
</script>

<template>
  <div>
    <DosenTable />
  </div>
</template>
