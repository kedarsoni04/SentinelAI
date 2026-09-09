'use client';

import Link from 'next/link';
import { Film, ArrowRight, Ban, Clock, Layers, Target } from 'lucide-react';
import type { AnalysisJob } from '@/types';
import JobStatusBadge from './JobStatusBadge';

interface AnalysisJobListProps {
  jobs: AnalysisJob[];
  onCancel?: (jobId: string) => void;
}

export default function AnalysisJobList({ jobs, onCancel }: AnalysisJobListProps) {
  if (jobs.length === 0) {
    return (
      <div className="bg-[#111620] border border-[#1e2736] rounded-xl p-12 text-center">
        <div className="w-12 h-12 rounded-full bg-[#161c28] border border-[#1e2736] flex items-center justify-center mx-auto mb-3 text-[#4e5a6b]">
          <Film className="w-6 h-6" />
        </div>
        <h3 className="text-sm font-semibold text-[#e8edf5] mb-1">No video analyses yet</h3>
        <p className="text-xs text-[#8b96a8] max-w-sm mx-auto">
          Upload a surveillance footage clip above to extract metadata and sample representative
          frames using SentinelAI&apos;s OpenCV pipeline.
        </p>
      </div>
    );
  }

  const formatDuration = (secs: number | null) => {
    if (!secs) return '—';
    const m = Math.floor(secs / 60);
    const s = Math.floor(secs % 60);
    return `${m}m ${s}s`;
  };

  const formatDate = (dateStr: string) => {
    try {
      const d = new Date(dateStr);
      return d.toLocaleDateString(undefined, {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return dateStr;
    }
  };

  return (
    <div className="bg-[#111620] border border-[#1e2736] rounded-xl overflow-hidden">
      <div className="px-5 py-4 border-b border-[#1e2736] flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Film className="w-4 h-4 text-[#3b7dd8]" />
          <h3 className="text-sm font-semibold text-[#e8edf5]">Analysis History</h3>
          <span className="text-xs text-[#8b96a8] font-mono bg-[#161c28] px-2 py-0.5 rounded border border-[#1e2736]">
            {jobs.length} total
          </span>
        </div>
      </div>

      <div className="divide-y divide-[#1e2736]">
        {jobs.map((job) => {
          const isProcessing = job.status === 'PROCESSING' || job.status === 'QUEUED';

          return (
            <div
              key={job.id}
              className="p-4 hover:bg-[#161c28]/40 transition-colors flex flex-col sm:flex-row sm:items-center justify-between gap-4"
            >
              <div className="flex items-start gap-3 min-w-0">
                <div className="w-9 h-9 rounded-lg bg-[#161c28] border border-[#1e2736] flex items-center justify-center text-[#8b96a8] shrink-0 mt-0.5">
                  <Film className="w-4 h-4" />
                </div>
                <div className="min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <Link
                      href={`/dashboard/analysis/${job.id}`}
                      className="text-sm font-medium text-[#e8edf5] hover:text-[#3b7dd8] transition-colors truncate"
                    >
                      {job.original_filename}
                    </Link>
                    <JobStatusBadge status={job.status} />
                  </div>

                  <div className="flex items-center gap-3 text-xs text-[#4e5a6b] mt-1 flex-wrap font-mono">
                    <span className="flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {formatDuration(job.duration_seconds)}
                    </span>
                    <span>•</span>
                    <span>
                      {job.width && job.height ? `${job.width}×${job.height}` : '—'}
                    </span>
                    <span>•</span>
                    <span className="flex items-center gap-1">
                      <Layers className="w-3 h-3" />
                      {job.sampled_frames} sampled frames
                    </span>
                    {job.status === 'COMPLETED' && (
                      <>
                        <span>•</span>
                        <span className="flex items-center gap-1 text-cyan-400/90">
                          <Target className="w-3 h-3 text-cyan-400" />
                          YOLOv11 Analyzed
                        </span>
                      </>
                    )}
                    <span>•</span>
                    <span className="text-[#8b96a8]">{formatDate(job.created_at)}</span>
                  </div>
                </div>
              </div>

              {/* Action column */}
              <div className="flex items-center gap-2 shrink-0 self-end sm:self-center">
                {isProcessing && onCancel && (
                  <button
                    type="button"
                    onClick={() => onCancel(job.id)}
                    className="px-3 py-1.5 text-xs text-red-400 hover:bg-red-500/10 rounded-lg border border-red-500/20 flex items-center gap-1 transition-colors"
                  >
                    <Ban className="w-3 h-3" />
                    Cancel
                  </button>
                )}

                <Link
                  href={`/dashboard/analysis/${job.id}`}
                  className="px-3 py-1.5 text-xs font-medium text-[#e8edf5] hover:text-[#3b7dd8] hover:bg-[#161c28] rounded-lg border border-[#1e2736] flex items-center gap-1.5 transition-colors"
                >
                  View Details
                  <ArrowRight className="w-3.5 h-3.5" />
                </Link>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
