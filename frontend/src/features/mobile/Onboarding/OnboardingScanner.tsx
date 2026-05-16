import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Html5QrcodeScanner, Html5QrcodeSupportedFormats } from 'html5-qrcode';
import { Shield, Camera, AlertCircle, CheckCircle2, Loader2 } from 'lucide-react';
import { MobileStorage } from '../../../services/zka/MobileStorage';

export const OnboardingScanner = () => {
  const navigate = useNavigate();
  const scannerRef = useRef<Html5QrcodeScanner | null>(null);
  const [status, setStatus] = useState<'idle' | 'scanning' | 'success' | 'error' | 'denied'>('idle');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    // Initialisation du scanner au montage
    const config = {
      fps: 10,
      qrbox: { width: 250, height: 250 },
      aspectRatio: 1.0,
      formatsToSupport: [Html5QrcodeSupportedFormats.QR_CODE]
    };

    const scanner = new Html5QrcodeScanner("reader", config, false);
    scannerRef.current = scanner;

    scanner.render(onScanSuccess, onScanFailure);

    return () => {
      // Nettoyage impératif pour couper le flux caméra
      if (scannerRef.current) {
        scannerRef.current.clear().catch(err => console.error("Erreur cleanup scanner", err));
      }
    };
  }, []);

  async function onScanSuccess(decodedText: string) {
    // 1. Validation du format combiné (ID_16|KEY_64)
    const isValid = /^[0-9a-fA-F]{16}\|[0-9a-fA-F]{64}$/.test(decodedText);
    
    if (!isValid) {
      setErrorMessage("QR Code invalide. Veuillez scanner le code 'Compagnon Mobile' affiché sur votre PC.");
      setStatus('error');
      return;
    }

    try {
      // 2. Parsing du payload
      const [publicId, masterKey] = decodedText.split('|');

      // 3. Arrêt immédiat de la caméra
      if (scannerRef.current) {
        await scannerRef.current.clear();
      }

      // 4. Stockage sécurisé
      await MobileStorage.saveCredentials({ publicId, masterKey });
      
      setStatus('success');
      
      // 5. Redirection
      setTimeout(() => navigate('/mobile/dashboard'), 1500);
      
    } catch (err) {
      setErrorMessage("Échec du stockage des identifiants.");
      setStatus('error');
    }
  }

  function onScanFailure(error: any) {
    // On ignore les échecs de scan (quand rien n'est dans le champ)
    // Sauf si c'est un problème de permission
    if (error?.includes?.("NotAllowedError") || error?.includes?.("Permission denied")) {
      setStatus('denied');
      setErrorMessage("Accès caméra refusé. Veuillez autoriser l'accès dans les réglages de votre navigateur.");
    }
  }

  return (
    <div className="min-h-screen bg-slate-950 text-white p-6 flex flex-col font-outfit">
      {/* Header */}
      <div className="flex items-center gap-3 mb-12">
        <div className="w-10 h-10 rounded-xl bg-indigo-500/20 flex items-center justify-center text-indigo-400 border border-indigo-500/30">
          <Shield size={20} />
        </div>
        <h1 className="text-xl font-black tracking-tight">Appairage Mobile</h1>
      </div>

      <div className="flex-1 flex flex-col items-center justify-center gap-8">
        {/* Scanner Container */}
        <div className="w-full max-w-[320px] aspect-square relative rounded-[2.5rem] overflow-hidden border-2 border-white/10 bg-slate-900 shadow-2xl">
          <div id="reader" className="w-full h-full"></div>
          
          {/* Overlay Status */}
          {status === 'success' && (
            <div className="absolute inset-0 bg-emerald-500 flex flex-col items-center justify-center z-20 animate-in fade-in zoom-in duration-500">
              <CheckCircle2 size={64} className="mb-4 text-white" />
              <p className="font-black text-white text-lg">CLÉ VALIDÉE</p>
            </div>
          )}

          {status === 'denied' && (
            <div className="absolute inset-0 bg-slate-900 flex flex-col items-center justify-center z-20 p-8 text-center animate-in fade-in">
              <Camera size={48} className="mb-4 text-rose-500" />
              <p className="font-bold text-rose-400 mb-2">Caméra Bloquée</p>
              <p className="text-[10px] text-slate-400 leading-relaxed mb-6">
                Pour synchroniser vos données, nous avons besoin de scanner le code QR. Activez la caméra dans les réglages de votre site.
              </p>
              <button 
                onClick={() => window.location.reload()}
                className="px-6 py-2 bg-white text-slate-900 rounded-full font-black text-xs uppercase tracking-widest"
              >
                Réessayer
              </button>
            </div>
          )}
        </div>

        {/* Info & Error Section */}
        <div className="w-full max-w-[320px] text-center">
          {status === 'error' ? (
            <div className="flex items-center gap-3 p-4 rounded-2xl bg-rose-500/10 border border-rose-500/20 text-rose-400 animate-in slide-in-from-top-4">
              <AlertCircle size={20} className="shrink-0" />
              <p className="text-xs font-bold text-left leading-tight">{errorMessage}</p>
            </div>
          ) : (
            <div className="space-y-4">
              <p className="text-sm text-slate-400 font-medium">
                Pointez votre téléphone vers l'écran de votre PC dans la section <span className="text-indigo-400 font-bold">Sécurité Mobile</span>.
              </p>
              <div className="flex items-center justify-center gap-2 text-[10px] font-black text-slate-600 uppercase tracking-widest">
                <Loader2 size={12} className="animate-spin" />
                Recherche du QR Code...
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Footer Security Note */}
      <div className="mt-auto p-6 bg-white/5 rounded-3xl border border-white/5">
        <div className="flex gap-4">
          <Shield size={24} className="text-indigo-500 shrink-0" />
          <div className="space-y-1">
            <p className="text-[10px] font-black text-indigo-400 uppercase tracking-widest">Sécurité Critique</p>
            <p className="text-[10px] text-slate-500 leading-relaxed">
              La clé est stockée uniquement sur ce téléphone. Ne partagez jamais votre QR code avec un tiers.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
