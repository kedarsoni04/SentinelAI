import React from 'react';
import type { SecurityEventStatus } from '@/types';

interface EventStatusBadgeProps {
  status: SecurityEventStatus | string;
  className?: string;
}

export default function EventStatusBadge({ status, className = '' }: EventStatusBadgeProps) {
  const stat = status.toUpperCase();

  switch (stat) {
    case 'OPEN':
      return (
        <span
          className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[11px] font-mono font-medium bg-red-500/10 text-red-400 border border-red-500/20 ${className}`}
        >
          <span className="w-1.5 h-1.5 rounded-full bg-red-400 animate-pulse" />
          OPEN
        </span>
      );
    case 'ACKNOWLEDGED':
      return (
        <span
          className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[11px] font-mono font-medium bg-amber-500/10 text-amber-400 border border-amber-500/20 ${className}`}
        >
          <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
          ACKNOWLEDGED
        </span>
      );
    case 'RESOLVED':
      return (
        <span
          className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[11px] font-mono font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 ${className}`}
        >
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
          RESOLVED
        </span>
      );
    case 'DISMISSED':
    default:
      return (
        <span
          className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[11px] font-mono font-medium bg-[#1e2736] text-[#8b96a8] border border-[#2a3649] ${className}`}
        >
          DISMISSED
        </span>
      );
  }
}
