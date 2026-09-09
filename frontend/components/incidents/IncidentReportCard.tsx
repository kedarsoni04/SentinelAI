import Link from 'next/link';
import { Camera, Clock, FileText, Loader2, Trash2, XCircle } from 'lucide-react';
import type { IncidentReportListItem } from '@/types';
import IncidentRiskBadge from './IncidentRiskBadge';
import { cn } from '@/lib/utils';

interface IncidentReportCardProps {
  report: IncidentReportListItem;
  onDelete?: (id: string) => void;
}

function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return iso;
  }
}

function StatusIndicator({ status }: { status: string }) {
  if (status === 'GENERATING') {
    return (
      <span className="inline-flex items-center gap-1.5 text-[10px] font-semibold text-[#3b7dd8] uppercase tracking-wider">
        <Loader2 className="w-3 h-3 animate-spin" />
        Generating…
      </span>
    );
  }
  if (status === 'FAILED') {
    return (
      <span className="inline-flex items-center gap-1.5 text-[10px] font-semibold text-red-400 uppercase tracking-wider">
        <XCircle className="w-3 h-3" />
        Failed
      </span>
    );
  }
  return null;
}

export default function IncidentReportCard({ report, onDelete }: IncidentReportCardProps) {
  const isGenerating = report.status === 'GENERATING';
  const isFailed = report.status === 'FAILED';

  return (
    <div
      className={cn(
        'group relative rounded-xl border bg-[#0d1117] p-5 transition-all duration-200',
        isGenerating
          ? 'border-[#3b7dd8]/40 shadow-[0_0_0_1px_rgba(59,125,216,0.15)]'
          : isFailed
          ? 'border-red-500/25'
          : 'border-[#1e2736] hover:border-[#2a3548]'
      )}
    >
      {/* Header row */}
      <div className="flex items-start justify-between gap-4 mb-3">
        <div className="flex items-center gap-2 flex-wrap">
          {report.status === 'COMPLETED' && report.risk_level && (
            <IncidentRiskBadge level={report.risk_level} size="sm" />
          )}
          {report.status !== 'COMPLETED' && (
            <StatusIndicator status={report.status} />
          )}
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <span className="text-[10px] font-mono text-[#4e5a6b] uppercase tracking-wider border border-[#1e2736] rounded px-1.5 py-0.5">
            {report.ai_provider}
          </span>
          {onDelete && (
            <button
              onClick={(e) => {
                e.preventDefault();
                onDelete(report.id);
              }}
              className="opacity-0 group-hover:opacity-100 transition-opacity p-1 rounded hover:bg-red-500/10 text-[#4e5a6b] hover:text-red-400"
              title="Delete report"
            >
              <Trash2 className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </div>

      {/* Summary preview */}
      <p className="text-sm text-[#c8d4e5] leading-relaxed mb-3 line-clamp-2">
        {isGenerating
          ? 'AI analysis in progress — this usually takes a few seconds…'
          : isFailed
          ? 'Analysis failed. The report could not be generated.'
          : report.summary_preview || 'No summary available.'}
      </p>

      {/* Meta row */}
      <div className="flex items-center gap-4 text-[11px] text-[#4e5a6b] flex-wrap">
        {report.camera_name && (
          <span className="flex items-center gap-1">
            <Camera className="w-3 h-3" />
            {report.camera_name}
          </span>
        )}
        <span className="flex items-center gap-1">
          <FileText className="w-3 h-3" />
          {report.event_count} event{report.event_count !== 1 ? 's' : ''}
        </span>
        <span className="flex items-center gap-1">
          <Clock className="w-3 h-3" />
          {formatDate(report.created_at)}
        </span>
      </div>

      {/* Link overlay for completed reports */}
      {report.status === 'COMPLETED' && (
        <Link
          href={`/dashboard/incidents/${report.id}`}
          className="absolute inset-0 rounded-xl"
          aria-label="View full incident report"
        />
      )}

      {/* View button */}
      {report.status === 'COMPLETED' && (
        <div className="mt-3 pt-3 border-t border-[#1e2736] flex justify-end">
          <span className="text-[11px] font-medium text-[#3b7dd8] group-hover:text-[#5a9be0] transition-colors">
            View Full Report →
          </span>
        </div>
      )}
    </div>
  );
}
