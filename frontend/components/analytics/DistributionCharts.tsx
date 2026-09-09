'use client';

import type { DistributionItem, SeverityDistributionItem } from '@/types';
import { cn } from '@/lib/utils';
import { PieChart, ShieldAlert } from 'lucide-react';

interface DistributionChartsProps {
  eventTypes: DistributionItem[];
  severities: SeverityDistributionItem[];
  totalEvents: number;
  isLoading?: boolean;
}

const SEVERITY_CONFIG: Record<
  string,
  { label: string; color: string; bg: string; border: string; bar: string }
> = {
  CRITICAL: {
    label: 'Critical',
    color: 'text-red-400',
    bg: 'bg-red-500/10',
    border: 'border-red-500/30',
    bar: 'bg-red-500',
  },
  HIGH: {
    label: 'High',
    color: 'text-orange-400',
    bg: 'bg-orange-500/10',
    border: 'border-orange-500/30',
    bar: 'bg-orange-500',
  },
  MEDIUM: {
    label: 'Medium',
    color: 'text-amber-400',
    bg: 'bg-amber-500/10',
    border: 'border-amber-500/30',
    bar: 'bg-amber-500',
  },
  LOW: {
    label: 'Low',
    color: 'text-blue-400',
    bg: 'bg-blue-500/10',
    border: 'border-blue-500/30',
    bar: 'bg-blue-500',
  },
};

export default function DistributionCharts({
  eventTypes,
  severities,
  totalEvents,
  isLoading = false,
}: DistributionChartsProps) {
  if (isLoading) {
    return (
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <div className="h-[280px] bg-[#0d1117] border border-[#1e2736] rounded-xl p-5 animate-pulse" />
        <div className="h-[280px] bg-[#0d1117] border border-[#1e2736] rounded-xl p-5 animate-pulse" />
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
      {/* Severity Breakdown Card */}
      <div className="bg-[#0d1117] border border-[#1e2736] rounded-xl p-5 flex flex-col justify-between">
        <div>
          <div className="flex items-center justify-between pb-3 border-b border-[#1a2332]">
            <div>
              <h3 className="text-sm font-semibold text-[#e8edf5] tracking-tight">
                Severity Distribution
              </h3>
              <p className="text-xs text-[#8b96a8] mt-0.5">
                Proportion of security alerts across 4 severity tiers
              </p>
            </div>
            <ShieldAlert className="w-4 h-4 text-[#8b96a8]" />
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-4">
            {severities.map((s) => {
              const cfg = SEVERITY_CONFIG[s.severity] || SEVERITY_CONFIG.LOW;
              return (
                <div
                  key={s.severity}
                  className={cn(
                    'p-3 rounded-lg border flex flex-col justify-between',
                    cfg.bg,
                    cfg.border
                  )}
                >
                  <span className={cn('text-[11px] font-semibold uppercase', cfg.color)}>
                    {cfg.label}
                  </span>
                  <div className="mt-2">
                    <div className="text-xl font-bold text-[#e8edf5]">
                      {s.count.toLocaleString()}
                    </div>
                    <div className="text-[10px] text-[#8b96a8] mt-0.5 font-medium">
                      {s.percentage}% of alerts
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Stacked bar visualization */}
        <div className="mt-5">
          <div className="h-2.5 w-full bg-[#161c28] rounded-full overflow-hidden flex">
            {totalEvents > 0 ? (
              severities.map((s) => {
                const cfg = SEVERITY_CONFIG[s.severity] || SEVERITY_CONFIG.LOW;
                if (s.percentage <= 0) return null;
                return (
                  <div
                    key={s.severity}
                    style={{ width: `${s.percentage}%` }}
                    className={cn('h-full transition-all duration-300', cfg.bar)}
                    title={`${cfg.label}: ${s.count} (${s.percentage}%)`}
                  />
                );
              })
            ) : (
              <div className="w-full h-full bg-[#1e2736]" />
            )}
          </div>
        </div>
      </div>

      {/* Event Type Distribution Card */}
      <div className="bg-[#0d1117] border border-[#1e2736] rounded-xl p-5 flex flex-col justify-between">
        <div>
          <div className="flex items-center justify-between pb-3 border-b border-[#1a2332]">
            <div>
              <h3 className="text-sm font-semibold text-[#e8edf5] tracking-tight">
                Event Category Distribution
              </h3>
              <p className="text-xs text-[#8b96a8] mt-0.5">
                Frequency breakdown by detected security event rule type
              </p>
            </div>
            <PieChart className="w-4 h-4 text-[#8b96a8]" />
          </div>

          <div className="mt-4 space-y-3">
            {eventTypes && eventTypes.length > 0 ? (
              eventTypes.map((item) => (
                <div key={item.name} className="space-y-1">
                  <div className="flex justify-between items-center text-xs">
                    <span className="font-medium text-[#e8edf5]">
                      {item.name.replace(/_/g, ' ')}
                    </span>
                    <div className="flex items-center gap-2">
                      <span className="text-[#8b96a8]">{item.count} events</span>
                      <span className="font-semibold text-[#3b7dd8]">{item.percentage}%</span>
                    </div>
                  </div>
                  <div className="h-1.5 w-full bg-[#161c28] rounded-full overflow-hidden">
                    <div
                      style={{ width: `${item.percentage}%` }}
                      className="h-full bg-[#3b7dd8] rounded-full transition-all duration-300"
                    />
                  </div>
                </div>
              ))
            ) : (
              <div className="py-8 text-center text-xs text-[#8b96a8]">
                No security event categories recorded in this period.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
