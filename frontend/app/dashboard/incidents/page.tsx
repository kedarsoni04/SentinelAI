'use client';

import { useEffect, useRef, useState, useCallback } from 'react';
import { Brain, RefreshCw, AlertTriangle, FileText, Filter } from 'lucide-react';
import { getIncidentReports, deleteIncidentReport } from '@/services/incidents';
import type { IncidentReportListItem, IncidentRiskLevel } from '@/types';
import IncidentReportCard from '@/components/incidents/IncidentReportCard';
import { cn } from '@/lib/utils';

const POLL_INTERVAL_MS = 3000;

const riskFilters: { label: string; value: IncidentRiskLevel | 'ALL' }[] = [
  { label: 'All', value: 'ALL' },
  { label: 'Critical', value: 'CRITICAL' },
  { label: 'High', value: 'HIGH' },
  { label: 'Medium', value: 'MEDIUM' },
  { label: 'Low', value: 'LOW' },
];

export default function IncidentsPage() {
  const [reports, setReports] = useState<IncidentReportListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [riskFilter, setRiskFilter] = useState<IncidentRiskLevel | 'ALL'>('ALL');
  const pollRef = useRef<NodeJS.Timeout | null>(null);

  const fetchReports = useCallback(async (showLoader = false) => {
    if (showLoader) setLoading(true);
    try {
      const data = await getIncidentReports({ limit: 100 });
      setReports(data);
      setError(null);
    } catch (err: unknown) {
      const errorMsg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        'Failed to load incident reports.';
      setError(errorMsg);
    } finally {
      if (showLoader) setLoading(false);
    }
  }, []);

  // Initial load + auto-poll while any report is GENERATING
  useEffect(() => {
    fetchReports(true);

    const startPolling = () => {
      pollRef.current = setInterval(async () => {
        const data = await getIncidentReports({ limit: 100 }).catch(() => null);
        if (data) {
          setReports(data);
          const stillGenerating = data.some((r) => r.status === 'GENERATING');
          if (!stillGenerating && pollRef.current) {
            clearInterval(pollRef.current);
            pollRef.current = null;
          }
        }
      }, POLL_INTERVAL_MS);
    };

    startPolling();
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, [fetchReports]);

  // Restart polling if a new GENERATING report appears
  useEffect(() => {
    const hasGenerating = reports.some((r) => r.status === 'GENERATING');
    if (hasGenerating && !pollRef.current) {
      pollRef.current = setInterval(async () => {
        const data = await getIncidentReports({ limit: 100 }).catch(() => null);
        if (data) {
          setReports(data);
          const stillGenerating = data.some((r) => r.status === 'GENERATING');
          if (!stillGenerating && pollRef.current) {
            clearInterval(pollRef.current);
            pollRef.current = null;
          }
        }
      }, POLL_INTERVAL_MS);
    }
  }, [reports]);

  const handleDelete = async (id: string) => {
    if (!confirm('Delete this incident report? This cannot be undone.')) return;
    try {
      await deleteIncidentReport(id);
      setReports((prev) => prev.filter((r) => r.id !== id));
    } catch {
      alert('Failed to delete report.');
    }
  };

  const filtered =
    riskFilter === 'ALL'
      ? reports
      : reports.filter((r) => r.risk_level === riskFilter);

  const generatingCount = reports.filter((r) => r.status === 'GENERATING').length;

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Page Header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-3 mb-1">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-violet-500/20 to-[#3b7dd8]/20 border border-violet-500/20 flex items-center justify-center">
              <Brain className="w-4.5 h-4.5 text-violet-400" />
            </div>
            <h1 className="text-xl font-semibold text-[#e8edf5]">Incident Intelligence</h1>
          </div>
          <p className="text-sm text-[#8b96a8] ml-12">
            AI-assisted analysis reports for SOC operator review. All findings require human verification.
          </p>
        </div>
        <button
          onClick={() => fetchReports(false)}
          className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm text-[#8b96a8] hover:text-[#e8edf5] hover:bg-[#161c28] transition-colors"
        >
          <RefreshCw className="w-4 h-4" />
          Refresh
        </button>
      </div>

      {/* Generating Banner */}
      {generatingCount > 0 && (
        <div className="flex items-center gap-3 rounded-lg border border-[#3b7dd8]/30 bg-[#3b7dd8]/8 px-4 py-3">
          <div className="w-2 h-2 rounded-full bg-[#3b7dd8] animate-pulse" />
          <p className="text-sm text-[#3b7dd8]">
            {generatingCount} report{generatingCount > 1 ? 's' : ''} being generated…
          </p>
        </div>
      )}

      {/* Filters */}
      {reports.length > 0 && (
        <div className="flex items-center gap-2 flex-wrap">
          <Filter className="w-3.5 h-3.5 text-[#4e5a6b]" />
          {riskFilters.map((f) => (
            <button
              key={f.value}
              onClick={() => setRiskFilter(f.value)}
              className={cn(
                'px-3 py-1 rounded-full text-xs font-medium transition-colors',
                riskFilter === f.value
                  ? 'bg-[#3b7dd8] text-white'
                  : 'bg-[#161c28] text-[#8b96a8] hover:text-[#e8edf5] border border-[#1e2736]'
              )}
            >
              {f.label}
            </button>
          ))}
        </div>
      )}

      {/* Content */}
      {loading ? (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              className="h-36 rounded-xl bg-[#0d1117] border border-[#1e2736] animate-pulse"
            />
          ))}
        </div>
      ) : error ? (
        <div className="flex items-center gap-3 rounded-xl border border-red-500/20 bg-red-500/8 p-5">
          <AlertTriangle className="w-5 h-5 text-red-400 shrink-0" />
          <p className="text-sm text-red-400">{error}</p>
        </div>
      ) : filtered.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 text-center">
          <div className="w-16 h-16 rounded-2xl bg-[#161c28] border border-[#1e2736] flex items-center justify-center mb-4">
            <FileText className="w-7 h-7 text-[#4e5a6b]" />
          </div>
          <h3 className="text-[#e8edf5] font-medium mb-2">No incident reports yet</h3>
          <p className="text-sm text-[#8b96a8] max-w-sm">
            Generate AI incident reports from the{' '}
            <a href="/dashboard/events" className="text-[#3b7dd8] hover:underline">
              Security Events
            </a>{' '}
            page by selecting events and clicking{' '}
            <strong className="text-[#c8d4e5]">Generate AI Report</strong>.
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {filtered.map((report) => (
            <IncidentReportCard
              key={report.id}
              report={report}
              onDelete={handleDelete}
            />
          ))}
        </div>
      )}

      {/* Info footer */}
      {reports.length > 0 && (
        <p className="text-[11px] text-[#4e5a6b] text-center pb-4">
          {reports.length} report{reports.length !== 1 ? 's' : ''} total ·{' '}
          AI analysis is for human review only — not a substitute for operator judgment
        </p>
      )}
    </div>
  );
}
