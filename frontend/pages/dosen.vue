<script setup>
const { data: dataDosenList, pending, error } = useFetch('/data_dosen', {
  baseURL: useRuntimeConfig().public.baseUrl,
  transform: (data) => data || []
});
</script>

<template>
  <div class="container">
    <DosenTable :dosen-list="dataDosenList" :pending="pending" :error="error" />
  </div>
</template>