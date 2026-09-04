type MobileQuickIntent = 'photo' | 'scan';

const SELECTORS: Record<MobileQuickIntent, string> = {
  photo: '[data-m6a-photo-action]',
  scan: '[data-m6b-scan-action]',
};

export function bootstrapMobileQuickIntent(): void {
  if (window.location.pathname !== '/mobile/context') return;

  let intent: MobileQuickIntent | null = null;
  try {
    const stored = sessionStorage.getItem('dc-mobile-quick-intent');
    if (stored === 'photo' || stored === 'scan') intent = stored;
  } catch {
    return;
  }
  if (!intent) return;

  document.documentElement.dataset.mobileQuickIntent = intent;
  const selector = SELECTORS[intent];

  const reveal = (): boolean => {
    const target = document.querySelector(selector);
    if (!(target instanceof HTMLElement)) return false;
    try { sessionStorage.removeItem('dc-mobile-quick-intent'); } catch { /* ignore */ }
    requestAnimationFrame(() => target.scrollIntoView({ block: 'center', behavior: 'smooth' }));
    window.setTimeout(() => {
      delete document.documentElement.dataset.mobileQuickIntent;
    }, 4500);
    return true;
  };

  if (reveal()) return;

  const observer = new MutationObserver(() => {
    if (reveal()) observer.disconnect();
  });
  observer.observe(document.documentElement, { childList: true, subtree: true });
  window.setTimeout(() => {
    observer.disconnect();
    delete document.documentElement.dataset.mobileQuickIntent;
  }, 8000);
}
