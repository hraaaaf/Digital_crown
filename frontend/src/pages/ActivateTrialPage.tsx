import React, { useEffect, useMemo, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { AlertCircle, CheckCircle2, Crown, KeyRound, Loader2, Lock, Mail, ShieldCheck, User } from 'lucide-react';
import Logo from '../assets/logo.png';
import { authService } from '../services/auth';

type TrialPreview = {
  email: string;
  nom_complet?: string | null;
  cabinet_name?: string | null;
  trial_days: number;
  expires_at: string;
};

export const ActivateTrialPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const initialCode = searchParams.get('code') ?? '';
  const [code, setCode] = useState(initialCode);
  const [preview, setPreview] = useState<TrialPreview | null>(null);
  const [loadingPreview, setLoadingPreview] = useState(Boolean(initialCode));
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [form, setForm] = useState({
    email: '',
    nom_complet: '',
    cabinet_name: '',
    password: '',
    accept_terms: false,
    accept_privacy: false,
  });

  useEffect(() => {
    if (!initialCode) return;
    let cancelled = false;

    const loadPreview = async () => {
      try {
        const data = await authService.previewTrialCode(initialCode);
        if (cancelled) return;
        setPreview(data);
        setForm((prev) => ({
          ...prev,
          email: data.email ?? prev.email,
          nom_complet: data.nom_complet ?? prev.nom_complet,
          cabinet_name: data.cabinet_name ?? prev.cabinet_name,
        }));
      } catch (err: any) {
        if (!cancelled) {
          setError(err.response?.data?.detail || "Code d'activation invalide.");
        }
      } finally {
        if (!cancelled) setLoadingPreview(false);
      }
    };

    loadPreview();
    return () => {
      cancelled = true;
    };
  }, [initialCode]);

  const expiryLabel = useMemo(() => {
    if (!preview?.expires_at) return '';
    return new Date(preview.expires_at).toLocaleDateString('fr-FR', {
      day: 'numeric',
      month: 'long',
      year: 'numeric',
    });
  }, [preview]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError('');
    setSuccess('');
    try {
      const data = await authService.activateTrial({
        code,
        email: form.email,
        password: form.password,
        nom_complet: form.nom_complet,
        cabinet_name: form.cabinet_name || undefined,
        accept_terms: form.accept_terms,
        accept_privacy: form.accept_privacy,
      });
      setSuccess(data.message || "Essai activé. Vous pouvez maintenant vous connecter.");
    } catch (err: any) {
      setError(err.response?.data?.detail || "Échec de l'activation.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <main className="min-h-screen bg-[linear-gradient(135deg,#eff6ff_0%,#ffffff_48%,#f8fafc_100%)] px-6 py-10 text-slate-900">
      <div className="mx-auto max-w-5xl">
        <div className="mb-10 flex items-center justify-between gap-4">
          <Link to="/landing" className="inline-flex items-center gap-3">
            <img src={Logo} alt="Digital Crown" className="h-10 w-auto" />
            <span className="text-sm font-bold text-slate-600">Retour au site</span>
          </Link>
          <Link to="/download" className="text-sm font-bold text-[#003380] hover:underline">
            Télécharger l'application
          </Link>
        </div>

        <div className="grid gap-8 lg:grid-cols-[1.1fr_0.9fr]">
          <section className="rounded-[2rem] border border-slate-200 bg-white p-8 shadow-sm">
            <div className="mb-8 flex items-center gap-4">
              <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-[#003380] text-white shadow-lg shadow-[#003380]/20">
                <KeyRound size={24} />
              </div>
              <div>
                <p className="text-xs font-black uppercase tracking-[0.2em] text-[#003380]">Activation Après Démo</p>
                <h1 className="mt-1 text-3xl font-black text-slate-950">Activer votre essai</h1>
              </div>
            </div>

            {loadingPreview ? (
              <div className="flex items-center gap-3 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-4 text-sm font-semibold text-slate-600">
                <Loader2 className="animate-spin" size={18} />
                Vérification du code d'activation...
              </div>
            ) : (
              <form onSubmit={handleSubmit} className="space-y-5">
                <div>
                  <label className="mb-2 block text-sm font-bold text-slate-700">Code d'activation</label>
                  <div className="relative">
                    <KeyRound className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
                    <input
                      value={code}
                      onChange={(e) => setCode(e.target.value.toUpperCase())}
                      className="w-full rounded-2xl border border-slate-200 bg-slate-50 py-3 pl-11 pr-4 font-black uppercase tracking-[0.16em] outline-none transition-all focus:border-[#003380] focus:ring-2 focus:ring-[#003380]/10"
                      placeholder="DC-AB12-CD34-EF56"
                      required
                    />
                  </div>
                </div>

                <div className="grid gap-5 sm:grid-cols-2">
                  <div>
                    <label className="mb-2 block text-sm font-bold text-slate-700">Email professionnel</label>
                    <div className="relative">
                      <Mail className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
                      <input
                        type="email"
                        value={form.email}
                        onChange={(e) => setForm((prev) => ({ ...prev, email: e.target.value }))}
                        className="w-full rounded-2xl border border-slate-200 bg-slate-50 py-3 pl-11 pr-4 outline-none transition-all focus:border-[#003380] focus:ring-2 focus:ring-[#003380]/10"
                        required
                      />
                    </div>
                  </div>
                  <div>
                    <label className="mb-2 block text-sm font-bold text-slate-700">Mot de passe</label>
                    <div className="relative">
                      <Lock className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
                      <input
                        type="password"
                        value={form.password}
                        onChange={(e) => setForm((prev) => ({ ...prev, password: e.target.value }))}
                        className="w-full rounded-2xl border border-slate-200 bg-slate-50 py-3 pl-11 pr-4 outline-none transition-all focus:border-[#003380] focus:ring-2 focus:ring-[#003380]/10"
                        placeholder="8 caractères minimum"
                        minLength={8}
                        required
                      />
                    </div>
                  </div>
                  <div>
                    <label className="mb-2 block text-sm font-bold text-slate-700">Nom complet</label>
                    <div className="relative">
                      <User className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
                      <input
                        value={form.nom_complet}
                        onChange={(e) => setForm((prev) => ({ ...prev, nom_complet: e.target.value }))}
                        className="w-full rounded-2xl border border-slate-200 bg-slate-50 py-3 pl-11 pr-4 outline-none transition-all focus:border-[#003380] focus:ring-2 focus:ring-[#003380]/10"
                        required
                      />
                    </div>
                  </div>
                  <div>
                    <label className="mb-2 block text-sm font-bold text-slate-700">Nom du cabinet</label>
                    <div className="relative">
                      <Crown className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
                      <input
                        value={form.cabinet_name}
                        onChange={(e) => setForm((prev) => ({ ...prev, cabinet_name: e.target.value }))}
                        className="w-full rounded-2xl border border-slate-200 bg-slate-50 py-3 pl-11 pr-4 outline-none transition-all focus:border-[#003380] focus:ring-2 focus:ring-[#003380]/10"
                      />
                    </div>
                  </div>
                </div>

                <div className="space-y-3 rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-600">
                  <label className="flex items-start gap-3">
                    <input
                      type="checkbox"
                      checked={form.accept_terms}
                      onChange={(e) => setForm((prev) => ({ ...prev, accept_terms: e.target.checked }))}
                      className="mt-1 h-4 w-4 rounded border-slate-300"
                      required
                    />
                    <span>J'accepte les <Link to="/terms" className="font-bold text-[#003380] hover:underline">CGU</Link>.</span>
                  </label>
                  <label className="flex items-start gap-3">
                    <input
                      type="checkbox"
                      checked={form.accept_privacy}
                      onChange={(e) => setForm((prev) => ({ ...prev, accept_privacy: e.target.checked }))}
                      className="mt-1 h-4 w-4 rounded border-slate-300"
                      required
                    />
                    <span>J'accepte la <Link to="/privacy" className="font-bold text-[#003380] hover:underline">politique de confidentialité</Link>.</span>
                  </label>
                </div>

                {error && (
                  <div className="flex items-start gap-3 rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm font-semibold text-rose-700">
                    <AlertCircle size={18} className="mt-0.5 shrink-0" />
                    <p>{error}</p>
                  </div>
                )}

                {success && (
                  <div className="rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-4 text-sm text-emerald-800">
                    <div className="flex items-start gap-3">
                      <CheckCircle2 size={18} className="mt-0.5 shrink-0" />
                      <div>
                        <p className="font-black">Essai activé</p>
                        <p className="mt-1 font-semibold">{success}</p>
                        <Link to="/login" className="mt-3 inline-flex font-black text-emerald-700 hover:underline">
                          Aller à la connexion
                        </Link>
                      </div>
                    </div>
                  </div>
                )}

                <button
                  type="submit"
                  disabled={submitting}
                  className="inline-flex w-full items-center justify-center gap-3 rounded-2xl bg-[#003380] px-6 py-4 text-sm font-black uppercase tracking-[0.16em] text-white shadow-xl shadow-[#003380]/20 transition-all hover:bg-blue-900 disabled:opacity-60"
                >
                  {submitting ? <Loader2 className="animate-spin" size={18} /> : <ShieldCheck size={18} />}
                  Activer Mon Essai
                </button>
              </form>
            )}
          </section>

          <aside className="rounded-[2rem] border border-slate-200 bg-slate-950 p-8 text-white shadow-2xl shadow-slate-900/10">
            <p className="text-xs font-black uppercase tracking-[0.2em] text-blue-200">Résumé</p>
            <h2 className="mt-3 text-2xl font-black">Ce que débloque ce code</h2>

            <div className="mt-6 space-y-4">
              <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                <p className="text-xs font-black uppercase tracking-[0.16em] text-blue-200">Cabinet</p>
                <p className="mt-2 text-lg font-black">{preview?.cabinet_name || form.cabinet_name || 'À renseigner'}</p>
                <p className="mt-2 text-xs font-semibold leading-relaxed text-slate-300">Le code prépare un brouillon de structure. L'onboarding finalise ensuite sa configuration.</p>
              </div>
              <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                <p className="text-xs font-black uppercase tracking-[0.16em] text-blue-200">Essai</p>
                <p className="mt-2 text-lg font-black">{preview?.trial_days ?? 30} jours gratuits</p>
                {expiryLabel && <p className="mt-1 text-sm font-semibold text-slate-300">Code valable jusqu'au {expiryLabel}</p>}
              </div>
            </div>

            <div className="mt-8 rounded-2xl border border-white/10 bg-gradient-to-br from-blue-500/20 to-white/5 p-5">
              <p className="text-sm font-black">Après activation</p>
              <ol className="mt-3 space-y-2 text-sm text-slate-200">
                <li>1. Connectez-vous dans l'app Windows.</li>
                <li>2. Complétez l'onboarding cabinet.</li>
                <li>3. Installez ensuite le compagnon mobile si besoin.</li>
              </ol>
            </div>
          </aside>
        </div>
      </div>
    </main>
  );
};

export default ActivateTrialPage;
