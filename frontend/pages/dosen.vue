<script setup>
const { data: dosenList, pending, error } = useFetch('/dosen', {
  baseURL: useRuntimeConfig().public.baseUrl,
  transform: (data) => data || []
});
</script>

<template>
  <div class="container">
    <DosenTable :dosen-list="dosenList" :pending="pending" :error="error" />
  </div>
</template>