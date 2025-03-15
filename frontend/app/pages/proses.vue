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
const errorMessage = ref('')

// Variabel progress bar
const progressValue = ref(0)
const progressSteps = ['Creating Schedule', 'Done!']

// Validasi input
const validateInputs = () => {
  if (populationSize.value <= 0 || maxIterations.value <= 0) {
    errorMessage.value = 'Population size dan max iterations harus lebih besar dari 0'
    return false
  }
  
  if (populationSize.value > 100 || maxIterations.value > 100) {
    errorMessage.value = 'Nilai terlalu besar, mohon gunakan nilai di bawah 100'
    return false
  }
  
  errorMessage.value = ''
  return true
}

const generateSchedule = async () => {
  if (!validateInputs()) return
  
  loading.value = true
  progressValue.value = 0
  errorMessage.value = ''
  
  try {
    progressValue.value = 1
    const baseUrl = config.public.BASE_URL
    const data = await $fetch(`${baseUrl}/generate-schedule/${populationSize.value}/${maxIterations.value}`)
    progressValue.value = 2
    scheduleData.value = data
    progressValue.value = 3
  } catch (error) {
    console.error("Error generating schedule:", error)
    errorMessage.value = `Gagal generate jadwal: ${error.message || 'Server error'}`
    progressValue.value = 0
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
          :disabled="loading"
          min="1"
          max="100"
        />
      </div>
      
      <div class="mb-4">
        <label for="maxIterations" class="mr-2 text-black">Max Iterations :</label>
        <UInput
          id="maxIterations"
          v-model.number="maxIterations"
          type="number"
          :disabled="loading"
          min="1"
          max="100"
        />
      </div>
      
      <div v-if="errorMessage" class="mb-4 text-red-500">
        {{ errorMessage }}
      </div>
      
      <div class="mb-4">
        <UButton
          label="Generate Schedule"
          icon="i-lucide-play"
          color="primary"
          :loading="loading"
          :disabled="loading"
          @click="generateSchedule"
        />
      </div>
      
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