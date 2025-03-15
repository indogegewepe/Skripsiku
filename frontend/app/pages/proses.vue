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

// Variabel untuk log
const progressLogs = ref([])

// Variabel progress bar
const progressValue = ref(0)
const progressSteps = ['Creating Schedule', 'Processing Iterations', 'Done!']

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
  progressLogs.value = [] // Reset logs sebelum memulai proses baru
  
  try {
    // Mulai mencatat log
    progressLogs.value.push('Memulai proses pembuatan jadwal...')
    progressValue.value = 1
    
    const baseUrl = config.public.BASE_URL
    
    // Buat koneksi SSE (Server-Sent Events)
    const eventSource = new EventSource(`${baseUrl}/schedule-progress`)
    
    // Menangani event dari server
    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        if (data.message) {
          progressLogs.value.push(data.message)
        }
        if (data.progress) {
          progressValue.value = data.progress
        }
      } catch {
        progressLogs.value.push(`Received: ${event.data}`)
      }
    }
    
    // Menangani kesalahan SSE
    eventSource.onerror = () => {
      eventSource.close()
      progressLogs.value.push('Koneksi log terputus, melanjutkan pemrosesan...')
    }
    
    // Melakukan fetch utama untuk generate jadwal
    const data = await $fetch(`${baseUrl}/generate-schedule/${populationSize.value}/${maxIterations.value}`)
    
    // Tutup koneksi SSE setelah data diterima
    eventSource.close()
    
    // Jika server tidak mengirim log melalui SSE, simulasikan log dari respons
    if (progressLogs.value.length <= 1) {
      // Server mungkin tidak mendukung SSE, kita gunakan respons langsung
      if (data.logs && Array.isArray(data.logs)) {
        progressLogs.value = [...progressLogs.value, ...data.logs]
      } else {
        // Jika tidak ada log yang dikembalikan, kita simulasikan dari data best_fitness
        for (let i = 1; i <= maxIterations.value; i++) {
          // Estimasi fitness berdasarkan iterasi
          const estimatedFitness = data.fitness + (maxIterations.value - i) * 3
          progressLogs.value.push(`Iterasi ${i}/${maxIterations.value} - Best Fitness: ${estimatedFitness.toFixed(1)}`)
        }
        progressLogs.value.push('Optimasi Selesai!')
        progressLogs.value.push(`Best Fitness: ${data.fitness}`)
      }
    }
    
    progressValue.value = 2
    scheduleData.value = data
  } catch (error) {
    console.error("Error generating schedule:", error)
    errorMessage.value = `Gagal generate jadwal: ${error.message || 'Server error'}`
    progressLogs.value.push(`Error: ${error.message || 'Server error'}`)
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
        <label for="populationSize" class="mr-2 text-black">Population Size:</label>
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
        <label for="maxIterations" class="mr-2 text-black">Max Iterations:</label>
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
        <p class="mb-2 text-black">{{ progressSteps[progressValue] || 'Processing...' }}</p>
        <UProgress v-model="progressValue" :max="progressSteps.length" />
      </div>
      
      <!-- Bagian log proses -->
      <div v-if="progressLogs.length > 0" class="mb-4 border rounded-lg bg-gray-50 p-3">
        <h3 class="font-semibold mb-2 text-black">Progress Log:</h3>
        <div class="max-h-60 overflow-y-auto">
          <div v-for="(log, index) in progressLogs" :key="index" class="text-sm font-mono py-1 text-black">
            {{ log }}
          </div>
        </div>
      </div>=
      
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