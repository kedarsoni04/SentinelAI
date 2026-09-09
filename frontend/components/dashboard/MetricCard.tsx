import { cn } from '@/lib/utils';
import type { LucideIcon } from 'lucide-react';

interface MetricCardProps {
  label: string;
  value: string | number;
  subtext?: string;
  icon: LucideIcon;
  iconColor?: string;
  iconBg?: string;
  trend?: 'up' | 'down' | 'neutral';
  className?: string;
}

/**
 * Reusable metric card for the SentinelAI dashboard.
 * Displays a key metric with an icon, value, and optional subtext.
 */
export default function MetricCard({
  label,
  value,
  subtext,
  icon: Icon,
  iconColor = '#3b7dd8',
  iconBg = 'rgba(59,125,216,0.1)',
  className,
}: MetricCardProps) {
  return (
    <div
      className={cn(
        'bg-[#111620] border border-[#1e2736] rounded-xl p-5',
        'hover:border-[#2a3748] transition-colors duration-200',
        className
      )}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="text-xs font-medium text-[#8b96a8] uppercase tracking-widest mb-3">
            {label}
          </p>
          <p className="text-3xl font-semibold text-[#e8edf5] tabular-nums leading-none">
            {value}
          </p>
          {subtext && (
            <p className="text-xs text-[#4e5a6b] mt-2 leading-relaxed">{subtext}</p>
          )}
        </div>

        {/* Icon */}
        <div
          className="w-10 h-10 rounded-lg flex items-center justify-center shrink-0 ml-4"
          style={{ backgroundColor: iconBg }}
        >
          <Icon className="w-5 h-5" style={{ color: iconColor }} />
        </div>
      </div>
    </div>
  );
}
