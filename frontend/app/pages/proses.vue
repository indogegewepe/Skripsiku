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
const currentIteration = ref(0)
const totalIterations = ref(0)
const bestFitness = ref(0)

function ToastBerhasil(msg) {
  toast.add({
    title: 'Berhasil!!',
    message: msg,
    icon: 'i-lucide-check-circle',
    duration: 5000,
    color: 'success'
  })
}

function ToastGagal(msg) {
  toast.add({
    title: 'Gagal!',
    message: msg,
    icon: 'i-lucide-alert-circle',
    duration: 5000,
    color: 'error'
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

const ws = new WebSocket('ws://localhost:8000/ws/logs');

ws.onmessage = (event) => {
  console.log("Log update:", event.data);
  
  // Ekstrak iterasi: "Iterasi <current>/<total>"
  const iterRegex = /Iterasi\s+(\d+)\/(\d+)/;
  const iterMatch = event.data.match(iterRegex);
  if (iterMatch) {
    currentIteration.value = parseInt(iterMatch[1]);
    totalIterations.value = parseInt(iterMatch[2]);
  }
  
  // Ekstrak best fitness: "Best fitness: <value>"
  const fitnessRegex = /Best\s+fitness:\s+([\d.]+)/i;
  const fitnessMatch = event.data.match(fitnessRegex);
  if (fitnessMatch) {
    bestFitness.value = parseFloat(fitnessMatch[1]);
  }
};

ws.onerror = (error) => {
  console.error("WebSocket error:", error);
};

// Menutup koneksi secara eksplisit sebelum pengguna berpindah laman
window.addEventListener("beforeunload", () => {
  ws.close();
});

const generateSchedule = async () => {
  if (!validateInputs()) return;
  
  loading.value = true;
  currentIteration.value = 0;
  totalIterations.value = maxIterations.value;
  errorMessage.value = '';

  try {
    const baseUrl = config.public.BASE_URL;
    const data = await $fetch(`${baseUrl}/generate-schedule/`, {
      method: 'POST',
      body: {
        population_size: populationSize.value,
        max_iterations: maxIterations.value
      }
    });
    scheduleData.value = data;
    ToastBerhasil('Jadwal berhasil digenerate');
  } catch (error) {
    ToastGagal('Terjadi kesalahan saat generate jadwal');
    console.error('Error generating schedule:', error);
    errorMessage.value = `Gagal generate jadwal: ${error.message || 'Server error'}`;
    currentIteration.value = 0;
    totalIterations.value = 0;
  } finally {
    loading.value = false;
  }
};
</script>

<template>
  <div class="min-h-screen flex items-center justify-center">
    <UCard class="w-full max-w-screen-md rounded-lg shadow-lg p-6" variant="soft">
      <h1 class="font-bold sm:text-7xl text-2xl text-center mb-6">
        Generate Jadwal
      </h1>
      
      <div class="mb-4">
        <label for="populationSize" class="mr-2">Population Size :</label>
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
        <label for="maxIterations" class="mr-2">Max Iterations :</label>
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
      
      <div v-if="loading || currentIteration > 0" class="mb-4">
        <p class="mb-2">
          Iterasi {{ currentIteration }} / {{ totalIterations }} {{ `| Fitness: ${bestFitness}` }}
        </p>
        <UProgress v-model="currentIteration" color="info" :max="totalIterations" />
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
          color="success"
          icon="i-lucide-calendar-check"
          class="px-8 py-4 shadow-lg"
          :loading="loading"
          @click="router.push('/jadwal')"
        />
      </div>
    </UCard>
  </div>
</template>
