export default function useApi() {
    const config = useRuntimeConfig();
    const baseUrl = config.public.apiBaseUrl || "http://127.0.0.1:8000"; // Ganti jika backend ada di server lain
  
    const fetchData = async (endpoint: string) => {
      try {
        const response = await $fetch(`${baseUrl}/${endpoint}`);
        return response;
      } catch (error) {
        console.error("Error fetching data:", error);
        return null;
      }
    };
  
    return { fetchData };
  }
  