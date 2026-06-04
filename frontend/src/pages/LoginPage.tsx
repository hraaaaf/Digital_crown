import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { authService } from '../services/auth';
import { Lock, Mail, AlertCircle, Loader2, User, RefreshCw, LogOut } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import Logo from '../assets/logo.png';
import { api, resetAuthState } from '../services/api';

export const LoginPage: React.FC = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [rememberMe, setRememberMe] = useState(true);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  const isLocked = new URLSearchParams(location.search).get('locked') === 'true';
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    authService.isAuthenticated().then((isAuth) => {
      if (isAuth && !isLocked) {
        navigate('/dashboard');
      } else {
        setIsAuthenticated(isAuth);
      }
    });
  }, [location.search]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      resetAuthState(); // Réarme le coupe-circuit auth avant chaque tentative de login
      if (isLogin) {
        await authService.login(email, password);
        if (isLocked) {
          // Si on était verrouillé, on tente de revérifier la licence
          await api.post('/clinics/recheck-license');
        }
        navigate('/dashboard');
      } else {
        await authService.register(email, password, fullName);
        navigate('/setup');
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Une erreur est survenue.');
    } finally {
      setLoading(false);
    }
  };

  const handleRecheckLicense = async () => {
    setLoading(true);
    setError('');
    try {
      await api.post('/clinics/recheck-license');
      navigate('/dashboard');
    } catch (err: any) {
      if (err.response?.status === 402) {
        setError("La licence est toujours invalide. Veuillez contacter le support ou mettre à jour votre abonnement.");
      } else {
        setError(err.response?.data?.detail || "Une erreur inattendue s'est produite.");
      }
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = async () => {
    await authService.logout();
    setIsAuthenticated(false);
  };

  return (
    <div className="min-h-screen bg-[#F8FAFC] flex items-center justify-center p-6 relative overflow-hidden">
      {/* Background Shapes */}
      <div className={`absolute top-[-10%] left-[-10%] w-[40%] h-[40%] rounded-full blur-3xl animate-pulse ${isLocked ? 'bg-red-500/10' : 'bg-primary/5'}`} />
      <div className={`absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] rounded-full blur-3xl animate-pulse ${isLocked ? 'bg-red-500/10' : 'bg-primary/10'}`} />

      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-md relative z-10"
      >
        <div className={`bg-white/80 backdrop-blur-xl border border-white p-8 rounded-3xl shadow-2xl ${isLocked ? 'shadow-red-500/10' : 'shadow-primary/10'}`}>
          <div className="flex flex-col items-center mb-8">
            <div className="mb-4">
              <img src={Logo} alt="Digital Crown" className="h-16 w-auto" />
            </div>
            {isLocked ? (
              <>
                <h1 className="font-bold text-red-600 text-xl text-center flex items-center gap-2">
                  <Lock className="w-5 h-5" /> Accès Verrouillé
                </h1>
                <p className="text-slate-500 text-sm mt-2 text-center">
                  Votre licence d'utilisation a expiré ou est invalide.
                </p>
              </>
            ) : (
              <>
                <h1 className="font-bold text-slate-900 text-xl text-center">
                  {isLogin ? 'Digital Crown AI' : 'Créer votre Cabinet'}
                </h1>
                <p className="text-slate-500 text-sm mt-1 text-center">
                  {isLogin ? 'Connectez-vous à votre espace' : 'Inscrivez-vous pour commencer'}
                </p>
              </>
            )}
          </div>

          {/* SI VERROUILLE ET DEJA CONNECTE -> On affiche juste le bouton pour revérifier */}
          {isLocked && isAuthenticated ? (
            <div className="space-y-5">
              <div className="p-4 bg-orange-50 border border-orange-100 rounded-xl text-sm text-orange-800 text-center">
                Vous êtes connecté en tant qu'Administrateur. Vous pouvez forcer la revérification de la licence si vous venez de la renouveler.
              </div>

              {error && (
                <motion.div 
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  className="flex items-center gap-3 p-4 bg-red-50 border border-red-100 text-red-600 rounded-xl text-sm"
                >
                  <AlertCircle className="w-5 h-5 shrink-0" />
                  <p>{error}</p>
                </motion.div>
              )}

              <button
                onClick={handleRecheckLicense}
                disabled={loading}
                className="w-full bg-red-600 hover:bg-red-700 text-white font-bold py-4 rounded-xl shadow-lg shadow-red-600/20 transition-all flex items-center justify-center gap-2 disabled:opacity-50"
              >
                {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <RefreshCw className="w-5 h-5" />}
                Revérifier la licence
              </button>
              
              <button
                onClick={handleLogout}
                disabled={loading}
                className="w-full flex items-center justify-center gap-2 py-3 text-slate-500 hover:text-slate-700 hover:bg-slate-50 rounded-xl transition-colors font-medium text-sm mt-2"
              >
                <LogOut className="w-4 h-4" /> Se déconnecter
              </button>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-5">
              <AnimatePresence mode="popLayout">
                {!isLogin && !isLocked && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                    className="overflow-hidden"
                  >
                    <label className="block text-sm font-medium text-slate-700 mb-2">Nom Complet</label>
                    <div className="relative">
                      <User className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 w-5 h-5" />
                      <input
                        type="text"
                        value={fullName}
                        onChange={(e) => setFullName(e.target.value)}
                        className="w-full pl-12 pr-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all"
                        placeholder="Dr. Ahmed Benmoussa"
                        required={!isLogin}
                      />
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">Email Professionnel</label>
                <div className="relative">
                  <Mail className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 w-5 h-5" />
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full pl-12 pr-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all"
                    placeholder="nom@cabinet.com"
                    required
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">Mot de passe</label>
                <div className="relative">
                  <Lock className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 w-5 h-5" />
                  <input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full pl-12 pr-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all"
                    placeholder="••••••••"
                    required
                    minLength={6}
                  />
                </div>
              </div>

              {isLogin && !isLocked && (
                <div className="flex items-center">
                  <label className="flex items-center gap-2 cursor-pointer group">
                    <input 
                      type="checkbox" 
                      checked={rememberMe}
                      onChange={(e) => setRememberMe(e.target.checked)}
                      className="w-4 h-4 rounded border-slate-300 text-primary focus:ring-primary/20 transition-all" 
                    />
                    <span className="text-sm text-slate-600 group-hover:text-slate-900 transition-colors">Rester connecté</span>
                  </label>
                </div>
              )}

              {error && (
                <motion.div 
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  className="flex items-center gap-3 p-4 bg-red-50 border border-red-100 text-red-600 rounded-xl text-sm"
                >
                  <AlertCircle className="w-5 h-5 shrink-0" />
                  <p>{error}</p>
                </motion.div>
              )}

              <button
                type="submit"
                disabled={loading}
                className={`w-full text-white font-bold py-4 rounded-xl shadow-lg transition-all flex items-center justify-center gap-2 disabled:opacity-50 ${isLocked ? 'bg-red-600 hover:bg-red-700 shadow-red-600/20' : 'bg-primary hover:bg-primary/90 shadow-primary/20'}`}
              >
                {loading ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  isLocked ? 'S\'authentifier en tant qu\'Admin' : (isLogin ? 'Se connecter' : 'Créer mon compte')
                )}
              </button>
            </form>
          )}

          {!isLocked && !isAuthenticated && (
            <div className="mt-6 text-center">
              <p className="text-sm text-slate-600">
                {isLogin ? "Nouveau sur Digital Crown ?" : "Vous avez déjà un compte ?"}
                <button 
                  type="button" 
                  onClick={() => {
                    setIsLogin(!isLogin);
                    setError('');
                  }} 
                  className="ml-2 font-bold text-primary hover:underline"
                >
                  {isLogin ? "Créer un compte" : "Se connecter"}
                </button>
              </p>
            </div>
          )}

          {(!isAuthenticated || !isLocked) && (
            <div className="mt-6">
            </div>
          )}

          <div className="mt-8 pt-6 border-t border-slate-100 text-center">
            <p className="text-xs text-slate-400">
              © 2026 SANINOVA - Digital Crown Elite Edition v4.0
            </p>
          </div>
        </div>
      </motion.div>
    </div>
  );
};
