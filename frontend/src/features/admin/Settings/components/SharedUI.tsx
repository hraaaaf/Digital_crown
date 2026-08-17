import React from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';
import { cn } from '../../../../utils/cn';

export const inputClass = "w-full px-5 py-4 bg-slate-50 border border-slate-200 rounded-xl text-sm outline-none focus:ring-4 transition-all duration-300 font-bold text-slate-800";
export const labelClass = "text-[10px] font-black text-slate-400 uppercase tracking-widest block mb-2 ml-1";

interface SettingsSectionProps {
  title: string;
  subtitle?: string;
  icon?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
}

export const SettingsSection: React.FC<SettingsSectionProps> = ({ title, subtitle, icon, children, className }) => (
  <div className={cn("space-y-6 animate-in slide-in-from-right-4 duration-500", className)}>
    <div className="flex items-center gap-4 mb-8 pb-6 border-b border-slate-100">
      {icon && (
        <div className="w-16 h-16 bg-primary/5 rounded-2xl flex items-center justify-center shadow-inner border border-primary/10" style={{ color: 'var(--primary)' }}>
          {icon}
        </div>
      )}
      <div>
        <h3 className="text-2xl font-black" style={{ color: 'var(--primary)' }}>{title}</h3>
        {subtitle && <p className="text-slate-500 text-sm font-medium mt-1">{subtitle}</p>}
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
  <div className="bg-rose-50 border border-rose-200 rounded-2xl p-5 sm:p-6 flex flex-col sm:flex-row sm:items-center gap-4 text-rose-700">
    <AlertTriangle size={22} className="shrink-0" />
    <div className="min-w-0 flex-1">
      <p className="font-black text-sm">{title}</p>
      <p className="text-sm font-medium mt-1">{message}</p>
    </div>
    <button type="button" onClick={() => void onRetry()} className="w-full sm:w-auto px-4 py-2.5 bg-white border border-rose-200 rounded-xl font-black text-sm flex items-center justify-center gap-2 hover:bg-rose-100 transition-colors">
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
      "flex items-center gap-4 px-6 py-4 rounded-2xl font-bold transition-all duration-300 w-full text-left",
      active ? "text-white shadow-lg scale-[1.02]" : "text-slate-500 hover:bg-slate-50 hover:text-primary"
    )}
    style={{ backgroundColor: active ? 'var(--primary)' : 'transparent', boxShadow: active ? '0 10px 30px -10px var(--primary)' : 'none', color: active ? 'white' : undefined }}
  >
    {icon} <span>{label}</span>
  </button>
);
