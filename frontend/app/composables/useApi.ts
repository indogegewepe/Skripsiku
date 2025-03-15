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
  
  const sendData = async (endpoint: string, method: 'GET' | 'HEAD' | 'PATCH' | 'POST' | 'PUT' | 'DELETE' | 'CONNECT' | 'OPTIONS' | 'TRACE' | 'get' | 'head' | 'patch' | 'post' | 'put' | 'delete' | 'connect' | 'options' | 'trace', body?: Record<string, unknown>) => {
    try {
      const response = await $fetch(`${baseUrl}/${endpoint}`, {
        method,
        body,
        
      });
      const prefixToInvalidate = endpoint.split('/')[0] || '';
      invalidateCache(prefixToInvalidate);
      return response;
    } catch (error) {
      console.error('Error sending data:', error);
      throw error;
    }
  };
  
  return { fetchData, sendData, invalidateCache };
}