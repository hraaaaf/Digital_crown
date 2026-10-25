import React from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';
import { cn } from '../../../../utils/cn';

export const inputClass = "w-full px-5 py-4 bg-input-field text-text-main border border-border-main rounded-xl text-sm focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary transition-all duration-300 font-bold text-text-main";
export const labelClass = "text-[10px] font-black text-text-muted uppercase tracking-widest block mb-2 ml-1";

interface SettingsSectionProps {
  title: string;
  subtitle?: string;
  icon?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
}

export const SettingsSection: React.FC<SettingsSectionProps> = ({ title, subtitle, icon, children, className }) => (
  <div className={cn("space-y-6 animate-in slide-in-from-right-4 duration-500", className)}>
    <div className="flex min-w-0 flex-col items-start gap-3 mb-8 pb-6 border-b border-border-main sm:flex-row sm:items-center sm:gap-4">
      {icon && (
        <div className="w-16 h-16 shrink-0 bg-primary/5 text-primary rounded-2xl flex items-center justify-center shadow-inner border border-primary/10">
          {icon}
        </div>
      )}
      <div className="min-w-0 max-w-full">
        <h3 className="break-words [overflow-wrap:anywhere] text-2xl font-black" style={{ color: 'var(--primary)' }}>{title}</h3>
        {subtitle && <p className="break-words [overflow-wrap:anywhere] text-text-muted text-sm font-medium mt-1">{subtitle}</p>}
      </div>
    </div>
    {children}
  </div>
);

interface SettingsReadErrorProps {
  title?: string;
  message: string;
  onRetry: () => void | Promise<void>;
}

export const SettingsReadError: React.FC<SettingsReadErrorProps> = ({ title = 'Configuration indisponible', message, onRetry }) => (
  <div className="bg-danger-surface border border-danger-border rounded-2xl p-5 sm:p-6 flex flex-col sm:flex-row sm:items-center gap-4 text-danger">
    <AlertTriangle size={22} className="shrink-0" />
    <div className="min-w-0 flex-1">
      <p className="font-black text-sm">{title}</p>
      <p className="text-sm font-medium mt-1">{message}</p>
    </div>
    <button type="button" onClick={() => void onRetry()} className="w-full sm:w-auto px-4 py-2.5 bg-card text-danger border border-danger-border focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary rounded-xl font-black text-sm flex items-center justify-center gap-2 hover:bg-danger-surface transition-colors">
      <RefreshCw size={16} /> Réessayer
    </button>
  </div>
);

interface TabButtonProps {
  active: boolean;
  onClick: () => void;
  icon: React.ReactNode;
  label: string;
}

export const TabButton: React.FC<TabButtonProps> = ({ active, onClick, icon, label }) => (
  <button 
    onClick={onClick} 
    className={cn(
      "flex shrink-0 items-center gap-2 whitespace-nowrap px-4 py-3 rounded-xl text-sm font-bold transition-all duration-300 w-auto text-left 2xl:w-full 2xl:gap-4 2xl:px-6 2xl:py-4 2xl:rounded-2xl 2xl:text-base focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary",
      active ? "bg-primary text-on-primary shadow-lg 2xl:scale-[1.02]" : "text-text-muted hover:bg-input-field hover:text-primary"
    )}
  >
    {icon} <span>{label}</span>
  </button>
);
