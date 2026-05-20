import { Component, ErrorInfo, ReactNode } from 'react';

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
        <div className="flex flex-col items-center justify-center h-screen gap-4 bg-slate-50">
          <div className="text-red-400 text-5xl">⚠</div>
          <h2 className="text-xl font-bold text-slate-700">Une erreur inattendue s'est produite</h2>
          <p className="text-slate-500 text-sm max-w-sm text-center">{this.state.error?.message}</p>
          <button
            className="px-5 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-sm font-medium transition-colors"
            onClick={() => window.location.reload()}
          >
            Recharger l'application
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
