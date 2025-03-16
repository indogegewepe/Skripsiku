<script setup>
import { ref } from 'vue'
import { useRouter, useRuntimeConfig } from '#imports'

const toast = useToast();
const router = useRouter()
const config = useRuntimeConfig()
const populationSize = ref(30)
const maxIterations = ref(30)
const scheduleData = ref(null)
const loading = ref(false)
const errorMessage = ref('')
const progressValue = ref(0)
const progressSteps = ['Creating Schedule...', 'Done!']

function showToast() {
  toast.add({
    title: 'Jadwal Berhasil Dibuat',
    message: 'Jadwal telah berhasil dibuat, silahkan lihat hasilnya di bawah',
    icon: 'i-lucide-check-circle',
    duration: 5000,
    color: 'success'
  })
}

const validateInputs = () => {
  if (populationSize.value <= 3 || maxIterations.value <= 3) {
    errorMessage.value = 'Population size dan max iterations harus lebih besar dari 3'
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
    const data = await $fetch(`${baseUrl}/generate-schedule/`, {
      method: 'POST',
      body: {
        population_size: populationSize.value,
        max_iterations: maxIterations.value
      }
    })
    
    progressValue.value = 2
    scheduleData.value = data
    progressValue.value = 3
    showToast()
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
      <h1 class="font-bold sm:text-7xl text-2xl text-black text-center mb-6">
        Generate Jadwal
      </h1>
      
      <div class="mb-4">
        <label for="populationSize" class="mr-2 text-black">Population Size :</label>
        <UInput
          id="populationSize"
          v-model.number="populationSize"
          type="number"
          :disabled="loading"
          color="info"
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
          color="info"
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
          icon="i-lucide-rocket"
          color="info"
          :loading="loading"
          :disabled="loading"
          class=" p-3 shadow-lg"
          @click="generateSchedule"
        />
      </div>
      
      <div v-if="loading || progressValue > 0" class="mb-4">
        <p class="mb-2 text-black">{{ progressSteps[progressValue-1] || progressSteps[0] }}</p>
        <UProgress v-model="progressValue" color="info" :max="progressSteps.length " />
      </div>
      
      <!-- <div v-if="scheduleData" class="mt-6 p-4 border rounded-lg bg-gray-300">
        <h3 class="font-bold text-lg text-black">Optimasi Selesai!</h3>
        <div class="overflow-auto max-h-80">
          <pre class="text-sm">{{ JSON.stringify(scheduleData.schedule, null, 2) }}</pre>
        </div>
      </div> -->
      
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
          color="success"
          icon="i-lucide-calendar-check"
          class="px-8 py-4 shadow-lg"
          :loading="loading"
          @click="router.push('/jadwal')"
        />
      </div>
    </div>
  </div>
</template>
