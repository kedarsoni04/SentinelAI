import { cn } from '@/lib/utils';
import type { IncidentRiskLevel } from '@/types';

interface IncidentRiskBadgeProps {
  level: IncidentRiskLevel | null | undefined;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

const config: Record<string, { label: string; classes: string; dot: string }> = {
  CRITICAL: {
    label: 'CRITICAL',
    classes: 'bg-red-500/15 text-red-400 border border-red-500/30',
    dot: 'bg-red-400',
  },
  HIGH: {
    label: 'HIGH',
    classes: 'bg-orange-500/15 text-orange-400 border border-orange-500/30',
    dot: 'bg-orange-400',
  },
  MEDIUM: {
    label: 'MEDIUM',
    classes: 'bg-yellow-500/15 text-yellow-400 border border-yellow-500/30',
    dot: 'bg-yellow-400',
  },
  LOW: {
    label: 'LOW',
    classes: 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30',
    dot: 'bg-emerald-400',
  },
  UNKNOWN: {
    label: 'UNKNOWN',
    classes: 'bg-[#1e2736] text-[#8b96a8] border border-[#2a3548]',
    dot: 'bg-[#4e5a6b]',
  },
};

const sizeClasses = {
  sm: 'text-[9px] px-2 py-0.5 gap-1',
  md: 'text-[10px] px-2.5 py-1 gap-1.5',
  lg: 'text-xs px-3 py-1.5 gap-2',
};

const dotSizeClasses = {
  sm: 'w-1.5 h-1.5',
  md: 'w-2 h-2',
  lg: 'w-2.5 h-2.5',
};

export default function IncidentRiskBadge({
  level,
  size = 'md',
  className,
}: IncidentRiskBadgeProps) {
  const key = level ?? 'UNKNOWN';
  const { label, classes, dot } = config[key] ?? config.UNKNOWN;

  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full font-semibold tracking-wider uppercase',
        sizeClasses[size],
        classes,
        className
      )}
    >
      <span className={cn('rounded-full shrink-0', dotSizeClasses[size], dot)} />
      {label}
    </span>
  );
}
