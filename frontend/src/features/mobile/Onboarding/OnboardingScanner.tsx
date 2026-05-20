import { useState, useEffect, useRef } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Html5QrcodeScanner, Html5QrcodeSupportedFormats } from 'html5-qrcode';
import { Shield, Camera, AlertCircle, CheckCircle2, Loader2, Smartphone, Lock } from 'lucide-react';
import { MobileStorage } from '../../../services/zka/MobileStorage';

/**
 * Résout l'URL du backend :
 * - En production (app servie depuis LAN IP) → window.location.origin
 * - En dev (Vite :5173) → VITE_API_URL ou localhost:8000
 */
function resolveApiBase(): string {
  const origin = window.location.origin;
  const isDevServer = origin.includes('localhost') || origin.includes('127.0.0.1') || origin.includes(':5173');
  if (!isDevServer) return origin;
  return import.meta.env.VITE_API_URL ?? 'http://localhost:8000';
}

const API_BASE = resolveApiBase();

export const OnboardingScanner = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const scannerRef = useRef<Html5QrcodeScanner | null>(null);
  const [phase, setPhase] = useState<'welcome' | 'scanning' | 'claiming' | 'success' | 'error' | 'denied'>('welcome');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Si un token arrive en query param (lien direct depuis QR), on l'échange immédiatement
  useEffect(() => {
    const token = searchParams.get('token');
    if (token) {
      setPhase('claiming');
      exchangeToken(token);
    }
  }, []);

  async function exchangeToken(token: string) {
    try {
      const res = await fetch(`${API_BASE}/api/mobile/claim-token`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail ?? `Erreur ${res.status}`);
      }

      const { publicId, masterKey, access_token } = await res.json();

      if (!/^[0-9a-fA-F]{16}$/.test(publicId) || !/^[0-9a-fA-F]{64}$/.test(masterKey)) {
        throw new Error('Credentials reçus invalides.');
      }
      if (!access_token) throw new Error('JWT mobile manquant dans la réponse.');

      await MobileStorage.saveCredentials({ publicId, masterKey, access_token, api_base_url: API_BASE });
      setPhase('success');
      setTimeout(() => navigate('/mobile/dashboard', { replace: true }), 1500);
    } catch (err: any) {
      setErrorMessage(err.message ?? 'Token invalide ou expiré. Régénérez le QR Code.');
      setPhase('error');
    }
  }

  function startScanner() {
    setPhase('scanning');
  }

  useEffect(() => {
    if (phase !== 'scanning') return;

    const scanner = new Html5QrcodeScanner(
      'reader',
      {
        fps: 10,
        qrbox: { width: 260, height: 260 },
        aspectRatio: 1.0,
        formatsToSupport: [Html5QrcodeSupportedFormats.QR_CODE],
      },
      false,
    );
    scannerRef.current = scanner;

    scanner.render(
      async (decodedText: string) => {
        // Extraire le token depuis l'URL scannée
        let token: string | null = null;
        try {
          const url = new URL(decodedText);
          token = url.searchParams.get('token');
        } catch {
          // format non-URL — invalide
        }

        if (!token) {
          setErrorMessage("QR Code non reconnu. Scannez le code 'Compagnon Mobile' affiché sur votre PC.");
          setPhase('error');
          return;
        }

        await scanner.clear().catch(() => null);
        setPhase('claiming');
        exchangeToken(token);
      },
      (error: any) => {
        if (error?.includes?.('NotAllowedError') || error?.includes?.('Permission denied')) {
          setPhase('denied');
        }
      },
    );

    return () => {
      scannerRef.current?.clear().catch(() => null);
    };
  }, [phase]);

  // ── ÉCRAN D'ACCUEIL ──────────────────────────────────────────────────────────
  if (phase === 'welcome') {
    return (
      <div className="min-h-screen bg-slate-950 text-white flex flex-col items-center justify-center p-8 font-outfit">
        <div className="w-24 h-24 rounded-3xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400 mb-8 shadow-2xl shadow-indigo-500/10">
          <Smartphone size={44} />
        </div>

        <h1 className="text-3xl font-black tracking-tight text-center mb-3">
          Compagnon Mobile
        </h1>
        <p className="text-slate-400 text-sm text-center leading-relaxed mb-2 max-w-xs">
          Synchronisez votre cabinet sur ce téléphone en scannant le QR Code affiché dans la section{' '}
          <span className="text-indigo-400 font-bold">Sécurité Mobile</span> de votre PC.
        </p>

        <div className="w-full max-w-xs mt-8 p-5 bg-white/5 rounded-3xl border border-white/5 flex gap-4 mb-10">
          <Lock size={20} className="text-indigo-400 shrink-0 mt-0.5" />
          <div>
            <p className="text-[10px] font-black text-indigo-400 uppercase tracking-widest mb-1">Zero-Knowledge</p>
            <p className="text-[10px] text-slate-500 leading-relaxed">
              La clé AES-256 reste sur ce téléphone. Aucune donnée lisible ne quitte votre réseau local.
            </p>
          </div>
        </div>

        <button
          onClick={startScanner}
          className="w-full max-w-xs py-5 bg-indigo-600 hover:bg-indigo-500 active:scale-95 rounded-[2rem] font-black text-sm uppercase tracking-widest transition-all shadow-xl shadow-indigo-500/20"
        >
          Scanner le QR Code
        </button>
      </div>
    );
  }

  // ── ÉTAT CLAIMING ────────────────────────────────────────────────────────────
  if (phase === 'claiming') {
    return (
      <div className="min-h-screen bg-slate-950 text-white flex flex-col items-center justify-center gap-6 font-outfit">
        <Loader2 size={48} className="text-indigo-400 animate-spin" />
        <p className="font-black text-slate-300 text-sm uppercase tracking-widest">Vérification en cours…</p>
      </div>
    );
  }

  // ── ÉTAT SUCCESS ─────────────────────────────────────────────────────────────
  if (phase === 'success') {
    return (
      <div className="min-h-screen bg-emerald-600 text-white flex flex-col items-center justify-center gap-6 font-outfit animate-in fade-in duration-500">
        <CheckCircle2 size={72} className="text-white" />
        <p className="font-black text-2xl tracking-tight">Appairage réussi</p>
        <p className="text-emerald-100 text-sm">Redirection vers le tableau de bord…</p>
      </div>
    );
  }

  // ── ÉTAT ERREUR ──────────────────────────────────────────────────────────────
  if (phase === 'error') {
    return (
      <div className="min-h-screen bg-slate-950 text-white flex flex-col items-center justify-center p-8 gap-8 font-outfit">
        <div className="w-20 h-20 rounded-3xl bg-rose-500/10 border border-rose-500/20 flex items-center justify-center">
          <AlertCircle size={40} className="text-rose-400" />
        </div>
        <div className="text-center max-w-xs">
          <p className="font-black text-rose-400 text-lg mb-2">Échec de l'appairage</p>
          <p className="text-[11px] text-slate-400 leading-relaxed">{errorMessage}</p>
        </div>
        <button
          onClick={() => { setErrorMessage(null); setPhase('welcome'); }}
          className="px-8 py-4 bg-white/10 hover:bg-white/20 rounded-2xl font-black text-xs uppercase tracking-widest transition-all"
        >
          Réessayer
        </button>
      </div>
    );
  }

  // ── ÉTAT CAMÉRA REFUSÉE ───────────────────────────────────────────────────────
  if (phase === 'denied') {
    return (
      <div className="min-h-screen bg-slate-950 text-white flex flex-col items-center justify-center p-8 gap-8 font-outfit">
        <Camera size={48} className="text-rose-400" />
        <div className="text-center max-w-xs">
          <p className="font-black text-rose-400 mb-2">Caméra bloquée</p>
          <p className="text-[11px] text-slate-400 leading-relaxed">
            Autorisez l'accès à la caméra dans les réglages de votre navigateur, puis rechargez la page.
          </p>
        </div>
        <button
          onClick={() => window.location.reload()}
          className="px-8 py-4 bg-white text-slate-900 rounded-2xl font-black text-xs uppercase tracking-widest"
        >
          Réessayer
        </button>
      </div>
    );
  }

  // ── ÉCRAN DE SCAN ─────────────────────────────────────────────────────────────
  return (
    <div className="min-h-screen bg-slate-950 text-white p-6 flex flex-col font-outfit">
      <div className="flex items-center gap-3 mb-10">
        <div className="w-10 h-10 rounded-xl bg-indigo-500/20 flex items-center justify-center text-indigo-400 border border-indigo-500/30">
          <Shield size={20} />
        </div>
        <h1 className="text-xl font-black tracking-tight">Appairage Mobile</h1>
      </div>

      <div className="flex-1 flex flex-col items-center justify-center gap-8">
        <div className="w-full max-w-[320px] aspect-square relative rounded-[2.5rem] overflow-hidden border-2 border-white/10 bg-slate-900 shadow-2xl">
          <div id="reader" className="w-full h-full" />
        </div>

        <div className="w-full max-w-[320px] text-center space-y-3">
          <p className="text-sm text-slate-400 font-medium">
            Pointez vers le QR Code affiché sur votre PC dans{' '}
            <span className="text-indigo-400 font-bold">Sécurité Mobile</span>.
          </p>
          <div className="flex items-center justify-center gap-2 text-[10px] font-black text-slate-600 uppercase tracking-widest">
            <Loader2 size={12} className="animate-spin" />
            Recherche du QR Code…
          </div>
        </div>
      </div>

      <div className="mt-auto p-6 bg-white/5 rounded-3xl border border-white/5">
        <div className="flex gap-4">
          <Shield size={24} className="text-indigo-500 shrink-0" />
          <div className="space-y-1">
            <p className="text-[10px] font-black text-indigo-400 uppercase tracking-widest">Sécurité Critique</p>
            <p className="text-[10px] text-slate-500 leading-relaxed">
              La clé est stockée uniquement sur ce téléphone. Ne partagez jamais votre QR code.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
