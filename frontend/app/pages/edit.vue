<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

import EditPreferensi from '@/components/EditPreferensi.vue'
import EditMatkul from '@/components/EditMatkul.vue'
import EditRuang from '@/components/EditRuang.vue'
import EditJam from '@/components/EditJam.vue'
import EditHari from '@/components/EditHari.vue'

const route = useRoute()

const componentMap = {
  preferensi: EditPreferensi,
  matkul: EditMatkul,
  ruang: EditRuang,
  jam: EditJam,
  hari: EditHari
}

const selectedComponent = computed(() => {
  return componentMap[route.query.type] || EditPreferensi
})
</script>

<template>
  <div>
    <component :is="selectedComponent" />
  </div>
</template>