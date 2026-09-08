import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import {
  ArrowRight,
  Building2,
  CalendarDays,
  CheckCircle2,
  Crown,
  Download,
  Files,
  Loader2,
  Mail,
  MessageSquare,
  MonitorSmartphone,
  Phone,
  ScanLine,
  Sparkles,
  Users,
  WalletCards,
} from 'lucide-react';
import { api } from '../services/api';
import toast from 'react-hot-toast';

const glassStyle: React.CSSProperties = {
  background: 'var(--glass-bg)',
  borderColor: 'var(--glass-border)',
};

const FeatureCard: React.FC<{
  icon: React.ReactNode;
  title: string;
  description: string;
}> = ({ icon, title, description }) => (
  <article
    className="rounded-[26px] border p-6 backdrop-blur-xl transition-transform duration-300 hover:-translate-y-1 sm:p-7"
    style={glassStyle}
  >
    <div
      className="mb-5 flex h-11 w-11 items-center justify-center rounded-2xl"
      style={{
        background: 'color-mix(in srgb, var(--primary) 11%, transparent)',
        color: 'var(--primary)',
      }}
    >
      {icon}
    </div>
    <h3 className="text-lg font-black" style={{ color: 'var(--text-main)' }}>{title}</h3>
    <p className="mt-2 text-sm font-medium leading-6" style={{ color: 'var(--text-muted)' }}>{description}</p>
  </article>
);

export const LandingPage: React.FC = () => {
  const [form, setForm] = useState({ nom: '', email: '', cabinet: '', telephone: '', message: '' });
  const [sending, setSending] = useState(false);
  const [sent, setSent] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.nom || !form.email || !form.cabinet) return;

    setSending(true);
    try {
      await api.post('/public/demo-request', form);
      setSent(true);
      toast.success('Demande envoyée. Nous vous recontactons pour organiser la démo.');
    } catch {
      toast.error("Erreur lors de l'envoi. Réessayez.");
    } finally {
      setSending(false);
    }
  };

  const pillars = [
    { title: 'Gestion', label: 'Patients · Agenda · Facturation', icon: <Users size={18} /> },
    { title: 'Clinique', label: 'Dossiers · Imagerie · Documents', icon: <ScanLine size={18} /> },
    { title: 'Mobilité', label: 'Desktop · Companion mobile', icon: <MonitorSmartphone size={18} /> },
  ];

  const features = [
    {
      title: 'Dossiers patients',
      description: 'Créez, recherchez et consultez les informations utiles depuis un dossier patient structuré.',
      icon: <Users size={21} />,
    },
    {
      title: 'Agenda',
      description: 'Organisez les rendez-vous et gardez une lecture claire de l’activité du cabinet.',
      icon: <CalendarDays size={21} />,
    },
    {
      title: 'Facturation',
      description: 'Retrouvez les encaissements et les informations financières dans des vues dédiées.',
      icon: <WalletCards size={21} />,
    },
    {
      title: 'Dossiers cliniques',
      description: 'Centralisez documents, imagerie et informations cliniques autour du dossier patient.',
      icon: <Files size={21} />,
    },
  ];

  return (
    <div
      className="min-h-screen overflow-x-hidden font-sans"
      style={{
        background: 'radial-gradient(circle at 15% 8%, rgba(56,189,248,.10), transparent 24%), radial-gradient(circle at 85% 20%, rgba(2,132,199,.07), transparent 24%), var(--bg-medical-pearl)',
        color: 'var(--text-main)',
      }}
    >
      <nav className="sticky top-0 z-50 border-b backdrop-blur-2xl" style={glassStyle}>
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-4 py-3 sm:px-6 lg:px-8">
          <Link to="/landing" className="flex items-center gap-2.5">
            <span className="flex h-9 w-9 items-center justify-center rounded-xl text-white shadow-lg" style={{ background: 'var(--primary)' }}>
              <Crown size={18} />
            </span>
            <span className="text-lg font-black tracking-tight" style={{ color: 'var(--text-main)' }}>DigitalCrown</span>
          </Link>

          <div className="hidden items-center gap-7 text-sm font-bold md:flex" style={{ color: 'var(--text-muted)' }}>
            <a href="#features" className="transition-opacity hover:opacity-70">Fonctionnalités</a>
            <a href="#demo" className="transition-opacity hover:opacity-70">Démo</a>
          </div>

          <div className="flex items-center gap-2">
            <Link to="/login" className="hidden rounded-xl px-3 py-2 text-sm font-bold sm:block" style={{ color: 'var(--text-muted)' }}>
              Connexion
            </Link>
            <Link
              to="/download"
              className="inline-flex items-center gap-2 rounded-xl px-4 py-2.5 text-sm font-black text-white shadow-lg transition-opacity hover:opacity-90"
              style={{ background: 'var(--primary)' }}
            >
              <Download size={15} />
              <span className="hidden sm:inline">Télécharger</span>
            </Link>
          </div>
        </div>
      </nav>

      <main>
        <section className="mx-auto max-w-5xl px-4 pb-20 pt-16 text-center sm:px-6 sm:pb-24 sm:pt-20 lg:pt-24">
          <div
            className="mb-6 inline-flex items-center gap-2 rounded-full border px-4 py-2 text-[11px] font-black uppercase tracking-[0.16em] backdrop-blur-xl"
            style={{ ...glassStyle, color: 'var(--primary)' }}
          >
            <Sparkles size={13} />
            Logiciel dentaire nouvelle génération
          </div>

          <h1 className="mx-auto max-w-4xl text-5xl font-black leading-[0.98] tracking-[-0.045em] sm:text-6xl lg:text-7xl" style={{ color: 'var(--text-main)' }}>
            Gérez votre cabinet <span style={{ color: 'var(--primary)' }}>avec clarté.</span>
          </h1>

          <p className="mx-auto mt-6 max-w-2xl text-base font-medium leading-7 sm:text-lg" style={{ color: 'var(--text-muted)' }}>
            DigitalCrown centralise les patients, l’agenda, la facturation et les dossiers cliniques dans une interface moderne conçue pour le quotidien du cabinet dentaire.
          </p>

          <div className="mt-8 flex flex-col justify-center gap-3 sm:flex-row">
            <a
              href="#demo"
              className="inline-flex items-center justify-center gap-2 rounded-2xl px-6 py-3.5 text-sm font-black text-white shadow-xl transition-all hover:-translate-y-0.5 hover:opacity-90"
              style={{ background: 'var(--primary)' }}
            >
              Demander une démo <ArrowRight size={17} />
            </a>
            <Link
              to="/download"
              className="inline-flex items-center justify-center gap-2 rounded-2xl border px-6 py-3.5 text-sm font-black backdrop-blur-xl transition-all hover:-translate-y-0.5"
              style={{ ...glassStyle, color: 'var(--text-main)' }}
            >
              <Download size={17} /> Télécharger l’application
            </Link>
          </div>

          <div className="mx-auto mt-12 grid max-w-3xl divide-y rounded-[26px] border text-left backdrop-blur-xl sm:grid-cols-3 sm:divide-x sm:divide-y-0" style={glassStyle}>
            {pillars.map(({ title, label, icon }) => (
              <div key={title} className="flex min-h-[112px] items-center gap-3 px-5 py-5 sm:flex-col sm:items-start sm:justify-center sm:gap-2 sm:px-6">
                <div className="flex items-center gap-2">
                  <span className="flex h-8 w-8 items-center justify-center rounded-xl" style={{ background: 'color-mix(in srgb, var(--primary) 11%, transparent)', color: 'var(--primary)' }}>
                    {icon}
                  </span>
                  <span className="text-[11px] font-black uppercase tracking-[0.16em]" style={{ color: 'var(--primary)' }}>{title}</span>
                </div>
                <p className="text-sm font-black leading-5" style={{ color: 'var(--text-main)' }}>{label}</p>
              </div>
            ))}
          </div>
        </section>

        <section id="features" className="mx-auto max-w-6xl px-4 py-16 sm:px-6 sm:py-20 lg:px-8">
          <div className="mx-auto mb-10 max-w-2xl text-center sm:mb-12">
            <p className="text-[11px] font-black uppercase tracking-[0.2em]" style={{ color: 'var(--primary)' }}>Fonctionnalités</p>
            <h2 className="mt-3 text-3xl font-black tracking-tight sm:text-4xl" style={{ color: 'var(--text-main)' }}>Tout ce dont vous avez besoin, sans détour.</h2>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            {features.map(feature => (
              <FeatureCard key={feature.title} {...feature} />
            ))}
          </div>
        </section>

        <section id="demo" className="mx-auto max-w-4xl px-4 py-16 sm:px-6 sm:py-20 lg:px-8">
          <div className="overflow-hidden rounded-[34px] border p-6 backdrop-blur-2xl sm:p-9 lg:p-10" style={glassStyle}>
            <div className="grid gap-8 lg:grid-cols-[0.8fr_1.2fr] lg:items-center lg:gap-12">
              <div className="text-center lg:text-left">
                <p className="text-[11px] font-black uppercase tracking-[0.2em]" style={{ color: 'var(--primary)' }}>Découvrir DigitalCrown</p>
                <h2 className="mt-3 text-3xl font-black tracking-tight sm:text-4xl" style={{ color: 'var(--text-main)' }}>Voyez le produit en action.</h2>
                <p className="mt-4 text-sm font-medium leading-6 sm:text-base" style={{ color: 'var(--text-muted)' }}>
                  Demandez une démonstration pour découvrir les principaux flux du cabinet.
                </p>
              </div>

              {sent ? (
                <div className="flex min-h-[260px] flex-col items-center justify-center rounded-[26px] bg-white/80 p-8 text-center">
                  <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-emerald-100 text-emerald-600">
                    <CheckCircle2 size={26} />
                  </div>
                  <h3 className="mt-5 text-2xl font-black text-slate-800">Demande envoyée</h3>
                  <p className="mt-2 max-w-sm text-sm font-medium leading-6 text-slate-500">Nous vous recontactons pour organiser la démonstration.</p>
                </div>
              ) : (
                <form onSubmit={handleSubmit} className="rounded-[26px] bg-white/80 p-5 shadow-sm sm:p-6">
                  <div className="grid gap-3 sm:grid-cols-2">
                    {[
                      { icon: <Users size={15} />, placeholder: 'Votre nom *', value: form.nom, key: 'nom', type: 'text', required: true },
                      { icon: <Mail size={15} />, placeholder: 'Email professionnel *', value: form.email, key: 'email', type: 'email', required: true },
                      { icon: <Building2 size={15} />, placeholder: 'Nom du cabinet *', value: form.cabinet, key: 'cabinet', type: 'text', required: true },
                      { icon: <Phone size={15} />, placeholder: 'Téléphone', value: form.telephone, key: 'telephone', type: 'tel', required: false },
                    ].map(field => (
                      <label key={field.key} className="relative block">
                        <span className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400">{field.icon}</span>
                        <input
                          required={field.required}
                          type={field.type}
                          placeholder={field.placeholder}
                          value={field.value}
                          onChange={e => setForm(current => ({ ...current, [field.key]: e.target.value }))}
                          className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3.5 pl-10 text-sm font-bold text-slate-700 outline-none transition-all focus:border-sky-400 focus:ring-4 focus:ring-sky-100"
                        />
                      </label>
                    ))}
                  </div>

                  <label className="relative mt-3 block">
                    <MessageSquare size={15} className="absolute left-4 top-4 text-slate-400" />
                    <textarea
                      rows={3}
                      placeholder="Message (optionnel)"
                      value={form.message}
                      onChange={e => setForm(current => ({ ...current, message: e.target.value }))}
                      className="w-full resize-none rounded-2xl border border-slate-200 bg-white px-4 py-3.5 pl-10 text-sm font-bold text-slate-700 outline-none transition-all focus:border-sky-400 focus:ring-4 focus:ring-sky-100"
                    />
                  </label>

                  <button
                    type="submit"
                    disabled={sending}
                    className="mt-4 inline-flex w-full items-center justify-center gap-2 rounded-2xl px-5 py-3.5 text-sm font-black text-white shadow-lg transition-opacity hover:opacity-90 disabled:opacity-60"
                    style={{ background: 'var(--primary)' }}
                  >
                    {sending ? <Loader2 size={17} className="animate-spin" /> : <ArrowRight size={17} />}
                    {sending ? 'Envoi en cours…' : 'Demander ma démo'}
                  </button>
                </form>
              )}
            </div>
          </div>
        </section>
      </main>

      <footer className="border-t backdrop-blur-xl" style={glassStyle}>
        <div className="mx-auto flex max-w-7xl flex-col gap-4 px-4 py-8 sm:flex-row sm:items-center sm:justify-between sm:px-6 lg:px-8">
          <div className="flex items-center gap-2.5">
            <span className="flex h-8 w-8 items-center justify-center rounded-xl text-white" style={{ background: 'var(--primary)' }}>
              <Crown size={15} />
            </span>
            <span className="font-black" style={{ color: 'var(--text-main)' }}>DigitalCrown</span>
          </div>

          <div className="flex flex-wrap items-center gap-x-5 gap-y-2 text-sm font-medium" style={{ color: 'var(--text-muted)' }}>
            <Link to="/download">Télécharger</Link>
            <Link to="/terms">Conditions</Link>
            <Link to="/privacy">Confidentialité</Link>
          </div>

          <span className="text-xs font-medium" style={{ color: 'var(--text-muted)' }}>© {new Date().getFullYear()} Saninova</span>
        </div>
      </footer>
    </div>
  );
};
