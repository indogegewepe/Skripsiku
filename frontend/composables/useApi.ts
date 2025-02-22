export default function useApi() {
  const config = useRuntimeConfig();
  const baseUrl = config.public.baseUrl;

  const fetchData = async (endpoint: string) => {
    try {
      return await $fetch(`${baseUrl}/${endpoint}`);
    } catch (error) {
      console.error('Error fetching data:', error);
      return null;
    }
  };

  const sendData = async (endpoint: string, method: string, body?: any) => {
    try {
      const response = await $fetch(`${baseUrl}/${endpoint}`, {
        method,
        body
      });
      return response;
    } catch (error) {
      console.error('Error sending data:', error);
      throw error;
    }
  };

  return { fetchData, sendData };
}