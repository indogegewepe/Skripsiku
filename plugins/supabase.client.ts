import { createClient } from '@supabase/supabase-js';

export default defineNuxtPlugin(() => {
  const supabaseUrl = useRuntimeConfig().public.SUPABASE_URL;
  const supabaseAnonKey = useRuntimeConfig().public.SUPABASE_ANON_KEY;
  
  const supabase = createClient(supabaseUrl, supabaseAnonKey);

  return {
    provide: {
      supabase
    }
  };
});
