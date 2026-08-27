import { motion } from 'framer-motion';
import { CheckCircle2, Database, Fingerprint, LogOut, ShieldCheck, WifiOff } from 'lucide-react';

const rows = [
  {
    icon: WifiOff,
    title: 'Connexion cabinet',
    value: 'Désactivée',
    detail: 'Aucun appel réseau vers Digital Crown local.',
  },
  {
    icon: Database,
    title: 'Données',
    value: 'Fictives uniquement',
    detail: 'Aucun dossier patient réel n’est chargé ou stocké.',
  },
  {
    icon: Fingerprint,
    title: 'Biométrie',
    value: 'Non certifiée ici',
    detail: 'Face ID / empreinte restent un gate terrain sur appareil physique.',
  },
];

function exitPreviewDemo() {
  try {
    sessionStorage.removeItem('dc_preview_demo');
    localStorage.removeItem('dc_preview_demo');
  } catch { /* aucune persistance démo requise */ }
  window.location.replace('/mobile/onboarding?demo=1');
}

export function MobilePreviewSecurityView() {
  return (
    <div data-dc-preview-security className="space-y-5 pb-28">
      <motion.section
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        className="relative overflow-hidden rounded-[28px] bg-gradient-to-br from-primary to-[#5C7AD9] p-6 text-white shadow-elite"
      >
        <div className="absolute -right-10 -top-10 h-32 w-32 rounded-full bg-white/10 blur-2xl" />
        <div className="relative z-10 flex items-start gap-4">
          <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl border border-white/20 bg-white/15 backdrop-blur-md">
            <ShieldCheck size={25} strokeWidth={2.2} />
          </div>
          <div>
            <p className="text-[10px] font-black uppercase tracking-[0.18em] text-white/70">Sécurité Mobile</p>
            <h2 className="mt-1 text-xl font-black tracking-tight">Preview isolée</h2>
            <p className="mt-2 text-[11px] font-semibold leading-relaxed text-white/80">
              Aucun appareil appairé. Aucune clé, session ou donnée cabinet n’est créée dans cette Preview.
            </p>
          </div>
        </div>
      </motion.section>

      <section className="rounded-[26px] border border-white/70 bg-white/70 p-2 shadow-elite backdrop-blur-xl">
        {rows.map(({ icon: Icon, title, value, detail }, index) => (
          <div
            key={title}
            className={`flex items-start gap-3 rounded-[20px] px-4 py-4 ${index !== rows.length - 1 ? 'border-b border-border-main/60' : ''}`}
          >
            <div className="mt-0.5 flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl bg-primary/10 text-primary">
              <Icon size={19} strokeWidth={2.2} />
            </div>
            <div className="min-w-0 flex-1">
              <div className="flex items-center justify-between gap-3">
                <p className="text-[11px] font-black text-text-main">{title}</p>
                <span className="shrink-0 rounded-full bg-primary/8 px-2.5 py-1 text-[8px] font-black uppercase tracking-wider text-primary">
                  {value}
                </span>
              </div>
              <p className="mt-1 text-[10px] font-semibold leading-relaxed text-text-muted">{detail}</p>
            </div>
          </div>
        ))}
      </section>

      <div className="flex items-start gap-3 rounded-[22px] border border-emerald-200/70 bg-emerald-50/70 px-4 py-4 shadow-sm">
        <CheckCircle2 className="mt-0.5 shrink-0 text-emerald-600" size={20} />
        <div>
          <p className="text-[10px] font-black uppercase tracking-widest text-emerald-700">Isolation active</p>
          <p className="mt-1 text-[10px] font-semibold leading-relaxed text-emerald-800/75">
            Cette surface est uniquement une démonstration visuelle du compagnon mobile.
          </p>
        </div>
      </div>

      <button
        type="button"
        onClick={exitPreviewDemo}
        className="w-full min-h-[52px] rounded-2xl border border-border-main bg-white/80 text-text-main text-xs font-black flex items-center justify-center gap-2 shadow-sm active:scale-[0.98] transition-transform"
      >
        <LogOut size={16} />
        Quitter la démo
      </button>
    </div>
  );
}
