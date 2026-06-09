import { Component } from 'react';
import type { ErrorInfo, ReactNode } from 'react';
import { AlertCircle, RefreshCcw } from 'lucide-react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false, error: null };

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    // Log structuré sans exposer de données sensibles
    console.error('[ErrorBoundary] Crash non géré:', error.message, info.componentStack?.slice(0, 200));
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) return this.props.fallback;
      return (
        <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4">
          <div className="max-w-md w-full bg-white rounded-[2rem] shadow-xl border border-slate-100 p-8 text-center space-y-6">
            <div className="w-20 h-20 bg-red-50 text-red-500 rounded-full flex items-center justify-center mx-auto shadow-inner relative">
               <div className="absolute inset-0 bg-red-500/20 blur-xl rounded-full" />
               <AlertCircle size={40} className="relative z-10" />
            </div>
            
            <div>
              <h1 className="text-2xl font-black text-slate-800 mb-2">Erreur Inattendue</h1>
              <p className="text-slate-500 font-medium text-sm">
                Une erreur s'est produite lors de l'affichage de cette page.
              </p>
            </div>

            {this.state.error && (
              <div className="bg-slate-50 p-4 rounded-xl text-left overflow-auto max-h-32 text-[10px] font-mono text-slate-600 border border-slate-200">
                {this.state.error.message}
              </div>
            )}

            <button
              onClick={() => window.location.href = '/'}
              className="w-full bg-slate-900 text-white py-4 rounded-2xl font-bold hover:bg-primary transition-all flex items-center justify-center gap-2 shadow-lg"
            >
              <RefreshCcw size={18} />
              Redémarrer l'application
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
