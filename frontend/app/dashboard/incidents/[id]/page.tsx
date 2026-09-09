'use client';

import { useEffect, useRef, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import {
  ArrowLeft,
  Brain,
  Camera,
  CheckSquare,
  Clock,
  FileText,
  Loader2,
  ShieldAlert,
  XCircle,
  Zap,
} from 'lucide-react';
import { getIncidentReport } from '@/services/incidents';
import type { IncidentReport } from '@/types';
import IncidentRiskBadge from '@/components/incidents/IncidentRiskBadge';
import DisclaimerBanner from '@/components/incidents/DisclaimerBanner';
import IncidentTimeline from '@/components/incidents/IncidentTimeline';

const POLL_INTERVAL_MS = 2500;

function SectionCard({
  icon: Icon,
  title,
  children,
  iconClass = 'text-[#3b7dd8]',
}: {
  icon: React.ComponentType<{ className?: string }>;
  title: string;
  children: React.ReactNode;
  iconClass?: string;
}) {
  return (
    <div className="rounded-xl border border-[#1e2736] bg-[#0d1117] p-5">
      <div className="flex items-center gap-2 mb-4">
        <Icon className={`w-4 h-4 shrink-0 ${iconClass}`} />
        <h2 className="text-sm font-semibold text-[#e8edf5]">{title}</h2>
      </div>
      {children}
    </div>
  );
}

function SkeletonSection() {
  return (
    <div className="rounded-xl border border-[#1e2736] bg-[#0d1117] p-5 space-y-3">
      <div className="h-4 w-32 bg-[#1e2736] rounded animate-pulse" />
      <div className="h-3 w-full bg-[#161c28] rounded animate-pulse" />
      <div className="h-3 w-5/6 bg-[#161c28] rounded animate-pulse" />
      <div className="h-3 w-4/6 bg-[#161c28] rounded animate-pulse" />
    </div>
  );
}

function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleString('en-US', {
      weekday: 'short',
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return iso;
  }
}

export default function IncidentReportDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [report, setReport] = useState<IncidentReport | null>(null);
  const [error, setError] = useState<string | null>(null);
  const pollRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    if (!id) return;

    const load = async () => {
      try {
        const data = await getIncidentReport(id);
        setReport(data);

        if (data.status === 'GENERATING') {
          // Keep polling until done
          if (!pollRef.current) {
            pollRef.current = setInterval(async () => {
              try {
                const updated = await getIncidentReport(id);
                setReport(updated);
                if (updated.status !== 'GENERATING' && pollRef.current) {
                  clearInterval(pollRef.current);
                  pollRef.current = null;
                }
              } catch {
                /* ignore interim errors */
              }
            }, POLL_INTERVAL_MS);
          }
        }
      } catch (err: unknown) {
        const errorMsg =
          (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
          'Failed to load incident report.';
        setError(errorMsg);
      }
    };

    load();
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, [id]);

  // ─── Error State ────────────────────────────────────────────────────────────
  if (error) {
    return (
      <div className="max-w-3xl mx-auto">
        <button
          onClick={() => router.back()}
          className="flex items-center gap-2 text-sm text-[#8b96a8] hover:text-[#e8edf5] mb-6 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" /> Back
        </button>
        <div className="flex items-center gap-3 rounded-xl border border-red-500/20 bg-red-500/8 p-5">
          <XCircle className="w-5 h-5 text-red-400 shrink-0" />
          <p className="text-sm text-red-400">{error}</p>
        </div>
      </div>
    );
  }

  // ─── Loading / Generating State ─────────────────────────────────────────────
  if (!report || report.status === 'GENERATING') {
    return (
      <div className="max-w-3xl mx-auto space-y-6">
        <button
          onClick={() => router.back()}
          className="flex items-center gap-2 text-sm text-[#8b96a8] hover:text-[#e8edf5] transition-colors"
        >
          <ArrowLeft className="w-4 h-4" /> Back to Incidents
        </button>

        <div className="rounded-xl border border-[#3b7dd8]/30 bg-[#0d1117] p-6 flex items-center gap-4">
          <Loader2 className="w-6 h-6 text-[#3b7dd8] animate-spin shrink-0" />
          <div>
            <p className="text-sm font-medium text-[#e8edf5]">Generating AI Analysis…</p>
            <p className="text-xs text-[#8b96a8] mt-0.5">
              The AI is processing your incident context. This usually takes a few seconds.
            </p>
          </div>
        </div>

        <SkeletonSection />
        <SkeletonSection />
        <SkeletonSection />
      </div>
    );
  }

  // ─── Failed State ───────────────────────────────────────────────────────────
  if (report.status === 'FAILED') {
    return (
      <div className="max-w-3xl mx-auto space-y-6">
        <button
          onClick={() => router.back()}
          className="flex items-center gap-2 text-sm text-[#8b96a8] hover:text-[#e8edf5] transition-colors"
        >
          <ArrowLeft className="w-4 h-4" /> Back to Incidents
        </button>
        <div className="rounded-xl border border-red-500/25 bg-[#0d1117] p-6">
          <div className="flex items-center gap-3 mb-3">
            <XCircle className="w-5 h-5 text-red-400" />
            <h2 className="text-sm font-semibold text-[#e8edf5]">Analysis Failed</h2>
          </div>
          <p className="text-sm text-[#8b96a8]">
            {report.error_message ?? 'The AI analysis could not be completed.'}
          </p>
        </div>
      </div>
    );
  }

  // ─── Completed Report ───────────────────────────────────────────────────────
  return (
    <div className="max-w-3xl mx-auto space-y-5">
      {/* Back nav */}
      <button
        onClick={() => router.back()}
        className="flex items-center gap-2 text-sm text-[#8b96a8] hover:text-[#e8edf5] transition-colors"
      >
        <ArrowLeft className="w-4 h-4" /> Back to Incidents
      </button>

      {/* Report Header */}
      <div className="rounded-xl border border-[#1e2736] bg-[#0d1117] p-5">
        <div className="flex items-start justify-between gap-4 mb-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-violet-500/20 to-[#3b7dd8]/20 border border-violet-500/20 flex items-center justify-center">
              <Brain className="w-5 h-5 text-violet-400" />
            </div>
            <div>
              <h1 className="text-base font-semibold text-[#e8edf5]">AI Incident Report</h1>
              <p className="text-xs text-[#4e5a6b] mt-0.5">
                {formatDate(report.created_at)}
              </p>
            </div>
          </div>
          <IncidentRiskBadge level={report.risk_level} size="md" />
        </div>

        {/* Metadata pills */}
        <div className="flex flex-wrap gap-2">
          {report.camera_name && (
            <span className="inline-flex items-center gap-1.5 text-[11px] text-[#8b96a8] bg-[#161c28] border border-[#1e2736] rounded-full px-2.5 py-1">
              <Camera className="w-3 h-3" />
              {report.camera_name}
            </span>
          )}
          <span className="inline-flex items-center gap-1.5 text-[11px] text-[#8b96a8] bg-[#161c28] border border-[#1e2736] rounded-full px-2.5 py-1">
            <FileText className="w-3 h-3" />
            {report.event_count} event{report.event_count !== 1 ? 's' : ''}
          </span>
          <span className="inline-flex items-center gap-1.5 text-[11px] text-[#8b96a8] bg-[#161c28] border border-[#1e2736] rounded-full px-2.5 py-1">
            <Zap className="w-3 h-3" />
            {report.ai_provider}
            {report.ai_model ? ` · ${report.ai_model}` : ''}
          </span>
          {report.prompt_tokens && (
            <span className="inline-flex items-center gap-1.5 text-[11px] text-[#8b96a8] bg-[#161c28] border border-[#1e2736] rounded-full px-2.5 py-1">
              <Clock className="w-3 h-3" />
              {report.prompt_tokens.toLocaleString()} tokens
            </span>
          )}
        </div>
      </div>

      {/* Mandatory Disclaimer */}
      <DisclaimerBanner text={report.disclaimer ?? undefined} />

      {/* Summary */}
      {report.summary && (
        <SectionCard icon={FileText} title="Incident Summary">
          <p className="text-sm text-[#c8d4e5] leading-relaxed">{report.summary}</p>
        </SectionCard>
      )}

      {/* Timeline */}
      {report.timeline && report.timeline.length > 0 && (
        <SectionCard icon={Clock} title="Event Timeline" iconClass="text-violet-400">
          <IncidentTimeline items={report.timeline} />
        </SectionCard>
      )}

      {/* Risk Assessment */}
      {report.risk_explanation && (
        <SectionCard icon={ShieldAlert} title="Risk Assessment" iconClass="text-orange-400">
          <div className="flex items-center gap-3 mb-3">
            <IncidentRiskBadge level={report.risk_level} size="md" />
          </div>
          <p className="text-sm text-[#c8d4e5] leading-relaxed">{report.risk_explanation}</p>
        </SectionCard>
      )}

      {/* Recommended Actions */}
      {report.recommendations && report.recommendations.length > 0 && (
        <SectionCard icon={CheckSquare} title="Recommended Human Review Actions" iconClass="text-emerald-400">
          <ol className="space-y-3">
            {report.recommendations.map((rec, i) => (
              <li key={i} className="flex gap-3">
                <span className="flex-shrink-0 w-6 h-6 rounded-full bg-emerald-500/15 border border-emerald-500/25 text-emerald-400 text-xs font-bold flex items-center justify-center">
                  {i + 1}
                </span>
                <p className="text-sm text-[#c8d4e5] leading-relaxed pt-0.5">{rec}</p>
              </li>
            ))}
          </ol>
        </SectionCard>
      )}

      {/* Footer note */}
      <p className="text-[11px] text-[#4e5a6b] text-center pb-6">
        Report ID: {report.id} · Generated by {report.ai_provider}
        {report.ai_model ? ` (${report.ai_model})` : ''} · SentinelAI Phase 8
      </p>
    </div>
  );
}
