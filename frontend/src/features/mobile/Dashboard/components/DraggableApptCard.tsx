import { useDraggable } from '@dnd-kit/core';
import { GripVertical } from 'lucide-react';
import { ApptCard } from './ApptCard';
import type { Appointment, ApptStatus } from '../types';

export function DraggableApptCard({
  apt,
  onStatusChange,
  openApptWhatsApp,
  handleDeleteAppt,
  handleOpenSignature
}: {
  apt: Appointment;
  onStatusChange: (id: number, status: ApptStatus) => void;
  openApptWhatsApp: (apt: Appointment) => void;
  handleDeleteAppt: (id: number) => void;
  handleOpenSignature: (id: number, name: string) => void;
}) {
  const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({
    id: `appt-${apt.id}`,
    data: { apt }
  });

  const style = transform ? {
    transform: `translate3d(${transform.x}px, ${transform.y}px, 0)`,
    zIndex: isDragging ? 50 : 1,
    opacity: isDragging ? 0.8 : 1,
  } : undefined;

  return (
    <div ref={setNodeRef} style={style} className="relative group flex gap-2 items-stretch">
      <div 
        {...attributes} 
        {...listeners} 
        className="w-10 bg-glass-bg border border-glass-border rounded-[24px] flex items-center justify-center text-text-muted hover:text-primary hover:bg-primary/5 transition-colors touch-none cursor-grab active:cursor-grabbing shadow-elite shrink-0"
      >
        <GripVertical size={16} />
      </div>
      <div className="flex-1 min-w-0">
        <ApptCard
          apt={apt}
          onStatusChange={onStatusChange}
          onWhatsApp={openApptWhatsApp}
          onDelete={handleDeleteAppt}
          onSign={handleOpenSignature}
        />
      </div>
    </div>
  );
}
