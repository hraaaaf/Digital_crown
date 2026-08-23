import { useState, useEffect, useRef } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Html5QrcodeScanner, Html5QrcodeSupportedFormats } from 'html5-qrcode';
import { Shield, Camera, AlertCircle, CheckCircle2, Loader2, Smartphone, Lock, ShieldCheck, ArrowRight, Share, Plus } from 'lucide-react';
import { MobileStorage } from '../../../services/zka/MobileStorage';
import { usePWAInstall } from '../../../hooks/usePWAInstall';
import {
  deriveMasterKey,
  generateClientKeyPair,
  hasPlaintextMasterKey,
} from '../../../services/zka/ecdhPairing';
import Logo from '../../../assets/logo.png';

/**
 * Résout l'URL du backend :
 * - En production (app servie depuis LAN IP) → window.location.origin
 * - En dev (Vite :5173) → VITE_API_URL ou localhost:8000
 */
function resolveApiBase(): string {
  const hostname = window.location.hostname;
  if (hostname === 'localhost' || hostname === '127.0.0.1') {
    return import.meta.env.VITE_API_URL ?? 'http://127.0.0.1:8005';
  }
  return `${window.location.protocol}//${hostname}:8005`;
}

const API_BASE = resolveApiBase();

export const OnboardingScanner = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const scannerRef = useRef<Html5QrcodeScanner | null>(null);
  const [phase, setPhase] = useState<'welcome' | 'scanning' | 'claiming' | 'success' | 'cert-setup' | 'error' | 'denied'>('welcome');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [manualToken, setManualToken] = useState('');
  const [showIOSInstallHint, setShowIOSInstallHint] = useState(false);
  const { isIOS, isInstalled } = usePWAInstall();

  // Si un token arrive en query param (lien direct depuis QR), on l'échange immédiatement
  useEffect(() => {
    // Forcer le thème clair pour l'interface mobile (Désactive complètement le dark mode)
    document.documentElement.dataset.theme = '';
    document.body.dataset.theme = '';

    const token = searchParams.get('token');
    if (token) {
      setPhase('claiming');
      exchangeToken(token);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function exchangeToken(token: string) {
    try {
      // ZKA (S5) : appairage sécurisé ECDH obligatoire — la masterKey ne transite
      // jamais en clair. On génère une paire P-256 et on envoie la clé publique.
      const { privateKey, publicKeyHex } = await generateClientKeyPair();

      const res = await fetch(`${API_BASE}/api/mobile/claim-token`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token, client_public_key_hex: publicKeyHex }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail ?? `Erreur ${res.status}`);
      }

      const payload = await res.json();
      if (hasPlaintextMasterKey(payload)) {
        throw new Error('Reponse d\'appairage non securisee (masterKey en clair refusee).');
      }

      const { publicId, access_token, refresh_token, device_id, server_public_key_hex, encrypted_master_key_hex } = payload;

      if (!server_public_key_hex || !encrypted_master_key_hex) {
        throw new Error('Réponse d\'appairage non sécurisée (ECDH manquant).');
      }

      const masterKey = await deriveMasterKey(
        privateKey,
        server_public_key_hex,
        encrypted_master_key_hex,
      );

      if (!/^[0-9a-fA-F]{16}$/.test(publicId) || !/^[0-9a-fA-F]{64}$/.test(masterKey)) {
        throw new Error('Credentials reçus invalides.');
      }
      if (!access_token || !refresh_token || !device_id) throw new Error('Session mobile durable incomplète.');

      await MobileStorage.saveCredentials({ publicId, masterKey, access_token, refresh_token, device_id, api_base_url: API_BASE });
      setPhase('success');
      // Si déjà en HTTPS → dashboard direct. Sinon → proposer l'install cert (optionnel).
      const alreadySecure = window.isSecureContext;
      const certSkipped = localStorage.getItem('dc_cert_skipped') === '1';
      setTimeout(() => {
        if (alreadySecure || certSkipped) navigate('/mobile/dashboard', { replace: true });
        else setPhase('cert-setup');
      }, 1200);
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

    try {
      if (!window.isSecureContext && window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
        setErrorMessage("Accès caméra bloqué (nécessite HTTPS). Vous pouvez utiliser le code à 6 chiffres.");
        setPhase('error');
        return;
      }

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
    } catch (err: any) {
      console.error(err);
      setErrorMessage("La caméra n'est pas supportée sur ce navigateur ou cette connexion. Utilisez le code.");
      setPhase('error');
    }

    return () => {
      scannerRef.current?.clear().catch(() => null);
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [phase]);

  // ── ÉCRAN D'ACCUEIL ──────────────────────────────────────────────────────────
  if (phase === 'welcome') {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center p-8 font-outfit relative overflow-hidden" style={{ backgroundColor: '#f8fafc', color: '#0f172a' }}>
        <div className="document-watermark absolute inset-0 z-0 pointer-events-none" />
        
        <div className="z-10 w-full max-w-xs flex flex-col items-center">
          <img src={Logo} alt="Digital Crown" className="w-48 h-auto object-contain mb-8 drop-shadow-md" />

          <div className="w-24 h-24 rounded-3xl bg-primary/10 border border-primary/20 flex items-center justify-center text-primary mb-8 shadow-elite">
            <Smartphone size={44} />
          </div>

          <h1 className="text-3xl font-black tracking-tight text-center mb-3">
            Compagnon Mobile
          </h1>
          <p className="text-text-muted text-sm text-center leading-relaxed mb-2 font-medium">
            Synchronisez votre cabinet sur ce téléphone en scannant le QR Code affiché dans la section{' '}
            <span className="text-primary font-black">Sécurité Mobile</span> de votre PC.
          </p>

          {isIOS && !isInstalled && (
            <div className="w-full mt-6 p-5 rounded-3xl shadow-elite" style={{ backgroundColor: 'var(--glass-bg)', borderColor: 'var(--glass-border)', borderWidth: '1px' }}>
              <div className="flex gap-3">
                <Smartphone size={20} className="text-primary shrink-0 mt-0.5" />
                <div className="flex-1">
                  <p className="text-[10px] font-black text-primary uppercase tracking-widest mb-1">Étape 1 — Installez d'abord l'app</p>
                  <p className="text-[11px] text-text-muted leading-relaxed font-bold mb-3">
                    Sur iPhone, scannez le QR depuis l'app installée sur votre écran d'accueil, pas depuis Safari — sinon la connexion ne sera pas conservée quand vous rouvrirez l'icône.
                  </p>
                  <button
                    type="button"
                    onClick={() => setShowIOSInstallHint(!showIOSInstallHint)}
                    className="text-[11px] font-black text-primary underline underline-offset-2"
                  >
                    Comment installer sur iPhone ?
                  </button>
                  {showIOSInstallHint && (
                    <div className="mt-3 space-y-2">
                      <p className="flex items-center gap-2 text-[11px] font-bold text-text-muted">
                        <span className="w-5 h-5 rounded-full bg-primary/10 text-primary text-[10px] font-black flex items-center justify-center shrink-0">1</span>
                        Appuyez sur <Share size={14} className="text-primary" /> dans la barre Safari
                      </p>
                      <p className="flex items-center gap-2 text-[11px] font-bold text-text-muted">
                        <span className="w-5 h-5 rounded-full bg-primary/10 text-primary text-[10px] font-black flex items-center justify-center shrink-0">2</span>
                        Choisissez « Sur l'écran d'accueil » <Plus size={14} className="text-primary" />
                      </p>
                      <p className="flex items-center gap-2 text-[11px] font-bold text-text-muted">
                        <span className="w-5 h-5 rounded-full bg-primary/10 text-primary text-[10px] font-black flex items-center justify-center shrink-0">3</span>
                        Ouvrez l'icône installée puis scannez le QR ci-dessous
                      </p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          <div className="w-full mt-6 p-5 rounded-3xl flex gap-4 mb-10 shadow-elite" style={{ backgroundColor: 'var(--glass-bg)', borderColor: 'var(--glass-border)', borderWidth: '1px' }}>
            <Lock size={20} className="text-primary shrink-0 mt-0.5" />
            <div>
              <p className="text-[10px] font-black text-primary uppercase tracking-widest mb-1">Zero-Knowledge</p>
              <p className="text-[10px] text-text-muted leading-relaxed font-bold">
                La clé AES-256 reste sur ce téléphone. Aucune donnée lisible ne quitte votre réseau local.
              </p>
            </div>
          </div>

          <button
            onClick={startScanner}
            className="w-full py-4 bg-primary hover:opacity-90 active:scale-95 rounded-2xl font-black text-sm text-white uppercase tracking-widest transition-all shadow-elite-hover mb-4"
          >
            Scanner le QR Code
          </button>

          <div className="w-full flex items-center justify-center gap-4 mb-4">
            <div className="h-px bg-border-main flex-1"></div>
            <span className="text-xs font-bold text-text-muted uppercase tracking-widest">OU</span>
            <div className="h-px bg-border-main flex-1"></div>
          </div>

          <div className="w-full flex gap-2">
            <input 
              type="text" 
              placeholder="Code à 6 chiffres" 
              className="flex-1 bg-white dark:bg-slate-900 border border-border-main rounded-2xl px-4 py-3 text-center font-black tracking-widest text-lg outline-none focus:border-primary transition-all"
              value={manualToken}
              onChange={e => setManualToken(e.target.value)}
              maxLength={6}
            />
            <button 
              onClick={() => {
                if (manualToken.length >= 5) {
                  setPhase('claiming');
                  exchangeToken(manualToken);
                }
              }}
              className="px-6 py-3 bg-slate-800 text-white font-bold rounded-2xl active:scale-95 transition-transform"
            >
              OK
            </button>
          </div>
        </div>
      </div>
    );
  }

  // ── ÉTAT CLAIMING ────────────────────────────────────────────────────────────
  if (phase === 'claiming') {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center gap-6 font-outfit relative" style={{ backgroundColor: '#f8fafc', color: '#0f172a' }}>
        <div className="document-watermark absolute inset-0 z-0 pointer-events-none" />
        <Loader2 size={48} className="text-primary animate-spin z-10" />
        <p className="font-black text-text-muted text-sm uppercase tracking-widest z-10">Vérification en cours…</p>
      </div>
    );
  }

  // ── ÉTAT SUCCESS ─────────────────────────────────────────────────────────────
  if (phase === 'success') {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center gap-6 font-outfit animate-in fade-in duration-500 relative" style={{ backgroundColor: 'var(--bg-medical-pearl)', color: 'var(--primary)' }}>
        <div className="document-watermark absolute inset-0 z-0 pointer-events-none opacity-20" />
        <CheckCircle2 size={72} className="text-emerald-500 z-10" />
        <p className="font-black text-2xl tracking-tight z-10 text-emerald-600">Appairage réussi</p>
        <p className="text-emerald-700 font-bold text-sm z-10">Redirection vers le tableau de bord…</p>
      </div>
    );
  }

  // ── ACTIVATION HTTPS (optionnel) ─────────────────────────────────────────────
  if (phase === 'cert-setup') {
    const certUrl = `${API_BASE}/api/mobile/ca-cert`;
    const skipAndGo = () => {
      localStorage.setItem('dc_cert_skipped', '1');
      navigate('/mobile/dashboard', { replace: true });
    };

    return (
      <div className="min-h-screen flex flex-col p-6 font-outfit relative" style={{ backgroundColor: '#f8fafc', color: '#0f172a' }}>
        <div className="document-watermark absolute inset-0 z-0 pointer-events-none" />
        <div className="z-10 flex-1 flex flex-col max-w-xs mx-auto w-full justify-center">

          <div className="flex flex-col items-center mb-8">
            <div className="w-20 h-20 rounded-3xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center mb-4">
              <ShieldCheck size={40} className="text-emerald-500" />
            </div>
            <h2 className="text-2xl font-black tracking-tight text-center mb-2">Connexion sécurisée</h2>
            <p className="text-xs text-text-muted font-medium text-center leading-relaxed">
              Activez HTTPS pour chiffrer vos données sur le réseau local.{' '}
              <span className="font-black text-primary">Une seule fois.</span>
            </p>
          </div>

          {/* Étapes condensées */}
          <div className="w-full p-4 rounded-2xl bg-white border border-border-main shadow-elite mb-6 space-y-3">
            {[
              'Appuyez sur « Activer la sécurité »',
              'Autorisez le téléchargement du profil',
              'Réglages → Installer le profil → Installer',
              'Réglages → À propos → Certificats → Activer',
            ].map((step, i) => (
              <div key={i} className="flex gap-3 items-center">
                <span className="w-5 h-5 rounded-full bg-primary/10 text-primary text-[10px] font-black flex items-center justify-center shrink-0">
                  {i + 1}
                </span>
                <p className="text-[11px] text-text-muted font-medium">{step}</p>
              </div>
            ))}
          </div>

          <a
            href={certUrl}
            className="w-full py-4 mb-3 bg-emerald-600 hover:opacity-90 active:scale-95 rounded-2xl font-black text-sm text-white uppercase tracking-widest transition-all shadow-elite flex items-center justify-center gap-2"
          >
            <ShieldCheck size={16} />
            Activer la sécurité
          </a>

          <button
            onClick={skipAndGo}
            className="w-full py-3 text-xs font-bold text-text-muted hover:text-text-main transition-colors flex items-center justify-center gap-1"
          >
            Accéder au cabinet sans HTTPS
            <ArrowRight size={14} />
          </button>
        </div>
      </div>
    );
  }

  // ── ÉTAT ERREUR ──────────────────────────────────────────────────────────────
  if (phase === 'error') {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center p-8 gap-8 font-outfit relative" style={{ backgroundColor: '#f8fafc', color: '#0f172a' }}>
        <div className="document-watermark absolute inset-0 z-0 pointer-events-none" />
        <div className="z-10 flex flex-col items-center">
          <div className="w-20 h-20 rounded-3xl bg-rose-500/10 border border-rose-500/20 flex items-center justify-center mb-6">
            <AlertCircle size={40} className="text-rose-500" />
          </div>
          <div className="text-center max-w-xs mb-8">
            <p className="font-black text-rose-500 text-lg mb-2">Échec de l'appairage</p>
            <p className="text-[11px] text-text-muted font-bold leading-relaxed">{errorMessage}</p>
          </div>
          <button
            onClick={() => { setErrorMessage(null); setPhase('welcome'); }}
            className="px-8 py-4 bg-card border border-border-main hover:bg-border-main rounded-2xl font-black text-xs text-text-main uppercase tracking-widest transition-all shadow-elite"
          >
            Réessayer
          </button>
        </div>
      </div>
    );
  }

  // ── ÉTAT CAMÉRA REFUSÉE ───────────────────────────────────────────────────────
  if (phase === 'denied') {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center p-8 gap-8 font-outfit relative" style={{ backgroundColor: '#f8fafc', color: '#0f172a' }}>
        <div className="document-watermark absolute inset-0 z-0 pointer-events-none" />
        <div className="z-10 flex flex-col items-center">
          <Camera size={48} className="text-rose-500 mb-6" />
          <div className="text-center max-w-xs mb-8">
            <p className="font-black text-rose-500 mb-2 text-lg">Caméra bloquée</p>
            <p className="text-[11px] text-text-muted font-bold leading-relaxed">
              Autorisez l'accès à la caméra dans les réglages de votre navigateur, puis rechargez la page.
            </p>
          </div>
          <button
            onClick={() => window.location.reload()}
            className="px-8 py-4 bg-primary hover:opacity-90 rounded-2xl font-black text-xs text-white uppercase tracking-widest shadow-elite"
          >
            Réessayer
          </button>
        </div>
      </div>
    );
  }

  // ── ÉCRAN DE SCAN ─────────────────────────────────────────────────────────────
  return (
    <div className="min-h-screen p-6 flex flex-col font-outfit relative" style={{ backgroundColor: '#f8fafc', color: '#0f172a' }}>
      <div className="document-watermark absolute inset-0 z-0 pointer-events-none" />
      <div className="z-10 flex-1 flex flex-col">
        <div className="flex items-center justify-center gap-3 mb-10 mt-4">
          <img src={Logo} alt="Digital Crown" className="w-36 h-auto object-contain drop-shadow-sm" />
        </div>

        <div className="flex-1 flex flex-col items-center justify-center gap-8">
          <div className="w-full max-w-[320px] aspect-square relative rounded-[2.5rem] overflow-hidden border border-border-main bg-card shadow-elite">
            <div id="reader" className="w-full h-full" />
          </div>

          <div className="w-full max-w-[320px] text-center space-y-3">
            <p className="text-sm text-text-muted font-bold">
              Pointez vers le QR Code affiché sur votre PC dans{' '}
              <span className="text-primary font-black">Sécurité Mobile</span>.
            </p>
            <div className="flex items-center justify-center gap-2 text-[10px] font-black text-text-muted uppercase tracking-widest">
              <Loader2 size={12} className="animate-spin text-primary" />
              Recherche du QR Code…
            </div>
          </div>
        </div>

        <div className="mt-auto p-6 rounded-3xl shadow-elite" style={{ backgroundColor: 'var(--glass-bg)', borderColor: 'var(--glass-border)', borderWidth: '1px' }}>
          <div className="flex gap-4">
            <Shield size={24} className="text-primary shrink-0" />
            <div className="space-y-1">
              <p className="text-[10px] font-black text-primary uppercase tracking-widest">Sécurité Critique</p>
              <p className="text-[10px] text-text-muted font-medium leading-relaxed">
                La clé est stockée uniquement sur ce téléphone. Ne partagez jamais votre QR code.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
