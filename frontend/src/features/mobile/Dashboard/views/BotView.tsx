import { Bot, Construction } from 'lucide-react';

export function BotView() {
  return (
    <section data-mobile-assistant className="pb-8 pt-2">
      <div className="rounded-[26px] border border-glass-border bg-card p-6 text-center shadow-sm">
        <div className="mx-auto grid h-14 w-14 place-items-center rounded-[20px] bg-primary/10 text-primary">
          <Bot size={26} />
        </div>
        <p className="mt-5 text-[10px] font-black uppercase tracking-[0.18em] text-primary">Digital Crown Pocket</p>
        <h1 className="mt-1 text-[24px] font-black tracking-tight text-text-main">Assistant</h1>
        <div className="mx-auto mt-4 inline-flex min-h-11 items-center gap-2 rounded-full border border-glass-border bg-background px-4 text-[11px] font-black text-text-muted">
          <Construction size={15} /> En cours de construction
        </div>
        <p className="mx-auto mt-4 max-w-sm text-[12px] font-semibold leading-relaxed text-text-muted">
          Cette surface reste dans la navigation Pocket canonique, sans ouvrir de session desktop ni exposer un accès partiel non certifié.
        </p>
      </div>
    </section>
  );
}
