import { useState, useEffect, useRef } from 'react';

/**
 * Hook qui télécharge une image protégée via fetch() natif (injecte le token Bearer)
 * et retourne un Object URL utilisable dans un <img src> ou un background-image CSS.
 *
 * Utilise fetch() natif (pas axios) pour éviter les intercepteurs coupe-circuit.
 * - Révoque automatiquement le blob URL précédent à chaque changement d'URL.
 * - Fallback sur l'URL directe en cas d'échec (cas cookie HttpOnly valide).
 */
export function useAuthenticatedImage(imgUrl: string): string {
  const [blobUrl, setBlobUrl] = useState<string>('');
  const prevBlobRef = useRef<string>('');

  useEffect(() => {
    if (!imgUrl) {
      setBlobUrl('');
      return;
    }

    let cancelled = false;

    const token =
      localStorage.getItem('token') ||
      sessionStorage.getItem('token') ||
      '';

    const headers: HeadersInit = {};
    if (token) headers['Authorization'] = `Bearer ${token}`;

    fetch(imgUrl, { headers, credentials: 'include' })
      .then(async res => {
        if (cancelled) return;
        if (!res.ok) {
          console.warn(`[useAuthenticatedImage] HTTP ${res.status} pour : ${imgUrl}`);
          // Fallback : passer l'URL directe (le navigateur essaiera avec ses propres cookies)
          setBlobUrl(imgUrl);
          return;
        }
        const blob = await res.blob();
        if (cancelled) return;
        const url = URL.createObjectURL(blob);
        if (prevBlobRef.current) URL.revokeObjectURL(prevBlobRef.current);
        prevBlobRef.current = url;
        setBlobUrl(url);
      })
      .catch(err => {
        if (!cancelled) {
          console.warn('[useAuthenticatedImage] Fetch échoué :', err);
          setBlobUrl(imgUrl);
        }
      });

    return () => { cancelled = true; };
  }, [imgUrl]);

  // Nettoyage final à la destruction du composant
  useEffect(() => () => {
    if (prevBlobRef.current) URL.revokeObjectURL(prevBlobRef.current);
  }, []);

  return blobUrl;
}
