import { useLayoutEffect, useState } from 'react';
import { createPortal } from 'react-dom';
import { ArrowRight } from 'lucide-react';
import { OnboardingScanner } from './OnboardingScanner';

function PreviewEntryCard() {
  return (
    <div
      data-dc-preview-entry
      className="w-full mt-6 p-5 rounded-3xl shadow-elite"
      style={{ backgroundColor: 'var(--glass-bg)', borderColor: 'var(--glass-border)', borderWidth: '1px' }}
    >
      <p className="text-[10px] font-black text-primary uppercase tracking-widest mb-2">MODE DÉMO — PREVIEW VERCEL</p>
      <h2 className="text-base font-black tracking-tight text-text-main mb-2">Explorer Digital Crown sans connecter le cabinet</h2>
      <p className="text-[11px] text-text-muted leading-relaxed font-bold mb-4">Aucune donnée cabinet • aucune session réelle</p>
      <button
        type="button"
        onClick={() => window.location.assign('/mobile/demo?demo=1')}
        className="w-full min-h-[52px] px-4 bg-primary hover:opacity-90 active:scale-95 rounded-2xl font-black text-sm text-white transition-all shadow-elite-hover flex items-center justify-center gap-2"
      >
        Entrer dans Digital Crown
        <ArrowRight size={16} />
      </button>
    </div>
  );
}

export function MobilePreviewOnboarding() {
  const [portalHost, setPortalHost] = useState<HTMLElement | null>(null);

  useLayoutEffect(() => {
    const shell = document.querySelector<HTMLElement>('[data-dc-mobile-shell]');
    const title = shell?.querySelector<HTMLHeadingElement>('h1');
    const intro = title?.nextElementSibling;
    const parent = intro?.parentElement;
    if (!intro || !parent) return;

    const host = document.createElement('div');
    host.dataset.dcPreviewPortal = 'true';
    host.className = 'w-full';
    parent.insertBefore(host, intro.nextSibling);
    setPortalHost(host);

    return () => {
      setPortalHost(null);
      host.remove();
    };
  }, []);

  return (
    <>
      <OnboardingScanner />
      {portalHost ? createPortal(<PreviewEntryCard />, portalHost) : null}
    </>
  );
}
