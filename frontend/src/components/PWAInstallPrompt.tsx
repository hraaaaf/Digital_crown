import React, { useState } from 'react';
import { usePWAInstall } from '../hooks/usePWAInstall';
import { Download, Share, X } from 'lucide-react';
import { cn } from '../utils/cn';

export function PWAInstallPrompt() {
  const { isInstallable, isInstalled, isIOS, install } = usePWAInstall();
  const [showIOSHint, setShowIOSHint] = useState(false);

  // Si l'application est déjà installée, on ne montre rien
  if (isInstalled) return null;

  // Si on n'est ni sur iOS ni sur un device qui peut installer l'app, on ne montre rien (par précaution)
  // Bien qu'il soit préférable de toujours montrer l'option sur iOS car isInstallable est false sur iOS
  if (!isInstallable && !isIOS) return null;

  return (
    <div className="bg-card text-text-main p-4 rounded-xl shadow-lg border border-border-main mx-4 mb-4">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <h3 className="font-semibold text-lg flex items-center gap-2">
            <Download size={20} className="text-warning" />
            Installer Pocket
          </h3>
          <p className="text-text-muted text-sm mt-1">
            Installez Digital Crown Pocket sur votre écran d'accueil pour un accès rapide et hors-ligne.
          </p>
        </div>
      </div>

      <div className="mt-4">
        {isIOS ? (
          <div>
            <button 
              onClick={() => setShowIOSHint(!showIOSHint)}
              className="w-full bg-input-field hover:bg-background text-text-main focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary font-medium py-2 px-4 rounded-lg transition-colors flex items-center justify-center gap-2"
            >
              Comment installer sur iPhone ?
            </button>
            
            {showIOSHint && (
              <div className="mt-3 bg-background p-3 rounded-lg text-sm text-text-muted border border-border-main relative overflow-hidden">
                <div className="absolute top-0 left-0 w-1 h-full bg-info"></div>
                <p className="flex items-center gap-2 mb-2">
                  <span className="bg-card w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold text-text-main border border-border-main">1</span>
                  Appuyez sur <Share size={16} className="text-info mx-1" /> dans la barre Safari
                </p>
                <p className="flex items-center gap-2">
                  <span className="bg-card w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold text-text-main border border-border-main">2</span>
                  Choisissez <strong>Sur l'écran d'accueil</strong> <PlusIcon />
                </p>
              </div>
            )}
          </div>
        ) : (
          <button 
            onClick={install}
            className="w-full bg-primary hover:bg-secondary text-on-primary font-medium py-2 px-4 rounded-lg transition-colors shadow-sm"
          >
            Installer maintenant
          </button>
        )}
      </div>
    </div>
  );
}

function PlusIcon() {
  return (
    <div className="border border-border-main rounded flex items-center justify-center p-0.5 ml-1">
      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <line x1="12" y1="5" x2="12" y2="19"></line>
        <line x1="5" y1="12" x2="19" y2="12"></line>
      </svg>
    </div>
  );
}
