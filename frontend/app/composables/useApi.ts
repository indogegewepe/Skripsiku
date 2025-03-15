export default function useApi() {
  const config = useRuntimeConfig();
  const baseUrl = config.public.baseUrl;
  const cache = new Map();

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

  const sendData = async (endpoint: string, method: string, body?: any) => {
    try {
      const response = await $fetch(`${baseUrl}/${endpoint}`, {
        method,
        body,
      });
      return response;
    } catch (error) {
      console.error('Error sending data:', error);
      throw error;
    }
  };

  return { fetchData, sendData };
}