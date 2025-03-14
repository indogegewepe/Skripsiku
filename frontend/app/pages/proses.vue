<script setup>
import { ref } from 'vue'
import { useRouter, useRuntimeConfig } from '#imports'

const router = useRouter()
const config = useRuntimeConfig()

// Variabel reaktif untuk form dan status
const populationSize = ref(10)
const maxIterations = ref(10)
const scheduleData = ref(null)
const loading = ref(false)

// Variabel progress bar: progressSteps memiliki 3 langkah
const progressValue = ref(0)
const progressSteps = ['Creating Schedule', 'Processing Iterations', 'Done!']

const generateSchedule = async () => {
  loading.value = true
  progressValue.value = 0

  try {
    progressValue.value = 1
    const baseUrl = config.public.BASE_URL
    const data = await $fetch(`${baseUrl}generate-schedule/${populationSize.value}/${maxIterations.value}`)
    progressValue.value = 2
    scheduleData.value = data
    progressValue.value = 3
  } catch (error) {
    console.error("Error generating schedule:", error)
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="min-h-screen flex items-center justify-center">
    <div class="w-full max-w-screen-md bg-white border border-black rounded-lg shadow-lg p-6">
      <h1 class="font-bold text-7xl text-black text-center mb-6">
        Generate Jadwal
      </h1>
      <div class="mb-4">
        <label for="populationSize" class="mr-2 text-black">Population Size :</label>
        <UInput
          id="populationSize"
          v-model.number="populationSize"
          type="number"
        />
      </div>
      <div class="mb-4">
        <label for="maxIterations" class="mr-2 text-black">Max Iterations :</label>
        <UInput
          id="maxIterations"
          v-model.number="maxIterations"
          type="number"
        />
      </div>
      <!-- Tombol Generate -->
      <div class="mb-4">
        <UButton
          label="Generate Schedule"
          color="primary"
          @click="generateSchedule"
        />
      </div>
      <!-- Progress Bar -->
      <div class="mb-4">
        <UProgress v-model="progressValue" :max="progressSteps" />
      </div>
      <!-- Tampilan Hasil -->
      <div v-if="scheduleData">
        <h3>Best Fitness: {{ scheduleData.fitness }}</h3>
        <pre>{{ scheduleData.schedule }}</pre>
      </div>
      <!-- Tombol Navigasi -->
      <div class="flex justify-center gap-4 mt-6">
        <UButton
          label="Kembali"
          color="error"
          icon="i-lucide-arrow-left"
          class="px-8 py-4 shadow-lg"
          @click="router.push('/')"
        />
        <UButton
          label="Lihat Jadwal"
          color="primary"
          icon="i-lucide-calendar-check"
          class="px-8 py-4 shadow-lg"
          @click="router.push('/jadwal')"
        />
      </div>
    </div>
  </div>
</template>
