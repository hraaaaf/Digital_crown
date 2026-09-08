import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Activity,
  ArrowRight,
  BarChart3,
  BookOpen,
  Building2,
  CalendarDays,
  CheckCircle2,
  ChevronDown,
  Crown,
  Download,
  FileText,
  Files,
  LayoutDashboard,
  Loader2,
  Mail,
  MessageSquare,
  MonitorSmartphone,
  Phone,
  ScanLine,
  ShieldCheck,
  ShoppingBag,
  Smartphone,
  Sparkles,
  Users,
  WalletCards,
} from 'lucide-react';
import { api } from '../services/api';
import toast from 'react-hot-toast';

type InfoCardProps = {
  icon: React.ReactNode;
  title: string;
  description: string;
};

const glassStyle: React.CSSProperties = {
  background: 'var(--glass-bg)',
  borderColor: 'var(--glass-border)',
};

const InfoCard: React.FC<InfoCardProps> = ({ icon, title, description }) => (
  <article
    className="rounded-[28px] border p-6 sm:p-7 backdrop-blur-xl transition-transform duration-300 hover:-translate-y-1"
    style={glassStyle}
  >
    <div
      className="mb-5 flex h-11 w-11 items-center justify-center rounded-2xl"
      style={{ background: 'color-mix(in srgb, var(--primary) 11%, transparent)', color: 'var(--primary)' }}
    >
      {icon}
    </div>
    <h3 className="mb-2 text-lg font-black" style={{ color: 'var(--text-main)' }}>{title}</h3>
    <p className="text-sm font-medium leading-6" style={{ color: 'var(--text-muted)' }}>{description}</p>
  </article>
);

const SectionHeading: React.FC<{ eyebrow?: string; title: string; description: string }> = ({ eyebrow, title, description }) => (
  <div className="mx-auto mb-12 max-w-3xl text-center sm:mb-16">
    {eyebrow && (
      <p className="mb-3 text-[11px] font-black uppercase tracking-[0.22em]" style={{ color: 'var(--primary)' }}>{eyebrow}</p>
    )}
    <h2 className="text-3xl font-black tracking-tight sm:text-4xl lg:text-5xl" style={{ color: 'var(--text-main)' }}>{title}</h2>
    <p className="mx-auto mt-4 max-w-2xl text-base font-medium leading-7 sm:text-lg" style={{ color: 'var(--text-muted)' }}>{description}</p>
  </div>
);

const MiniProductVisual = () => (
  <div className="relative mx-auto w-full max-w-[620px] lg:mx-0 lg:ml-auto">
    <div
      className="relative overflow-hidden rounded-[30px] border p-3 shadow-[0_30px_90px_rgba(15,23,42,0.16)] backdrop-blur-2xl sm:p-4"
      style={glassStyle}
    >
      <div className="mb-3 flex items-center gap-1.5 px-2 pt-1">
        <span className="h-2.5 w-2.5 rounded-full bg-slate-300" />
        <span className="h-2.5 w-2.5 rounded-full bg-slate-200" />
        <span className="h-2.5 w-2.5 rounded-full bg-slate-200" />
      </div>
      <div className="grid min-h-[330px] grid-cols-[54px_1fr] overflow-hidden rounded-[22px] bg-white/80 sm:grid-cols-[120px_1fr]">
        <aside className="border-r border-slate-100 bg-white/70 p-3 sm:p-4">
          <div className="mb-6 flex items-center gap-2">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl text-white" style={{ background: 'var(--primary)' }}>
              <Crown size={15} />
            </div>
            <span className="hidden text-xs font-black sm:block" style={{ color: 'var(--text-main)' }}>DigitalCrown</span>
          </div>
          <div className="space-y-2">
            {[LayoutDashboard, CalendarDays, Users, WalletCards].map((Icon, index) => (
              <div
                key={index}
                className="flex h-9 items-center gap-2 rounded-xl px-2.5"
                style={index === 0 ? { background: 'color-mix(in srgb, var(--primary) 10%, transparent)', color: 'var(--primary)' } : { color: '#94a3b8' }}
              >
                <Icon size={15} />
                <span className="hidden text-[10px] font-bold sm:block">{['Tableau de bord', 'Agenda', 'Patients', 'Facturation'][index]}</span>
              </div>
            ))}
          </div>
        </aside>
        <main className="p-4 sm:p-6">
          <div className="mb-5 flex items-start justify-between gap-4">
            <div>
              <p className="text-[10px] font-black uppercase tracking-[0.18em]" style={{ color: 'var(--primary)' }}>Aujourd'hui</p>
              <h3 className="mt-1 text-lg font-black sm:text-xl" style={{ color: 'var(--text-main)' }}>Votre cabinet en un coup d'œil</h3>
            </div>
            <div className="hidden h-9 w-9 items-center justify-center rounded-xl bg-slate-100 text-slate-500 sm:flex">
              <Activity size={16} />
            </div>
          </div>

          <div className="grid gap-3 sm:grid-cols-2">
            <div className="rounded-2xl border border-slate-100 bg-white p-4 shadow-sm">
              <div className="mb-3 flex items-center gap-2">
                <CalendarDays size={15} style={{ color: 'var(--primary)' }} />
                <span className="text-xs font-black text-slate-700">Agenda</span>
              </div>
              <div className="space-y-2">
                {['09:30 · Consultation', '11:00 · Contrôle', '14:30 · Rendez-vous'].map(item => (
                  <div key={item} className="rounded-xl bg-slate-50 px-3 py-2 text-[10px] font-bold text-slate-500">{item}</div>
                ))}
              </div>
            </div>
            <div className="rounded-2xl border border-slate-100 bg-white p-4 shadow-sm">
              <div className="mb-3 flex items-center gap-2">
                <Users size={15} style={{ color: 'var(--primary)' }} />
                <span className="text-xs font-black text-slate-700">Dossiers patients</span>
              </div>
              <div className="space-y-2">
                {['Patient A', 'Patient B', 'Patient C'].map((item, index) => (
                  <div key={item} className="flex items-center gap-2 rounded-xl bg-slate-50 px-3 py-2">
                    <span className="h-5 w-5 rounded-lg" style={{ background: index === 0 ? 'color-mix(in srgb, var(--primary) 16%, white)' : '#e2e8f0' }} />
                    <span className="text-[10px] font-bold text-slate-500">{item}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="mt-3 rounded-2xl border border-slate-100 bg-white p-4 shadow-sm">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Pilotage</p>
                <p className="mt-1 text-xs font-black text-slate-700">Une vue structurée de l'activité</p>
              </div>
              <BarChart3 size={20} style={{ color: 'var(--primary)' }} />
            </div>
          </div>
        </main>
      </div>
    </div>

    <div
      className="absolute -bottom-8 -right-2 hidden w-[180px] rounded-[26px] border p-3 shadow-[0_22px_55px_rgba(15,23,42,0.18)] backdrop-blur-2xl sm:block lg:-right-6"
      style={glassStyle}
    >
      <div className="rounded-[20px] bg-white p-3">
        <div className="mb-4 flex items-center justify-between">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg text-white" style={{ background: 'var(--primary)' }}>
            <Smartphone size={13} />
          </div>
          <span className="text-[9px] font-black uppercase tracking-wider text-slate-400">Companion</span>
        </div>
        <p className="text-[11px] font-black text-slate-700">L'essentiel sur mobile</p>
        <div className="mt-3 space-y-2">
          <div className="h-8 rounded-xl bg-slate-50" />
          <div className="h-8 rounded-xl bg-slate-50" />
        </div>
      </div>
    </div>
  </div>
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

  const productPillars = [
    { title: 'Gestion', label: 'Patients · Agenda · Facturation', icon: <Users size={17} /> },
    { title: 'Clinique', label: 'Dossiers · Imagerie · Documents', icon: <ScanLine size={17} /> },
    { title: 'Mobilité', label: 'Desktop · Companion mobile', icon: <MonitorSmartphone size={17} /> },
  ];

  const modules = [
    { title: 'Patients', icon: <Users size={18} /> },
    { title: 'Agenda', icon: <CalendarDays size={18} /> },
    { title: 'Facturation', icon: <WalletCards size={18} /> },
    { title: 'Dossiers cliniques', icon: <Files size={18} /> },
    { title: 'Imagerie', icon: <ScanLine size={18} /> },
    { title: 'Bibliothèque', icon: <BookOpen size={18} /> },
    { title: 'Approvisionnement', icon: <ShoppingBag size={18} /> },
    { title: 'Mobile', icon: <Smartphone size={18} /> },
  ];

  const faqs = [
    {
      q: 'Que peut-on gérer avec DigitalCrown ?',
      a: 'Les patients, les rendez-vous, la facturation, les dossiers cliniques, les documents et plusieurs vues de pilotage du cabinet.',
    },
    {
      q: "L'application existe-t-elle sur desktop et mobile ?",
      a: 'DigitalCrown propose une expérience desktop et un companion mobile pour accéder aux vues essentielles.',
    },
    {
      q: 'Peut-on centraliser les dossiers cliniques ?',
      a: 'Oui. Les informations et documents utiles au suivi patient sont regroupés dans des vues structurées.',
    },
    {
      q: 'Comment demander une démonstration ?',
      a: 'Le formulaire ci-dessous permet de demander directement une démonstration de DigitalCrown.',
    },
  ];

  return (
    <div
      className="min-h-screen overflow-x-hidden font-sans"
      style={{
        background: 'radial-gradient(circle at 12% 8%, rgba(56,189,248,.12), transparent 24%), radial-gradient(circle at 88% 24%, rgba(2,132,199,.08), transparent 26%), var(--bg-medical-pearl)',
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

          <div className="hidden items-center gap-7 text-sm font-bold lg:flex" style={{ color: 'var(--text-muted)' }}>
            <a href="#features" className="transition-opacity hover:opacity-70">Fonctionnalités</a>
            <a href="#mobile" className="transition-opacity hover:opacity-70">Mobile</a>
            <a href="#modules" className="transition-opacity hover:opacity-70">Modules</a>
            <a href="#faq" className="transition-opacity hover:opacity-70">FAQ</a>
          </div>

          <div className="flex items-center gap-2">
            <Link to="/login" className="hidden rounded-xl px-3 py-2 text-sm font-bold sm:block" style={{ color: 'var(--text-muted)' }}>
              Connexion
            </Link>
            <Link
              to="/download"
              className="hidden rounded-xl border px-4 py-2.5 text-sm font-black transition-opacity hover:opacity-80 md:inline-flex"
              style={{ ...glassStyle, color: 'var(--text-main)' }}
            >
              Télécharger
            </Link>
            <a
              href="#demo"
              className="inline-flex items-center gap-2 rounded-xl px-4 py-2.5 text-sm font-black text-white shadow-lg transition-opacity hover:opacity-90"
              style={{ background: 'var(--primary)' }}
            >
              Démo <ArrowRight size={15} />
            </a>
          </div>
        </div>
      </nav>

      <main>
        <section className="mx-auto grid max-w-7xl items-center gap-14 px-4 pb-24 pt-16 sm:px-6 sm:pt-20 lg:grid-cols-[0.94fr_1.06fr] lg:gap-16 lg:px-8 lg:pb-28 lg:pt-24">
          <div className="text-center lg:text-left">
            <div
              className="mb-6 inline-flex items-center gap-2 rounded-full border px-4 py-2 text-[11px] font-black uppercase tracking-[0.16em] backdrop-blur-xl"
              style={{ ...glassStyle, color: 'var(--primary)' }}
            >
              <Sparkles size={13} />
              Logiciel dentaire nouvelle génération
            </div>

            <h1 className="text-5xl font-black leading-[0.98] tracking-[-0.045em] sm:text-6xl lg:text-7xl" style={{ color: 'var(--text-main)' }}>
              Le cockpit de votre <span style={{ color: 'var(--primary)' }}>cabinet dentaire.</span>
            </h1>

            <p className="mx-auto mt-6 max-w-2xl text-base font-medium leading-7 sm:text-lg lg:mx-0 lg:max-w-xl" style={{ color: 'var(--text-muted)' }}>
              DigitalCrown centralise les patients, l'agenda, la facturation et les dossiers cliniques dans une interface claire, moderne et pensée pour le quotidien du cabinet.
            </p>

            <div className="mt-8 flex flex-col justify-center gap-3 sm:flex-row lg:justify-start">
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
                <Download size={17} /> Télécharger l'application
              </Link>
            </div>

            <div className="mt-8 grid gap-3 sm:grid-cols-3 lg:max-w-2xl">
              {productPillars.map(({ title, label, icon }) => (
                <div key={title} className="flex min-h-[104px] flex-col rounded-2xl border p-4 text-left backdrop-blur-xl" style={glassStyle}>
                  <div className="mb-3 flex items-center gap-2">
                    <span
                      className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl"
                      style={{ background: 'color-mix(in srgb, var(--primary) 11%, transparent)', color: 'var(--primary)' }}
                    >
                      {icon}
                    </span>
                    <span className="text-[10px] font-black uppercase tracking-[0.18em]" style={{ color: 'var(--primary)' }}>{title}</span>
                  </div>
                  <p className="mt-auto text-xs font-black leading-5 sm:text-[11px] xl:text-xs" style={{ color: 'var(--text-main)' }}>{label}</p>
                </div>
              ))}
            </div>
          </div>

          <MiniProductVisual />
        </section>

        <section className="mx-auto max-w-7xl px-4 py-20 sm:px-6 lg:px-8 lg:py-24">
          <SectionHeading
            eyebrow="Pourquoi DigitalCrown"
            title="Un outil pensé pour piloter le cabinet, pas pour compliquer la journée."
            description="Une expérience structurée autour des tâches que l'équipe utilise réellement, du premier rendez-vous au suivi clinique."
          />
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <InfoCard icon={<LayoutDashboard size={20} />} title="Tout au même endroit" description="Patients, rendez-vous, documents et suivi quotidien dans une seule interface." />
            <InfoCard icon={<Users size={20} />} title="Pensé pour le cabinet" description="Une navigation organisée autour des usages réels d'un cabinet dentaire." />
            <InfoCard icon={<Smartphone size={20} />} title="Companion mobile" description="Des vues mobiles dédiées pour retrouver rapidement les informations utiles." />
            <InfoCard icon={<ShieldCheck size={20} />} title="Clair et structuré" description="Une hiérarchie visuelle cohérente pour retrouver plus vite les actions importantes." />
          </div>
        </section>

        <section id="features" className="mx-auto max-w-7xl px-4 py-20 sm:px-6 lg:px-8 lg:py-24">
          <SectionHeading
            eyebrow="Fonctionnalités"
            title="Les fonctions essentielles, réunies au même endroit."
            description="Une base de travail unique pour organiser l'activité du cabinet et garder les informations importantes accessibles."
          />

          <div className="grid gap-5 lg:grid-cols-2">
            {[
              { icon: <Users size={22} />, title: 'Gérer les patients', desc: 'Créer, retrouver et consulter les dossiers depuis une vue structurée.', bullets: ['Recherche rapide', 'Dossier patient centralisé', 'Historique accessible'] },
              { icon: <CalendarDays size={22} />, title: "Organiser l'agenda", desc: "Visualiser les rendez-vous et garder une lecture claire de l'activité quotidienne.", bullets: ['Vues calendrier', 'Rendez-vous structurés', 'Accès rapide aux patients'] },
              { icon: <WalletCards size={22} />, title: 'Suivre la facturation', desc: 'Retrouver les informations financières utiles dans des écrans dédiés.', bullets: ['Encaissements', 'Suivi comptable', 'Vues de synthèse'] },
              { icon: <Files size={22} />, title: 'Centraliser le clinique', desc: 'Regrouper les documents et informations cliniques autour du dossier patient.', bullets: ['Documents', 'Imagerie', 'Historique clinique'] },
            ].map(item => (
              <article key={item.title} className="overflow-hidden rounded-[30px] border backdrop-blur-xl" style={glassStyle}>
                <div className="grid min-h-[300px] sm:grid-cols-[0.9fr_1.1fr]">
                  <div className="p-6 sm:p-8">
                    <div className="mb-5 flex h-11 w-11 items-center justify-center rounded-2xl" style={{ background: 'color-mix(in srgb, var(--primary) 11%, transparent)', color: 'var(--primary)' }}>
                      {item.icon}
                    </div>
                    <h3 className="text-2xl font-black" style={{ color: 'var(--text-main)' }}>{item.title}</h3>
                    <p className="mt-3 text-sm font-medium leading-6" style={{ color: 'var(--text-muted)' }}>{item.desc}</p>
                    <ul className="mt-5 space-y-2.5">
                      {item.bullets.map(bullet => (
                        <li key={bullet} className="flex items-center gap-2 text-sm font-bold" style={{ color: 'var(--text-main)' }}>
                          <CheckCircle2 size={15} style={{ color: 'var(--primary)' }} /> {bullet}
                        </li>
                      ))}
                    </ul>
                  </div>
                  <div className="m-4 min-h-[220px] rounded-[24px] border border-white/70 bg-white/75 p-4 shadow-inner sm:m-5">
                    <div className="mb-4 flex items-center justify-between">
                      <span className="text-[10px] font-black uppercase tracking-[0.16em] text-slate-400">Aperçu produit</span>
                      <span className="h-2 w-2 rounded-full" style={{ background: 'var(--primary)' }} />
                    </div>
                    <div className="space-y-3">
                      <div className="h-11 rounded-2xl bg-slate-50" />
                      <div className="grid grid-cols-2 gap-3">
                        <div className="h-20 rounded-2xl bg-slate-50" />
                        <div className="h-20 rounded-2xl bg-slate-50" />
                      </div>
                      <div className="h-14 rounded-2xl bg-slate-50" />
                    </div>
                  </div>
                </div>
              </article>
            ))}
          </div>
        </section>

        <section className="mx-auto max-w-7xl px-4 py-20 sm:px-6 lg:px-8 lg:py-24">
          <div className="overflow-hidden rounded-[34px] border p-6 backdrop-blur-2xl sm:p-10 lg:p-12" style={glassStyle}>
            <div className="grid items-center gap-10 lg:grid-cols-2 lg:gap-16">
              <div>
                <p className="text-[11px] font-black uppercase tracking-[0.22em]" style={{ color: 'var(--primary)' }}>Expérience</p>
                <h2 className="mt-3 text-3xl font-black tracking-tight sm:text-4xl" style={{ color: 'var(--text-main)' }}>Une interface qui va à l'essentiel.</h2>
                <p className="mt-4 max-w-xl text-base font-medium leading-7" style={{ color: 'var(--text-muted)' }}>
                  Gagner du temps commence par des écrans plus simples à lire et une navigation plus cohérente.
                </p>
              </div>
              <div className="grid gap-3 sm:grid-cols-2">
                {['Navigation claire', 'Écrans cohérents', 'Hiérarchie visuelle nette', 'Actions fréquentes accessibles'].map((item, index) => (
                  <div key={item} className="flex min-h-[92px] items-center gap-3 rounded-2xl border p-4" style={glassStyle}>
                    <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl text-xs font-black text-white" style={{ background: 'var(--primary)' }}>0{index + 1}</span>
                    <span className="text-sm font-black" style={{ color: 'var(--text-main)' }}>{item}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>

        <section id="mobile" className="mx-auto max-w-7xl px-4 py-20 sm:px-6 lg:px-8 lg:py-24">
          <div className="grid items-center gap-12 lg:grid-cols-[0.95fr_1.05fr] lg:gap-20">
            <div className="order-2 lg:order-1">
              <div className="relative mx-auto w-[280px] rounded-[42px] border p-3 shadow-[0_30px_80px_rgba(15,23,42,0.2)]" style={glassStyle}>
                <div className="min-h-[520px] rounded-[34px] bg-white p-5">
                  <div className="mx-auto mb-6 h-1.5 w-16 rounded-full bg-slate-200" />
                  <div className="mb-6 flex items-center justify-between">
                    <div>
                      <p className="text-[10px] font-black uppercase tracking-wider" style={{ color: 'var(--primary)' }}>DigitalCrown</p>
                      <h3 className="mt-1 text-lg font-black text-slate-800">Companion mobile</h3>
                    </div>
                    <div className="flex h-9 w-9 items-center justify-center rounded-xl text-white" style={{ background: 'var(--primary)' }}><Smartphone size={16} /></div>
                  </div>
                  <div className="space-y-3">
                    {['Agenda', 'Contexte patient', 'Équipe'].map((item, index) => (
                      <div key={item} className="rounded-2xl border border-slate-100 bg-slate-50 p-4">
                        <div className="flex items-center gap-3">
                          <span className="h-8 w-8 rounded-xl" style={{ background: index === 0 ? 'color-mix(in srgb, var(--primary) 16%, white)' : '#e2e8f0' }} />
                          <div>
                            <p className="text-xs font-black text-slate-700">{item}</p>
                            <p className="mt-1 text-[10px] font-medium text-slate-400">Vue mobile dédiée</p>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
            <div className="order-1 text-center lg:order-2 lg:text-left">
              <p className="text-[11px] font-black uppercase tracking-[0.22em]" style={{ color: 'var(--primary)' }}>Companion mobile</p>
              <h2 className="mt-3 text-4xl font-black tracking-tight sm:text-5xl" style={{ color: 'var(--text-main)' }}>L'essentiel du cabinet, aussi sur mobile.</h2>
              <p className="mx-auto mt-5 max-w-xl text-base font-medium leading-7 lg:mx-0" style={{ color: 'var(--text-muted)' }}>
                Retrouvez rapidement les vues mobiles utiles pour suivre l'activité et garder un accès simple aux informations importantes.
              </p>
              <div className="mt-7 space-y-3">
                {['Consultation rapide des vues essentielles', 'Interface dédiée aux petits écrans', 'Continuité avec la version desktop'].map(item => (
                  <div key={item} className="flex items-center justify-center gap-3 text-sm font-bold lg:justify-start" style={{ color: 'var(--text-main)' }}>
                    <CheckCircle2 size={17} style={{ color: 'var(--primary)' }} /> {item}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>

        <section id="modules" className="mx-auto max-w-7xl px-4 py-20 sm:px-6 lg:px-8 lg:py-24">
          <SectionHeading
            eyebrow="Modules"
            title="Un produit structuré autour de modules utiles."
            description="Chaque espace répond à un besoin précis du cabinet, avec le même langage visuel et la même logique de navigation."
          />
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            {modules.map(({ title, icon }) => (
              <div key={title} className="flex min-h-[118px] flex-col justify-between rounded-[24px] border p-5 backdrop-blur-xl" style={glassStyle}>
                <span className="flex h-9 w-9 items-center justify-center rounded-xl" style={{ background: 'color-mix(in srgb, var(--primary) 11%, transparent)', color: 'var(--primary)' }}>{icon}</span>
                <span className="mt-5 text-sm font-black" style={{ color: 'var(--text-main)' }}>{title}</span>
              </div>
            ))}
          </div>
        </section>

        <section id="faq" className="mx-auto max-w-4xl px-4 py-20 sm:px-6 lg:px-8 lg:py-24">
          <SectionHeading
            eyebrow="FAQ"
            title="Questions fréquentes"
            description="Les réponses essentielles avant de découvrir DigitalCrown en démonstration."
          />
          <div className="space-y-3">
            {faqs.map(({ q, a }) => (
              <details key={q} className="group rounded-[22px] border px-5 py-4 backdrop-blur-xl sm:px-6" style={glassStyle}>
                <summary className="flex cursor-pointer list-none items-center justify-between gap-4 text-left text-sm font-black sm:text-base" style={{ color: 'var(--text-main)' }}>
                  {q}
                  <ChevronDown size={18} className="shrink-0 transition-transform group-open:rotate-180" style={{ color: 'var(--primary)' }} />
                </summary>
                <p className="pt-3 text-sm font-medium leading-6" style={{ color: 'var(--text-muted)' }}>{a}</p>
              </details>
            ))}
          </div>
        </section>

        <section id="demo" className="mx-auto max-w-5xl px-4 py-20 sm:px-6 lg:px-8 lg:py-24">
          <div className="overflow-hidden rounded-[36px] border p-6 backdrop-blur-2xl sm:p-9 lg:p-12" style={glassStyle}>
            <div className="grid gap-10 lg:grid-cols-[0.85fr_1.15fr] lg:gap-14">
              <div>
                <p className="text-[11px] font-black uppercase tracking-[0.22em]" style={{ color: 'var(--primary)' }}>Découvrir DigitalCrown</p>
                <h2 className="mt-3 text-4xl font-black tracking-tight" style={{ color: 'var(--text-main)' }}>Prêt à voir le produit en action ?</h2>
                <p className="mt-4 text-base font-medium leading-7" style={{ color: 'var(--text-muted)' }}>
                  Demandez une démonstration pour découvrir les principaux flux de travail du cabinet.
                </p>
                <Link to="/download" className="mt-7 inline-flex items-center gap-2 text-sm font-black" style={{ color: 'var(--primary)' }}>
                  <Download size={16} /> Ou télécharger l'application
                </Link>
              </div>

              {sent ? (
                <div className="flex min-h-[320px] flex-col items-center justify-center rounded-[28px] bg-white/80 p-8 text-center">
                  <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-emerald-100 text-emerald-600"><CheckCircle2 size={26} /></div>
                  <h3 className="mt-5 text-2xl font-black text-slate-800">Demande envoyée</h3>
                  <p className="mt-2 max-w-sm text-sm font-medium leading-6 text-slate-500">Nous vous recontactons pour organiser la démonstration.</p>
                </div>
              ) : (
                <form onSubmit={handleSubmit} className="rounded-[28px] bg-white/80 p-5 shadow-sm sm:p-7">
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
        <div className="mx-auto grid max-w-7xl gap-8 px-4 py-10 sm:px-6 md:grid-cols-[1.4fr_repeat(3,1fr)] lg:px-8">
          <div>
            <div className="flex items-center gap-2.5">
              <span className="flex h-8 w-8 items-center justify-center rounded-xl text-white" style={{ background: 'var(--primary)' }}><Crown size={15} /></span>
              <span className="font-black" style={{ color: 'var(--text-main)' }}>DigitalCrown</span>
            </div>
            <p className="mt-3 max-w-xs text-sm font-medium leading-6" style={{ color: 'var(--text-muted)' }}>Gestion et pilotage du cabinet dentaire dans une interface unifiée.</p>
          </div>
          <div>
            <p className="text-xs font-black uppercase tracking-wider" style={{ color: 'var(--text-main)' }}>Produit</p>
            <div className="mt-3 space-y-2 text-sm font-medium" style={{ color: 'var(--text-muted)' }}><a className="block" href="#features">Fonctionnalités</a><a className="block" href="#mobile">Mobile</a><a className="block" href="#modules">Modules</a></div>
          </div>
          <div>
            <p className="text-xs font-black uppercase tracking-wider" style={{ color: 'var(--text-main)' }}>Découvrir</p>
            <div className="mt-3 space-y-2 text-sm font-medium" style={{ color: 'var(--text-muted)' }}><a className="block" href="#demo">Démo</a><Link className="block" to="/download">Télécharger</Link><a className="block" href="#faq">FAQ</a></div>
          </div>
          <div>
            <p className="text-xs font-black uppercase tracking-wider" style={{ color: 'var(--text-main)' }}>Légal</p>
            <div className="mt-3 space-y-2 text-sm font-medium" style={{ color: 'var(--text-muted)' }}><Link className="block" to="/terms">Conditions</Link><Link className="block" to="/privacy">Confidentialité</Link></div>
          </div>
        </div>
        <div className="mx-auto flex max-w-7xl flex-col gap-2 border-t px-4 py-5 text-xs font-medium sm:flex-row sm:items-center sm:justify-between sm:px-6 lg:px-8" style={{ borderColor: 'var(--glass-border)', color: 'var(--text-muted)' }}>
          <span>© {new Date().getFullYear()} Saninova. Tous droits réservés.</span>
          <span>DigitalCrown</span>
        </div>
      </footer>
    </div>
  );
};
