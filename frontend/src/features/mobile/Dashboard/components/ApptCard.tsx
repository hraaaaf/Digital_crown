import { useState } from 'react';
import { Phone, MessageSquare, ChevronRight, Stethoscope, Trash2, FileText } from 'lucide-react';
import { cn } from '../../../../utils/cn';
import { STATUS_META } from '../types';
import type { Appointment, ApptStatus } from '../types';

export function ApptCard({
  apt, onStatusChange, onWhatsApp, onDelete, onSign
}: {
  apt: Appointment;
  onStatusChange: (id: number, status: ApptStatus) => void;
  onWhatsApp: (apt: Appointment) => void;
  onDelete?: (id: number) => void;
  onSign?: (patientId: number, patientName: string) => void;
}) {
  const meta = STATUS_META[apt.status as ApptStatus] ?? STATUS_META.PLANIFIE;
  const [expanded, setExpanded] = useState(false);

  const nextStatuses: ApptStatus[] = apt.status === 'PLANIFIE'
    ? ['EN_COURS', 'ANNULE']
    : apt.status === 'EN_COURS'
    ? ['TERMINE', 'ANNULE']
    : [];

  return (
    <div className="bg-glass-bg border border-glass-border backdrop-blur-md rounded-[24px] overflow-hidden shadow-elite transition-all duration-300">
      <button
        className="w-full flex items-center gap-4 p-5 text-left hover:bg-primary/[0.02] transition-colors"
        onClick={() => setExpanded(e => !e)}
      >
        <div className="w-14 h-14 bg-primary/5 border border-primary/10 rounded-[16px] flex flex-col items-center justify-center shrink-0">
          <Stethoscope size={12} className="text-primary mb-0.5" />
          <span className="text-[11px] font-black text-primary leading-none">{apt.time}</span>
        </div>

        <div className="flex-1 min-w-0">
          <p className="font-black text-text-main font-outfit truncate leading-tight">{apt.patient_name}</p>
          <p className="text-[10px] text-text-muted font-bold mt-0.5 uppercase tracking-wider truncate">
            {apt.motif} · {apt.duration_minutes}min
          </p>
        </div>

        <div className="flex flex-col items-end gap-2 shrink-0">
          <span className={cn(
            'flex items-center gap-1 px-2 py-1 rounded-lg border text-[9px] font-black uppercase tracking-widest',
            meta.className
          )}>
            {meta.icon} {meta.label}
          </span>
          <ChevronRight size={14} className={cn('text-text-muted transition-transform', expanded ? 'rotate-90' : '')} />
        </div>
      </button>

      {expanded && (
        <div className="px-5 pb-5 space-y-3 border-t border-border-main pt-4">
          {nextStatuses.length > 0 && (
            <div className="flex gap-2">
              {nextStatuses.map(s => {
                const sm = STATUS_META[s];
                return (
                  <button
                    key={s}
                    onClick={() => onStatusChange(apt.id, s)}
                    className={cn(
                      'flex-1 flex items-center justify-center gap-1.5 py-2.5 rounded-[16px] border text-[10px] font-black uppercase tracking-widest transition-all active:scale-95',
                      sm.className
                    )}
                  >
                    {sm.icon} {sm.label}
                  </button>
                );
              })}
              {onDelete && (
                <button
                  onClick={() => onDelete(apt.id)}
                  className="flex-1 flex items-center justify-center gap-1.5 py-2.5 rounded-[16px] border text-[10px] font-black uppercase tracking-widest transition-all active:scale-95 bg-rose-500/10 text-rose-500 border-rose-500/20"
                >
                  <Trash2 size={12} /> Supprimer
                </button>
              )}
            </div>
          )}

          <div className="flex flex-col gap-2">
            {apt.phone && (
              <div className="flex gap-2">
                <a
                  href={`tel:${apt.phone}`}
                  className="flex-1 flex items-center justify-center gap-1.5 py-2.5 bg-emerald-500/10 border border-emerald-500/20 text-emerald-600 rounded-[16px] text-[10px] font-black uppercase tracking-widest"
                >
                  <Phone size={12} /> Appeler
                </a>
                <button
                  onClick={() => onWhatsApp(apt)}
                  className="flex-1 flex items-center justify-center gap-1.5 py-2.5 bg-primary/5 border border-primary/10 text-primary rounded-[16px] text-[10px] font-black uppercase tracking-widest"
                >
                  <MessageSquare size={12} /> WhatsApp
                </button>
              </div>
            )}

            {apt.patient_id && onSign && (
              <button
                onClick={() => onSign(apt.patient_id!, apt.patient_name)}
                className="w-full min-h-12 flex items-center justify-center gap-1.5 bg-indigo-500/10 border border-indigo-500/20 text-indigo-600 rounded-[16px] text-[10px] font-black uppercase tracking-widest transition-all active:scale-95"
              >
                <FileText size={12} /> Signature au Fauteuil
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
