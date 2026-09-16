import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';
import '../styles/agendaA3Theme.css';

/**
 * Utilitaire pour fusionner les classes Tailwind proprement
 * sans conflits (ex: 'p-4 p-2' devient 'p-2')
 *
 * agendaA3Theme.css est strictement scoped sur les surfaces A3 ; l'import ici
 * garantit que le bridge de thème est chargé aussi dans les harness visuels
 * qui montent directement les composants sans passer par main.tsx.
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}