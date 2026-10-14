import { useState, useEffect } from 'react';

interface BeforeInstallPromptEvent extends Event {
  readonly platforms: string[];
  readonly userChoice: Promise<{
    outcome: 'accepted' | 'dismissed';
    platform: string;
  }>;
  prompt(): Promise<void>;
}

// On iOS, the Home Screen web app can report navigator.standalone even when
// display-mode media queries lag during initial bootstrap. It has its own
// credential store and must complete pairing inside THIS container.
export function isStandalonePocketRuntime(): boolean {
  if (typeof window === 'undefined') return false;
  return (typeof window.matchMedia === 'function'
    && window.matchMedia('(display-mode: standalone)').matches)
    || (window.navigator as Navigator & { standalone?: boolean }).standalone === true;
}

export function usePWAInstall() {
  const [deferredPrompt, setDeferredPrompt] = useState<BeforeInstallPromptEvent | null>(null);
  const [isInstallable, setIsInstallable] = useState(false);
  const [isInstalled, setIsInstalled] = useState(isStandalonePocketRuntime);
  const [isIOS, setIsIOS] = useState(() => {
    if (typeof window === 'undefined') return false;
    return /iphone|ipad|ipod/.test(window.navigator.userAgent.toLowerCase());
  });

  useEffect(() => {
    setTimeout(() => {
      if (isStandalonePocketRuntime()) {
        setIsInstalled(true);
      }
    }, 0);

    const handleBeforeInstallPrompt = (e: Event) => {
      e.preventDefault(); // Prevent Chrome 67 and earlier from automatically showing the prompt
      setDeferredPrompt(e as BeforeInstallPromptEvent);
      setIsInstallable(true);
    };

    const handleAppInstalled = () => {
      setIsInstallable(false);
      setIsInstalled(true);
      setDeferredPrompt(null);
    };

    window.addEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
    window.addEventListener('appinstalled', handleAppInstalled);

    return () => {
      window.removeEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
      window.removeEventListener('appinstalled', handleAppInstalled);
    };
  }, []);

  const install = async () => {
    if (!deferredPrompt) return;
    deferredPrompt.prompt();
    const { outcome } = await deferredPrompt.userChoice;
    if (outcome === 'accepted') {
      setDeferredPrompt(null);
      setIsInstallable(false);
    }
  };

  return { isInstallable, isInstalled, isIOS, install };
}
