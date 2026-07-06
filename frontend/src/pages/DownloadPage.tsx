import React from 'react';
import { Link } from 'react-router-dom';
import { Download, Laptop, QrCode, ShieldCheck, Smartphone } from 'lucide-react';
import Logo from '../assets/logo.png';

const viteEnv = (import.meta as ImportMeta & { env?: Record<string, string | undefined> }).env;
const windowsInstallerUrl = viteEnv?.VITE_WINDOWS_INSTALLER_URL?.trim() || '';

export const DownloadPage: React.FC = () => {
  const mobileCompanionUrl = '/mobile/onboarding';

  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top_left,_rgba(0,51,128,0.08),_transparent_32%),linear-gradient(180deg,#f8fafc_0%,#ffffff_42%,#eff6ff_100%)] px-6 py-10 text-slate-900">
      <div className="mx-auto max-w-6xl">
        <div className="mb-10 flex items-center justify-between gap-4">
          <Link to="/landing" className="inline-flex items-center gap-3">
            <img src={Logo} alt="Digital Crown" className="h-10 w-auto" />
            <span className="text-sm font-bold text-slate-600">Retour au site</span>
          </Link>
          <Link to="/activate" className="text-sm font-bold text-[#003380] hover:underline">
            J'ai déjà un code d'activation
          </Link>
        </div>

        <section className="rounded-[2.5rem] border border-slate-200 bg-white/90 p-10 shadow-sm">
          <p className="text-xs font-black uppercase tracking-[0.2em] text-[#003380]">Distribution Produit</p>
          <h1 className="mt-4 max-w-3xl text-5xl font-black tracking-tight text-slate-950">
            Téléchargement de l'application principale et du compagnon mobile
          </h1>
          <p className="mt-5 max-w-3xl text-lg font-medium leading-8 text-slate-500">
            DigitalCrown s'installe d'abord sur le poste principal du cabinet sous Windows. Le mobile est un compagnon
            séparé pour l'appairage et l'usage terrain, pas le poste de travail principal.
          </p>
        </section>

        <section className="mt-8 grid gap-8 lg:grid-cols-2">
          <article className="rounded-[2rem] border border-slate-200 bg-slate-950 p-8 text-white shadow-2xl shadow-slate-900/10">
            <div className="flex items-center gap-4">
              <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-white/10">
                <Laptop size={26} />
              </div>
              <div>
                <p className="text-xs font-black uppercase tracking-[0.16em] text-blue-200">App Desktop Principale</p>
                <h2 className="mt-1 text-2xl font-black">Windows Installer</h2>
              </div>
            </div>

            <ul className="mt-8 space-y-3 text-sm font-medium text-slate-200">
              <li>Installation sur le PC principal du cabinet.</li>
              <li>Utilisation complète: patients, agenda, documents, comptabilité.</li>
              <li>Premier login avec votre code d'activation 30 jours après démo.</li>
            </ul>

            {windowsInstallerUrl ? (
              <a
                href={windowsInstallerUrl}
                className="mt-8 inline-flex items-center gap-3 rounded-2xl bg-white px-6 py-4 text-sm font-black uppercase tracking-[0.16em] text-[#003380] transition-all hover:bg-blue-50"
              >
                <Download size={18} />
                Télécharger L'Installateur Windows
              </a>
            ) : (
              <div className="mt-8 rounded-2xl border border-amber-200 bg-amber-50 px-5 py-4 text-sm font-semibold text-amber-900">
                L'URL publique de téléchargement Windows n'est pas encore configurée.
                Définis `VITE_WINDOWS_INSTALLER_URL` pour publier ce bouton.
              </div>
            )}
          </article>

          <article className="rounded-[2rem] border border-slate-200 bg-white p-8 shadow-sm">
            <div className="flex items-center gap-4">
              <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-[#003380]/10 text-[#003380]">
                <Smartphone size={26} />
              </div>
              <div>
                <p className="text-xs font-black uppercase tracking-[0.16em] text-[#003380]">Compagnon Mobile</p>
                <h2 className="mt-1 text-2xl font-black text-slate-950">PWA Mobile</h2>
              </div>
            </div>

            <ul className="mt-8 space-y-3 text-sm font-medium text-slate-600">
              <li>Compagnon terrain, distinct du poste principal.</li>
              <li>Appairage via QR code depuis l'application desktop.</li>
              <li>Installation depuis le navigateur mobile, sans setup Windows.</li>
            </ul>

            <a
              href={mobileCompanionUrl}
              className="mt-8 inline-flex items-center gap-3 rounded-2xl bg-[#003380] px-6 py-4 text-sm font-black uppercase tracking-[0.16em] text-white shadow-lg shadow-[#003380]/20 transition-all hover:bg-blue-900"
            >
              <QrCode size={18} />
              Ouvrir Le Compagnon Mobile
            </a>
          </article>
        </section>

        <section className="mt-8 rounded-[2rem] border border-slate-200 bg-white p-8 shadow-sm">
          <div className="grid gap-6 md:grid-cols-3">
            <div className="rounded-2xl bg-slate-50 p-5">
              <ShieldCheck className="text-[#003380]" size={20} />
              <p className="mt-3 text-sm font-black text-slate-900">1. Démo</p>
              <p className="mt-2 text-sm text-slate-600">L'équipe te remet un code d'activation d'essai valable 30 jours.</p>
            </div>
            <div className="rounded-2xl bg-slate-50 p-5">
              <Download className="text-[#003380]" size={20} />
              <p className="mt-3 text-sm font-black text-slate-900">2. Installation</p>
              <p className="mt-2 text-sm text-slate-600">Le cabinet installe l'app Windows principale sur le poste de travail.</p>
            </div>
            <div className="rounded-2xl bg-slate-50 p-5">
              <QrCode className="text-[#003380]" size={20} />
              <p className="mt-3 text-sm font-black text-slate-900">3. Appairage mobile</p>
              <p className="mt-2 text-sm text-slate-600">Le mobile vient ensuite en second, via la PWA compagnon et le QR d'appairage.</p>
            </div>
          </div>
        </section>
      </div>
    </main>
  );
};

export default DownloadPage;
