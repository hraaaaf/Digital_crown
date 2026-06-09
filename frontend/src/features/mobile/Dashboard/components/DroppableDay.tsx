import { useDroppable } from '@dnd-kit/core';
import { cn } from '../../../../utils/cn';

export function DroppableDay({
  date,
  label,
  sublabel,
  isSelected,
  onClick,
  isMonthView = false,
  hasAppointments = false,
}: {
  date: string;
  label: string;
  sublabel?: string;
  isSelected: boolean;
  onClick: () => void;
  isMonthView?: boolean;
  hasAppointments?: boolean;
}) {
  const { isOver, setNodeRef } = useDroppable({
    id: `day-${date}`,
    data: { date }
  });

  if (isMonthView) {
    return (
      <button
        ref={setNodeRef}
        onClick={onClick}
        className={cn(
          "h-12 w-full rounded-xl flex flex-col items-center justify-center transition-all border",
          isSelected 
            ? "bg-primary text-white border-primary shadow-md" 
            : "bg-white text-slate-700 border-slate-100 hover:border-primary/30",
          isOver && "ring-2 ring-primary bg-primary/10 scale-105 z-10"
        )}
      >
        <span className="text-sm font-black font-outfit">{label}</span>
        {hasAppointments && !isSelected && (
          <span className="w-1.5 h-1.5 rounded-full bg-primary mt-0.5" />
        )}
      </button>
    );
  }

  return (
    <button
      ref={setNodeRef}
      onClick={onClick}
      className={cn(
        "flex-1 py-3 flex flex-col items-center justify-center rounded-[20px] transition-all border",
        isSelected 
          ? "bg-primary text-white border-primary shadow-[0_4px_20px_rgba(var(--primary-rgb),0.3)] scale-105" 
          : "bg-glass-bg text-text-muted border-glass-border hover:bg-white/60",
        isOver && "ring-2 ring-primary bg-primary/10 scale-110 z-10"
      )}
    >
      <span className={cn("text-[10px] font-black uppercase tracking-widest mb-1", isSelected ? "text-white/80" : "text-text-muted")}>
        {sublabel}
      </span>
      <span className={cn("text-xl font-black font-outfit", isSelected ? "text-white" : "text-text-main")}>
        {label}
      </span>
      {hasAppointments && !isSelected && (
        <span className="w-1.5 h-1.5 rounded-full bg-primary mt-1" />
      )}
    </button>
  );
}
