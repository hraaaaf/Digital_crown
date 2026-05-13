import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { authService } from '../services/auth';
import { Mail, AlertCircle, Loader2, ArrowLeft, CheckCircle2 } from 'lucide-react';
import { motion } from 'framer-motion';
import Logo from '../assets/logo.png';
import toast from 'react-hot-toast';

export const ForgotPasswordPage: React.FC = () => {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      await authService.resetPassword(email);
      setSuccess(true);
      toast.success('Lien de réinitialisation envoyé !');
    } catch (err: any) {
      setError(err.message || 'Une erreur est survenue.');
      toast.error('Échec de l\'envoi');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#F8FAFC] flex items-center justify-center p-6 relative overflow-hidden">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,rgba(var(--primary-rgb),0.05),transparent_70%)]" />

      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-md relative z-10"
      >
        <div className="bg-white/80 backdrop-blur-2xl border border-white p-10 rounded-[2.5rem] shadow-2xl shadow-primary/5">
          <div className="flex flex-col items-center mb-10 text-center">
            <Link to="/login" className="mb-6 hover:scale-105 transition-transform">
              <img src={Logo} alt="Digital Crown" className="h-20 w-auto" />
            </Link>
            <h1 className="font-bold text-slate-900 text-2xl tracking-tight">Récupération d'accès</h1>
            <p className="text-slate-500 text-sm mt-3 px-4 leading-relaxed">
              Entrez votre adresse email professionnelle pour recevoir un lien sécurisé de réinitialisation.
            </p>
          </div>

          {!success ? (
            <form onSubmit={handleSubmit} className="space-y-6">
              <div>
                <label className="block text-xs font-bold text-slate-400 uppercase tracking-widest mb-2 ml-1">Email</label>
                <div className="relative">
                  <Mail className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-300 w-5 h-5" />
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full pl-12 pr-4 py-4 bg-slate-50/30 border border-slate-100 rounded-2xl focus:ring-4 focus:ring-primary/10 focus:border-primary outline-none transition-all font-semibold text-slate-900 placeholder:text-slate-300"
                    placeholder="nom@cabinet.com"
                    required
                  />
                </div>
              </div>

              {error && (
                <div className="flex items-center gap-3 p-4 bg-red-50 text-red-600 rounded-2xl text-xs font-bold border border-red-100">
                  <AlertCircle className="w-5 h-5 shrink-0" />
                  <p>{error}</p>
                </div>
              )}

              <button
                type="submit"
                disabled={loading}
                className="w-full bg-primary hover:bg-primary/90 text-white font-bold py-5 rounded-2xl shadow-xl shadow-primary/30 transition-all flex items-center justify-center gap-3 disabled:opacity-50"
              >
                {loading ? (
                  <Loader2 className="w-6 h-6 animate-spin" />
                ) : (
                  'Envoyer les instructions'
                )}
              </button>

              <Link 
                to="/login" 
                className="flex items-center justify-center gap-2 text-sm text-slate-400 hover:text-primary font-bold transition-colors mt-6"
              >
                <ArrowLeft className="w-4 h-4" />
                Retour à la connexion
              </Link>
            </form>
          ) : (
            <motion.div 
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              className="text-center py-6"
            >
              <div className="w-20 h-20 bg-green-50 rounded-full flex items-center justify-center mx-auto mb-6">
                <CheckCircle2 className="w-10 h-10 text-green-500" />
              </div>
              <h2 className="text-xl font-bold text-slate-900 mb-3">Email envoyé !</h2>
              <p className="text-slate-500 text-sm mb-10 leading-relaxed px-2">
                Si un compte existe pour <strong>{email}</strong>, vous recevrez un lien dans quelques instants. Pensez à vérifier vos spams.
              </p>
              <Link 
                to="/login" 
                className="inline-flex items-center justify-center gap-2 bg-slate-900 text-white font-bold px-8 py-4 rounded-2xl hover:bg-slate-800 transition-all"
              >
                <ArrowLeft className="w-4 h-4" />
                Retour au login
              </Link>
            </motion.div>
          )}
        </div>
      </motion.div>
    </div>
  );
};
