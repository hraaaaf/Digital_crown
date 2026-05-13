import React, { useState, useEffect } from 'react';
import { useNavigate, Link, useSearchParams } from 'react-router-dom';
import { authService } from '../services/auth';
import { Lock, Mail, User, AlertCircle, Loader2, ArrowRight } from 'lucide-react';
import { motion } from 'framer-motion';
import Logo from '../assets/logo.png';
import toast from 'react-hot-toast';

export const RegisterPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  // Capture des paramètres URL pour pré-remplir le formulaire
  useEffect(() => {
    const nameParam = searchParams.get('full_name');
    const emailParam = searchParams.get('email');
    if (nameParam) setFullName(nameParam);
    if (emailParam) setEmail(emailParam);
  }, [searchParams]);

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      await authService.register(email, password, fullName);
      toast.success('Compte créé avec succès ! Bienvenue.');
      navigate('/welcome');
    } catch (err: any) {
      setError(err.message || 'Une erreur est survenue lors de l\'inscription.');
      toast.error('Échec de l\'inscription');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#F8FAFC] flex items-center justify-center p-6 relative overflow-hidden">
      {/* Background Decor */}
      <div className="absolute top-[-5%] right-[-5%] w-[30%] h-[30%] bg-primary/5 rounded-full blur-3xl animate-pulse" />
      <div className="absolute bottom-[-5%] left-[-5%] w-[30%] h-[30%] bg-primary/10 rounded-full blur-3xl animate-pulse" />

      <motion.div 
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="w-full max-w-md"
      >
        <div className="bg-white/80 backdrop-blur-xl border border-white p-8 rounded-3xl shadow-2xl shadow-primary/10">
          <div className="flex flex-col items-center mb-8">
            <Link to="/login" className="mb-4">
              <img src={Logo} alt="Digital Crown" className="h-16 w-auto" />
            </Link>
            <h1 className="font-bold text-slate-900 text-lg uppercase tracking-wider">Rejoindre l'Elite</h1>
            <p className="text-slate-500 text-xs mt-1 text-center">
              Activez votre intelligence clinique augmentée en quelques secondes.
            </p>
          </div>

          <form onSubmit={handleRegister} className="space-y-5">
            <div>
              <label className="block text-sm font-bold text-slate-700 mb-1.5 ml-1">Nom Complet</label>
              <div className="relative">
                <User className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 w-5 h-5" />
                <input
                  type="text"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  className="w-full pl-12 pr-4 py-3 bg-slate-50/50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all font-medium text-slate-900"
                  placeholder="Dr. Jean Dupont"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-bold text-slate-700 mb-1.5 ml-1">Email Professionnel</label>
              <div className="relative">
                <Mail className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 w-5 h-5" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full pl-12 pr-4 py-3 bg-slate-50/50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all font-medium text-slate-900"
                  placeholder="votre@email.com"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-bold text-slate-700 mb-1.5 ml-1">Mot de passe</label>
              <div className="relative">
                <Lock className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 w-5 h-5" />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full pl-12 pr-4 py-3 bg-slate-50/50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all font-medium text-slate-900"
                  placeholder="8 caractères minimum"
                  minLength={8}
                  required
                />
              </div>
            </div>

            {error && (
              <motion.div 
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                className="flex items-center gap-3 p-3 bg-red-50 border border-red-100 text-red-600 rounded-xl text-xs font-medium"
              >
                <AlertCircle className="w-4 h-4 shrink-0" />
                <p>{error}</p>
              </motion.div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-primary hover:bg-primary/90 text-white font-bold py-4 rounded-xl shadow-lg shadow-primary/20 transition-all flex items-center justify-center gap-2 disabled:opacity-50 mt-4 group"
            >
              {loading ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <>
                  Créer mon compte
                  <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                </>
              )}
            </button>
          </form>

          <div className="mt-8 pt-6 border-t border-slate-100 flex flex-col items-center gap-4">
            <p className="text-sm text-slate-600">
              Déjà inscrit ?{' '}
              <Link to="/login" className="text-primary font-bold hover:underline">
                Se connecter
              </Link>
            </p>
            
            <p className="text-[10px] text-slate-400 text-center leading-relaxed">
              En vous inscrivant, vous acceptez nos Conditions d'Utilisation et notre Politique de Confidentialité. 
              <br />© 2026 SANINOVA - Digital Crown Elite
            </p>
          </div>
        </div>
      </motion.div>
    </div>
  );
};
