<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

import EditDosen from '@/components/EditDosen.vue'
import EditMatkul from '@/components/EditMatkul.vue'
import EditRuang from '@/components/EditRuang.vue'
import EditJam from '@/components/EditJam.vue'
import EditHari from '@/components/EditHari.vue'

const route = useRoute()

const componentMap = {
  dosen: EditDosen,
  matkul: EditMatkul,
  ruang: EditRuang,
  jam: EditJam,
  hari: EditHari
}

const selectedComponent = computed(() => {
  return componentMap[route.query.type] || EditDosen
})
</script>

<template>
  <div>
    <component :is="selectedComponent" />
  </div>
</template>