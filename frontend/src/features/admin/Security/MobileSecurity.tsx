import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import toast from 'react-hot-toast';
import { Shield, Smartphone, RefreshCw, Eye, AlertTriangle, CheckCircle2 } from 'lucide-react';
import { api } from '../../../services/api';

export const MobileSecurity = () => {
  const [qrCode, setQrCode] = useState<string | null>(null);
  const [tokenCode, setTokenCode] = useState<string | null>(null);
  const [isVisible, setIsVisible] = useState(false);
  const [countdown, setCountdown] = useState(0);
  const [isRevoking, setIsRevoking] = useState(false);
  const [status, setStatus] = useState<{ type: 'success' | 'error', msg: string } | null>(null);

  // Gestion du timer d'auto-masquage
  useEffect(() => {
    let timer: ReturnType<typeof setInterval>;
    if (isVisible && countdown > 0) {
      timer = setInterval(() => {
        setCountdown(prev => prev - 1);
      }, 1000);
    } else if (countdown === 0) {
      setIsVisible(false);
    }
    return () => clearInterval(timer);
  }, [isVisible, countdown]);

  const fetchQrCode = async () => {
    try {
      const response = await api.get('/admin/zka-key-qr');
      setQrCode(response.data.qr_code);
      setTokenCode(response.data.token_code);
      setIsVisible(true);
      setCountdown(30); // 30 secondes de visibilité
    } catch (error) {
      console.error("Erreur lors de la récupération du QR Code", error);
      toast.error("Impossible de générer le QR code — vérifiez la configuration serveur.");
    }
  };

  const handleRevoke = async () => {
    if (!window.confirm("Êtes-vous sûr de vouloir révoquer l'accès mobile ? Cela déconnectera immédiatement tous les téléphones appairés.")) return;
    
    setIsRevoking(true);
    try {
      await api.post('/admin/revoke-mobile');
      setStatus({ type: 'success', msg: "Accès révoqué avec succès. La clé a été renouvelée." });
      setQrCode(null);
      setIsVisible(false);
    } catch (error) {
      setStatus({ type: 'error', msg: "Échec de la révocation." });
    } finally {
      setIsRevoking(false);
      setTimeout(() => setStatus(null), 5000);
    }
  };

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
      <div className="flex items-center gap-4 mb-6">
        <div className="w-12 h-12 rounded-2xl bg-indigo-500/10 flex items-center justify-center text-indigo-500">
          <Smartphone size={24} />
        </div>
        <div>
          <h2 className="text-xl font-bold text-slate-800 dark:text-white font-outfit">Compagnon Mobile</h2>
          <p className="text-sm text-slate-500">Gérez l'accès Zero-Knowledge de votre smartphone.</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* SECTION 1: QR CODE PAIRING */}
        <div className="bg-white dark:bg-slate-900/50 rounded-3xl border border-slate-200/60 dark:border-white/5 p-8 relative overflow-hidden">
          <div className="relative z-10">
            <h3 className="text-lg font-semibold mb-2 flex items-center gap-2">
              <Shield size={18} className="text-emerald-500" />
              Appairage Sécurisé
            </h3>
            <p className="text-sm text-slate-500 mb-6">
              Scannez ce code avec l'application mobile Digital Crown pour importer votre clé de déchiffrement locale.
            </p>

            <div className="relative w-64 mx-auto group">
              {/* QR Code avec masque de sécurité */}
              <div className={`w-full h-72 rounded-2xl border-2 border-dashed border-slate-200 dark:border-white/10 flex flex-col items-center justify-center overflow-hidden bg-slate-50 dark:bg-slate-800/30 transition-all duration-500 ${!isVisible ? 'p-0' : 'p-4'}`}>
                {qrCode ? (
                  <>
                    <img src={qrCode} alt="ZKA Key QR" className={`w-full h-44 object-contain transition-all duration-700 ${!isVisible ? 'blur-2xl opacity-0 scale-95' : 'blur-0 opacity-100 scale-100'}`} />
                    {tokenCode && (
                      <div className={`mt-3 font-black text-3xl tracking-[0.25em] text-indigo-600 transition-all duration-700 ${!isVisible ? 'blur-xl opacity-0' : 'blur-0 opacity-100'}`}>
                        {tokenCode}
                      </div>
                    )}
                  </>
                ) : (
                  <Smartphone size={48} className="text-slate-300 dark:text-slate-700" />
                )}

                {/* Overlay de masquage */}
                {!isVisible && (
                  <div className="absolute inset-0 backdrop-blur-md bg-white/40 dark:bg-slate-900/40 flex flex-col items-center justify-center p-6 text-center">
                    <button 
                      onClick={fetchQrCode}
                      className="w-14 h-14 rounded-full bg-white dark:bg-slate-800 shadow-xl flex items-center justify-center text-indigo-500 hover:scale-110 transition-transform active:scale-95"
                    >
                      <Eye size={24} />
                    </button>
                    <p className="mt-4 text-xs font-bold text-slate-600 dark:text-slate-300 uppercase tracking-widest">Révéler la clé</p>
                  </div>
                )}
              </div>

              {/* Countdown badge */}
              <AnimatePresence>
                {isVisible && (
                  <motion.div 
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: 10 }}
                    className="absolute -bottom-4 left-1/2 -translate-x-1/2 px-4 py-1.5 bg-indigo-500 text-white text-[10px] font-black rounded-full shadow-lg flex items-center gap-2"
                  >
                    <RefreshCw size={12} className="animate-spin" />
                    MASQUAGE DANS {countdown}S
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </div>
          
          {/* Background decoration */}
          <div className="absolute -top-10 -right-10 w-40 h-40 bg-indigo-500/5 rounded-full blur-3xl" />
        </div>

        {/* SECTION 2: DANGER ZONE / REVOCATION */}
        <div className="flex flex-col gap-6">
          <div className="bg-rose-500/5 dark:bg-rose-500/10 rounded-3xl border border-rose-500/20 p-8">
            <h3 className="text-lg font-semibold text-rose-600 dark:text-rose-400 mb-2 flex items-center gap-2">
              <AlertTriangle size={18} />
              Zone de Danger
            </h3>
            <p className="text-sm text-slate-600 dark:text-slate-400 mb-6">
              En cas de perte ou de vol de votre smartphone, révoquez immédiatement l'accès. Une nouvelle clé sera générée et l'ancien téléphone ne pourra plus lire vos données.
            </p>

            <button 
              onClick={handleRevoke}
              disabled={isRevoking}
              className="w-full py-4 bg-rose-500 hover:bg-rose-600 disabled:bg-slate-400 text-white rounded-2xl font-bold flex items-center justify-center gap-3 shadow-lg shadow-rose-500/20 transition-all active:scale-[0.98]"
            >
              {isRevoking ? (
                <RefreshCw size={20} className="animate-spin" />
              ) : (
                <>
                  <RefreshCw size={20} />
                  Révoquer tous les accès mobiles
                </>
              )}
            </button>
          </div>

          <AnimatePresence>
            {status && (
              <motion.div 
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}
                className={`p-6 rounded-2xl flex items-center gap-4 ${status.type === 'success' ? 'bg-emerald-500/10 border border-emerald-500/20 text-emerald-600' : 'bg-rose-500/10 border border-rose-500/20 text-rose-600'}`}
              >
                {status.type === 'success' ? <CheckCircle2 size={24} /> : <AlertTriangle size={24} />}
                <p className="text-sm font-medium">{status.msg}</p>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>

      <div className="bg-slate-50 dark:bg-white/5 rounded-2xl p-6 border border-slate-200/60 dark:border-white/5">
        <h4 className="text-sm font-bold text-slate-700 dark:text-slate-300 mb-2">Comprendre la Sécurité Zero-Knowledge</h4>
        <p className="text-xs text-slate-500 leading-relaxed">
          Digital Crown utilise un chiffrement AES-256 de bout en bout. Votre clé secrète est générée localement sur ce PC et transmise physiquement à votre téléphone via le QR code. 
          <strong> Aucun tiers, ni même les développeurs de l'application, ne peut accéder à vos données cliniques sur le cloud.</strong>
        </p>
      </div>
    </div>
  );
};
