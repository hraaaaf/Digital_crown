import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

/**
 * Utilitaire pour fusionner les classes Tailwind proprement
 * sans conflits (ex: 'p-4 p-2' devient 'p-2')
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}