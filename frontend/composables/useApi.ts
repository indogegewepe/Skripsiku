export default function useApi() {
  const config = useRuntimeConfig();
  const baseUrl = config.public.baseUrl;

  const fetchData = async <T>(endpoint: string): Promise<T | null> => {
    try {
      return await $fetch(`${baseUrl}/${endpoint}`);
    } catch (error) {
      console.error("Error fetching data:", error);
      return null;
    }
  };

  const sendData = async <T>(endpoint: string, method: string, body?: any): Promise<T | null> => {
    try {
      return await $fetch(`${baseUrl}/${endpoint}`, {
        method,
        body
      });
    } catch (error) {
      console.error("Error sending data:", error);
      return null;
    }
  };

  return { fetchData, sendData };
}