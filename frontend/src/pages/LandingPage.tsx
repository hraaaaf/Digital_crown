import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Calendar, Users, FileText, BarChart3, Shield, Zap,
  Star, CheckCircle, ArrowRight, Mail, Phone, Building2, MessageSquare,
  Loader2, Sparkles, Crown
} from 'lucide-react';
import { api } from '../services/api';
import toast from 'react-hot-toast';

// ── helpers ──────────────────────────────────────────────────────────────────

const cn = (...classes: (string | false | undefined)[]) => classes.filter(Boolean).join(' ');

// ── sub-components ────────────────────────────────────────────────────────────

const Feature: React.FC<{ icon: React.ReactNode; title: string; desc: string }> = ({ icon, title, desc }) => (
  <div className="bg-white/70 backdrop-blur-sm border border-white rounded-3xl p-6 hover:shadow-xl hover:-translate-y-1 transition-all duration-300 group">
    <div className="w-12 h-12 rounded-2xl bg-[#003380]/10 flex items-center justify-center mb-4 group-hover:bg-[#003380]/20 transition-colors">
      {icon}
    </div>
    <h3 className="font-black text-slate-800 mb-2">{title}</h3>
    <p className="text-slate-500 text-sm leading-relaxed">{desc}</p>
  </div>
);

const PlanCard: React.FC<{
  name: string; price: string; dentists: string; secretaries: string;
  features: string[]; highlight?: boolean;
}> = ({ name, price, dentists, secretaries, features, highlight }) => (
  <div className={cn(
    "rounded-3xl p-8 border flex flex-col gap-6 transition-all duration-300 hover:-translate-y-1",
    highlight
      ? "bg-[#003380] text-white border-[#003380] shadow-2xl shadow-[#003380]/30"
      : "bg-white/80 text-slate-800 border-white shadow-lg hover:shadow-xl"
  )}>
    <div>
      <p className={cn("text-xs font-black uppercase tracking-widest mb-1", highlight ? "text-blue-200" : "text-[#003380]")}>{name}</p>
      <p className={cn("text-4xl font-black", highlight ? "text-white" : "text-slate-800")}>{price}</p>
      <p className={cn("text-sm mt-1", highlight ? "text-blue-200" : "text-slate-400")}>/ an</p>
    </div>
    <div className={cn("text-sm space-y-1", highlight ? "text-blue-100" : "text-slate-500")}>
      <p>{dentists}</p>
      <p>{secretaries}</p>
    </div>
    <ul className="space-y-2 flex-1">
      {features.map((f, i) => (
        <li key={i} className="flex items-start gap-2 text-sm">
          <CheckCircle size={14} className={cn("mt-0.5 shrink-0", highlight ? "text-blue-300" : "text-emerald-500")} />
          <span className={highlight ? "text-blue-50" : "text-slate-600"}>{f}</span>
        </li>
      ))}
    </ul>
    <Link
      to="/register"
      className={cn(
        "block text-center py-3 rounded-2xl font-black text-sm transition-all",
        highlight
          ? "bg-white text-[#003380] hover:bg-blue-50"
          : "bg-[#003380] text-white hover:bg-blue-900"
      )}
    >
      Commencer
    </Link>
  </div>
);

// ── main component ─────────────────────────────────────────────────────────

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
      toast.success('Demande envoyée ! Nous vous contacterons sous 24h.');
    } catch {
      toast.error('Erreur lors de l\'envoi. Réessayez.');
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50/30 to-indigo-50/20 font-sans">

      {/* ── NAVBAR ── */}
      <nav className="sticky top-0 z-50 bg-white/80 backdrop-blur-xl border-b border-slate-100 shadow-sm">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 bg-[#003380] rounded-xl flex items-center justify-center">
              <Crown size={18} className="text-white" />
            </div>
            <span className="font-black text-xl text-[#003380]">DigitalCrown</span>
          </div>
          <div className="hidden md:flex items-center gap-8 text-sm font-bold text-slate-500">
            <a href="#features" className="hover:text-[#003380] transition-colors">Fonctionnalités</a>
            <a href="#pricing" className="hover:text-[#003380] transition-colors">Tarifs</a>
            <a href="#demo" className="hover:text-[#003380] transition-colors">Démo</a>
          </div>
          <div className="flex items-center gap-3">
            <Link to="/login" className="text-sm font-bold text-slate-600 hover:text-[#003380] transition-colors px-4 py-2">
              Connexion
            </Link>
            <a href="#demo" className="bg-[#003380] text-white text-sm font-black px-5 py-2.5 rounded-xl hover:bg-blue-900 transition-colors shadow-lg shadow-[#003380]/20">
              Demander une démo
            </a>
          </div>
        </div>
      </nav>

      {/* ── HERO ── */}
      <section className="max-w-7xl mx-auto px-6 pt-24 pb-20 text-center">
        <div className="inline-flex items-center gap-2 bg-[#003380]/10 text-[#003380] text-xs font-black px-4 py-2 rounded-full mb-8 border border-[#003380]/20">
          <Sparkles size={12} />
          Logiciel dentaire nouvelle génération
        </div>
        <h1 className="text-5xl md:text-7xl font-black text-slate-900 leading-tight mb-6 tracking-tight">
          Gérez votre cabinet<br />
          <span className="text-[#003380]">avec intelligence.</span>
        </h1>
        <p className="text-xl text-slate-500 max-w-2xl mx-auto leading-relaxed mb-10 font-medium">
          DigitalCrown centralise patients, agenda, facturation et dossiers cliniques dans une interface moderne conçue pour les dentistes algériens.
        </p>
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <a
            href="#demo"
            className="inline-flex items-center gap-2 bg-[#003380] text-white font-black px-8 py-4 rounded-2xl hover:bg-blue-900 transition-all hover:-translate-y-0.5 shadow-2xl shadow-[#003380]/30 text-base"
          >
            Demander une démo gratuite <ArrowRight size={18} />
          </a>
          <Link
            to="/login"
            className="inline-flex items-center gap-2 bg-white text-slate-700 font-black px-8 py-4 rounded-2xl hover:bg-slate-50 transition-all border border-slate-200 shadow-sm text-base"
          >
            Se connecter
          </Link>
        </div>

        {/* Social proof */}
        <div className="mt-12 flex flex-col sm:flex-row items-center justify-center gap-8 text-slate-400">
          {[
            { val: '200+', label: 'Cabinets actifs' },
            { val: '50k+', label: 'Dossiers patients' },
            { val: '4.9', label: 'Note moyenne', icon: <Star size={12} className="text-amber-400 inline" /> },
          ].map(({ val, label, icon }) => (
            <div key={label} className="text-center">
              <p className="text-2xl font-black text-slate-700">{val} {icon}</p>
              <p className="text-xs font-bold uppercase tracking-widest mt-0.5">{label}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── FEATURES ── */}
      <section id="features" className="max-w-7xl mx-auto px-6 py-20">
        <div className="text-center mb-14">
          <h2 className="text-4xl font-black text-slate-900 mb-4">Tout ce dont vous avez besoin</h2>
          <p className="text-slate-500 font-medium max-w-xl mx-auto">Un seul outil pour piloter votre cabinet de A à Z.</p>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          <Feature
            icon={<Users size={22} className="text-[#003380]" />}
            title="Dossiers patients"
            desc="Créez, recherchez et gérez tous vos dossiers patients en quelques secondes. Import CSV en masse inclus."
          />
          <Feature
            icon={<Calendar size={22} className="text-[#003380]" />}
            title="Agenda intelligent"
            desc="Vue jour / semaine / mois, détection des conflits en temps réel, rappels SMS automatiques."
          />
          <Feature
            icon={<FileText size={22} className="text-[#003380]" />}
            title="Dossiers cliniques"
            desc="Céphalométrie, orthodontie, actes — tout en un. Export PDF soigné avec votre en-tête cabinet."
          />
          <Feature
            icon={<BarChart3 size={22} className="text-[#003380]" />}
            title="Comptabilité & Facturation"
            desc="Suivi des honoraires, export CSV/PDF, relances automatiques des impayés."
          />
          <Feature
            icon={<Shield size={22} className="text-[#003380]" />}
            title="Sécurité & Multi-tenant"
            desc="Chaque cabinet dispose d'un espace isolé. Permissions granulaires par sous-compte (secrétaire, associé)."
          />
          <Feature
            icon={<Zap size={22} className="text-[#003380]" />}
            title="IA intégrée"
            desc="Assistant clinique intelligent, analyse céphalométrique guidée, suggestions de traitement."
          />
        </div>
      </section>

      {/* ── PRICING ── */}
      <section id="pricing" className="max-w-7xl mx-auto px-6 py-20">
        <div className="text-center mb-14">
          <h2 className="text-4xl font-black text-slate-900 mb-4">Plans adaptés à chaque cabinet</h2>
          <p className="text-slate-500 font-medium">Tous les plans incluent les mises à jour et le support.</p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 items-start">
          <PlanCard
            name="Gold"
            price="4 900 MAD"
            dentists="1 dentiste"
            secretaries="2 secrétaires"
            features={[
              'Dossiers patients illimités',
              'Agenda complet',
              'Facturation & comptabilité',
              'Dossiers cliniques',
              'Support email',
            ]}
          />
          <PlanCard
            name="Premium"
            price="9 900 MAD"
            dentists="2 dentistes"
            secretaries="6 secrétaires"
            features={[
              'Tout Gold, plus…',
              'Vue multi-praticien',
              'Rappels SMS patients',
              'Import / Export avancé',
              'Support prioritaire',
            ]}
            highlight
          />
          <PlanCard
            name="Elite"
            price="17 900 MAD"
            dentists="Dentistes illimités"
            secretaries="Secrétaires illimitées"
            features={[
              'Tout Premium, plus…',
              'IA clinique avancée',
              'Analytics & tableaux de bord',
              'Science Hub orthodontique',
              'Support dédié 24/7',
            ]}
          />
        </div>
      </section>

      {/* ── DEMO FORM ── */}
      <section id="demo" className="max-w-3xl mx-auto px-6 py-20">
        <div className="bg-white/80 backdrop-blur-xl border border-white rounded-[2.5rem] shadow-2xl p-10">
          {sent ? (
            <div className="text-center py-10">
              <div className="w-16 h-16 bg-emerald-100 rounded-3xl flex items-center justify-center mx-auto mb-4">
                <CheckCircle size={32} className="text-emerald-500" />
              </div>
              <h3 className="text-2xl font-black text-slate-800 mb-2">Demande envoyée !</h3>
              <p className="text-slate-500 font-medium">Notre équipe vous contactera sous 24h pour organiser votre démo personnalisée.</p>
            </div>
          ) : (
            <>
              <div className="text-center mb-8">
                <h2 className="text-3xl font-black text-slate-900 mb-2">Demandez votre démo gratuite</h2>
                <p className="text-slate-500 font-medium">Un de nos experts vous contacte sous 24h.</p>
              </div>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="relative">
                    <Users size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" />
                    <input
                      required
                      placeholder="Votre nom *"
                      className="w-full pl-10 pr-4 py-3.5 border border-slate-200 rounded-2xl font-bold text-sm outline-none focus:ring-2 focus:ring-[#003380]/20 focus:border-[#003380]/40 transition-all"
                      value={form.nom}
                      onChange={e => setForm(f => ({ ...f, nom: e.target.value }))}
                    />
                  </div>
                  <div className="relative">
                    <Mail size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" />
                    <input
                      required
                      type="email"
                      placeholder="Email professionnel *"
                      className="w-full pl-10 pr-4 py-3.5 border border-slate-200 rounded-2xl font-bold text-sm outline-none focus:ring-2 focus:ring-[#003380]/20 focus:border-[#003380]/40 transition-all"
                      value={form.email}
                      onChange={e => setForm(f => ({ ...f, email: e.target.value }))}
                    />
                  </div>
                  <div className="relative">
                    <Building2 size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" />
                    <input
                      required
                      placeholder="Nom du cabinet *"
                      className="w-full pl-10 pr-4 py-3.5 border border-slate-200 rounded-2xl font-bold text-sm outline-none focus:ring-2 focus:ring-[#003380]/20 focus:border-[#003380]/40 transition-all"
                      value={form.cabinet}
                      onChange={e => setForm(f => ({ ...f, cabinet: e.target.value }))}
                    />
                  </div>
                  <div className="relative">
                    <Phone size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" />
                    <input
                      type="tel"
                      placeholder="Téléphone"
                      className="w-full pl-10 pr-4 py-3.5 border border-slate-200 rounded-2xl font-bold text-sm outline-none focus:ring-2 focus:ring-[#003380]/20 focus:border-[#003380]/40 transition-all"
                      value={form.telephone}
                      onChange={e => setForm(f => ({ ...f, telephone: e.target.value }))}
                    />
                  </div>
                </div>
                <div className="relative">
                  <MessageSquare size={16} className="absolute left-4 top-4 text-slate-400" />
                  <textarea
                    rows={3}
                    placeholder="Message (optionnel)"
                    className="w-full pl-10 pr-4 py-3.5 border border-slate-200 rounded-2xl font-bold text-sm outline-none focus:ring-2 focus:ring-[#003380]/20 focus:border-[#003380]/40 transition-all resize-none"
                    value={form.message}
                    onChange={e => setForm(f => ({ ...f, message: e.target.value }))}
                  />
                </div>
                <button
                  type="submit"
                  disabled={sending}
                  className="w-full py-4 bg-[#003380] text-white font-black rounded-2xl hover:bg-blue-900 transition-all hover:-translate-y-0.5 shadow-xl shadow-[#003380]/20 flex items-center justify-center gap-2 disabled:opacity-60"
                >
                  {sending ? <Loader2 size={18} className="animate-spin" /> : <ArrowRight size={18} />}
                  {sending ? 'Envoi en cours…' : 'Envoyer ma demande'}
                </button>
              </form>
            </>
          )}
        </div>
      </section>

      {/* ── FOOTER ── */}
      <footer className="border-t border-slate-100 bg-white/60 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-6 py-8 flex flex-col sm:flex-row items-center justify-between gap-4 text-sm text-slate-400">
          <div className="flex items-center gap-2 font-black text-slate-600">
            <Crown size={16} className="text-[#003380]" />
            DigitalCrown — Saninova
          </div>
          <div className="flex gap-6">
            <Link to="/terms" className="hover:text-slate-600 transition-colors">Mentions légales</Link>
            <Link to="/privacy" className="hover:text-slate-600 transition-colors">Confidentialité</Link>
          </div>
          <p>© {new Date().getFullYear()} Saninova. Tous droits réservés.</p>
        </div>
      </footer>

    </div>
  );
};
