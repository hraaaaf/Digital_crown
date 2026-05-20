import { createClient } from '@supabase/supabase-js';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

if (!supabaseUrl || !supabaseAnonKey) {
  console.error("CRITICAL: Supabase credentials missing in .env");
}

/**
 * Client Supabase dédié à la PWA.
 * Utilisé pour le PULL des snapshots chiffrés (ZKA).
 */
export const supabase = createClient(supabaseUrl, supabaseAnonKey);
