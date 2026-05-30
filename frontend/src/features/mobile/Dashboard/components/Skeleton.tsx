import { cn } from '../../../../utils/cn';

export function Skeleton({ className = '' }: { className?: string }) {
  return <div className={cn('bg-border-main/40 rounded-[16px] animate-pulse', className)} />;
}
