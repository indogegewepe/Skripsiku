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

// Variabel progress bar: progressSteps memiliki 2 langkah
const progressValue = ref(0)
const progressSteps = ['Creating Schedule', 'Done!']

const generateSchedule = async () => {
  loading.value = true
  progressValue.value = 0 // Starting
  
  try {
    progressValue.value = 1 // Creating Schedule
    const baseUrl = config.public.baseUrl
    const data = await $fetch(`${baseUrl}/generate-schedule/${populationSize.value}/${maxIterations.value}`)
    
    scheduleData.value = data
    progressValue.value = 2 // Done!
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
<<<<<<< HEAD
      <!-- Progress Bar -->
      <div class="mb-4">
        <UProgress 
          v-model="progressValue" 
          :max="progressSteps.length"
          :ui="{ 
            base: 'relative w-full overflow-hidden', 
            size: 'h-4',
            track: 'rounded-full bg-gray-200 dark:bg-gray-700',
            bar: 'rounded-full bg-primary-500' 
          }"
        />
        <div class="text-center mt-2 text-black">
          {{ progressSteps[progressValue - 1] || 'Starting...' }}
        </div>
      </div>
      <!-- Tampilan Hasil -->
      <div v-if="scheduleData">
        <h3>Best Fitness: {{ scheduleData.fitness }}</h3>
        <pre>{{ scheduleData.schedule }}</pre>
      </div>
      <!-- Tombol Navigasi -->
=======
      
      <div v-if="loading || progressValue > 0" class="mb-4">
        <p class="mb-2">{{ progressSteps[progressValue-1] || progressSteps[0] }}</p>
        <UProgress v-model="progressValue" :max="progressSteps.length" />
      </div>
      
      <div v-if="scheduleData" class="mt-6 p-4 border rounded-lg bg-gray-50">
        <h3 class="font-bold text-lg mb-2">Best Fitness: {{ scheduleData.fitness }}</h3>
        <div class="overflow-auto max-h-80">
          <pre class="text-sm">{{ JSON.stringify(scheduleData.schedule, null, 2) }}</pre>
        </div>
      </div>
      
>>>>>>> parent of 2755195 (p)
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
