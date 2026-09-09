import { CheckCircle2, Clock, Loader2, AlertCircle, Ban } from 'lucide-react';
import type { JobStatus } from '@/types';

interface JobStatusBadgeProps {
  status: JobStatus;
  className?: string;
}

export default function JobStatusBadge({ status, className = '' }: JobStatusBadgeProps) {
  switch (status) {
    case 'QUEUED':
      return (
        <span
          className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-[#3b7dd8]/10 text-[#3b7dd8] border border-[#3b7dd8]/20 ${className}`}
        >
          <Clock className="w-3 h-3" />
          Queued
        </span>
      );

    case 'PROCESSING':
      return (
        <span
          className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-amber-500/10 text-amber-400 border border-amber-500/20 ${className}`}
        >
          <Loader2 className="w-3 h-3 animate-spin" />
          Processing
        </span>
      );

    case 'COMPLETED':
      return (
        <span
          className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 ${className}`}
        >
          <CheckCircle2 className="w-3 h-3" />
          Completed
        </span>
      );

    case 'FAILED':
      return (
        <span
          className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-500/10 text-red-400 border border-red-500/20 ${className}`}
        >
          <AlertCircle className="w-3 h-3" />
          Failed
        </span>
      );

    case 'CANCELLED':
      return (
        <span
          className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-500/10 text-slate-400 border border-slate-500/20 ${className}`}
        >
          <Ban className="w-3 h-3" />
          Cancelled
        </span>
      );

    default:
      return null;
  }
}
