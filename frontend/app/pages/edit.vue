<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

import EditPreferensiDosen from '~/components/EditPreferensiDosen.vue'
import EditMatkul from '@/components/EditMatkul.vue'
import EditRuang from '@/components/EditRuang.vue'
import EditJam from '@/components/EditJam.vue'
import EditHari from '@/components/EditHari.vue'
import EditDosen from '@/components/EditDosen.vue'
import EditPreferensiProdi from '@/components/EditPreferensiProdi.vue'

const route = useRoute()

const componentMap = {
  preferensiDosen: EditPreferensiDosen,
  preferensiProdi: EditPreferensiProdi,
  matkul: EditMatkul,
  ruang: EditRuang,
  jam: EditJam,
  hari: EditHari,
  dosen: EditDosen
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