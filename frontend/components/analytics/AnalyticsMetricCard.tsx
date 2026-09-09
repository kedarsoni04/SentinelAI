'use client';

import { ArrowUpRight, ArrowDownRight, Minus } from 'lucide-react';
import { cn } from '@/lib/utils';

interface AnalyticsMetricCardProps {
  title: string;
  value: number | string;
  changePercentage?: number | null;
  changeLabel?: string;
  icon?: React.ComponentType<{ className?: string }>;
  accentColor?: 'blue' | 'red' | 'amber' | 'green' | 'purple';
  isLoading?: boolean;
}

export default function AnalyticsMetricCard({
  title,
  value,
  changePercentage,
  changeLabel = 'vs prior period',
  icon: Icon,
  accentColor = 'blue',
  isLoading = false,
}: AnalyticsMetricCardProps) {
  const accentClasses = {
    blue: 'border-l-[#3b7dd8] text-[#3b7dd8]',
    red: 'border-l-[#ef4444] text-[#ef4444]',
    amber: 'border-l-[#f59e0b] text-[#f59e0b]',
    green: 'border-l-[#22c55e] text-[#22c55e]',
    purple: 'border-l-[#8b5cf6] text-[#8b5cf6]',
  };

  const bgClasses = {
    blue: 'bg-[rgba(59,125,216,0.08)]',
    red: 'bg-[rgba(239,68,68,0.08)]',
    amber: 'bg-[rgba(245,158,11,0.08)]',
    green: 'bg-[rgba(34,197,94,0.08)]',
    purple: 'bg-[rgba(139,92,246,0.08)]',
  };

  return (
    <div
      className={cn(
        'p-5 bg-[#0d1117] border border-[#1e2736] rounded-xl border-l-4 transition-all duration-200 hover:border-[#2a374c]',
        accentClasses[accentColor]
      )}
    >
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold text-[#8b96a8] uppercase tracking-wider">
          {title}
        </span>
        {Icon && (
          <div className={cn('p-2 rounded-lg', bgClasses[accentColor])}>
            <Icon className="w-4 h-4" />
          </div>
        )}
      </div>

      <div className="mt-3">
        {isLoading ? (
          <div className="h-8 w-24 bg-[#1e2736] animate-pulse rounded my-1" />
        ) : (
          <div className="text-2xl font-bold text-[#e8edf5] tracking-tight">
            {typeof value === 'number' ? value.toLocaleString() : value}
          </div>
        )}
      </div>

      <div className="mt-2.5 flex items-center gap-1.5 text-xs">
        {changePercentage !== undefined && changePercentage !== null ? (
          <>
            <span
              className={cn(
                'inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded font-medium',
                changePercentage > 0
                  ? 'bg-red-500/10 text-red-400'
                  : changePercentage < 0
                  ? 'bg-green-500/10 text-green-400'
                  : 'bg-gray-500/10 text-gray-400'
              )}
            >
              {changePercentage > 0 ? (
                <ArrowUpRight className="w-3 h-3" />
              ) : changePercentage < 0 ? (
                <ArrowDownRight className="w-3 h-3" />
              ) : (
                <Minus className="w-3 h-3" />
              )}
              {Math.abs(changePercentage)}%
            </span>
            <span className="text-[#627084]">{changeLabel}</span>
          </>
        ) : (
          <span className="text-[#627084]">Baseline comparison baseline</span>
        )}
      </div>
    </div>
  );
}
