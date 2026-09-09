import React from 'react';
import type { SecurityEventSeverity } from '@/types';

interface EventSeverityBadgeProps {
  severity: SecurityEventSeverity;
  className?: string;
}

export default function EventSeverityBadge({ severity, className = '' }: EventSeverityBadgeProps) {
  const sev = severity.toUpperCase();

  switch (sev) {
    case 'CRITICAL':
      return (
        <span
          className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-mono font-semibold bg-red-500/15 text-red-400 border border-red-500/30 tracking-wide ${className}`}
        >
          CRITICAL
        </span>
      );
    case 'HIGH':
      return (
        <span
          className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-mono font-semibold bg-orange-500/15 text-orange-400 border border-orange-500/30 tracking-wide ${className}`}
        >
          HIGH
        </span>
      );
    case 'MEDIUM':
      return (
        <span
          className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-mono font-semibold bg-amber-500/15 text-amber-400 border border-amber-500/30 tracking-wide ${className}`}
        >
          MEDIUM
        </span>
      );
    case 'LOW':
    default:
      return (
        <span
          className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-mono font-semibold bg-blue-500/15 text-blue-400 border border-blue-500/30 tracking-wide ${className}`}
        >
          LOW
        </span>
      );
  }
}
