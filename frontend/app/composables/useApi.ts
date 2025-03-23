type HttpMethod = 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE'

export default function useApi() {
  const config = useRuntimeConfig();
  const baseUrl = config.public.BASE_URL;
  
  // Pindahkan cache ke sini agar tersedia di seluruh fungsi
  const cache = new Map();
  
  // Buat fungsi untuk invalidate cache berdasarkan prefix
  const invalidateCache = (prefix: string) => {
    // Hapus semua cache dengan key yang dimulai dengan prefix
    for (const key of cache.keys()) {
      if (key.startsWith(prefix)) {
        cache.delete(key);
      }
    }
  };
  
  const fetchData = async (endpoint: string) => {
    if (cache.has(endpoint)) {
      return cache.get(endpoint);
    }
    try {
      const response = await $fetch(`${baseUrl}/${endpoint}`);
      cache.set(endpoint, response);
      return response;
    } catch (error) {
      console.error('Error fetching data:', error);
      throw error;
    }
  };
  
  const sendData = async (
    endpoint: string,
    method: HttpMethod,
    body?: Record<string, unknown>
  ) => {
    try {
      const response = await $fetch(`${baseUrl}/${endpoint}`, {
        method,
        body: JSON.stringify(body),
        headers: {
          'Content-Type': 'application/json'
        }
      });
      
      // Invalidate cache untuk endpoint yang relevan
      const [resource = ''] = endpoint.split('/')
      invalidateCache(resource);
      
      return response;
    } catch (error) {
      if (error instanceof Error) {
        throw new Error(error.message || 'Gagal mengirim data');
      } else {
        throw new Error('Gagal mengirim data');
      }
    }
  };
  
  return { fetchData, sendData, invalidateCache };
}