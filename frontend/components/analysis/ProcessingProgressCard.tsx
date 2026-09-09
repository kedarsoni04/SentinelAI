'use client';

import Link from 'next/link';
import { Loader2, ArrowRight, Ban, Film, CheckCircle2 } from 'lucide-react';
import type { AnalysisJob } from '@/types';
import JobStatusBadge from './JobStatusBadge';

interface ProcessingProgressCardProps {
  job: AnalysisJob;
  onCancel?: (jobId: string) => void;
}

export default function ProcessingProgressCard({ job, onCancel }: ProcessingProgressCardProps) {
  const isProcessing = job.status === 'PROCESSING' || job.status === 'QUEUED';
  const isCompleted = job.status === 'COMPLETED';

  return (
    <div className="bg-[#111620] border border-[#1e2736] rounded-xl p-5 space-y-4">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-3 min-w-0">
          <div className="w-10 h-10 rounded-lg bg-[#3b7dd8]/10 border border-[#3b7dd8]/20 flex items-center justify-center text-[#3b7dd8] shrink-0">
            {isProcessing ? (
              <Loader2 className="w-5 h-5 animate-spin text-[#3b7dd8]" />
            ) : isCompleted ? (
              <CheckCircle2 className="w-5 h-5 text-emerald-400" />
            ) : (
              <Film className="w-5 h-5 text-[#8b96a8]" />
            )}
          </div>
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-semibold text-[#e8edf5] truncate">
                {job.original_filename}
              </h3>
              <JobStatusBadge status={job.status} />
            </div>
            <p className="text-xs text-[#8b96a8] mt-0.5">
              Job ID: <span className="font-mono text-[#4e5a6b]">{job.id.slice(0, 8)}…</span>
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          {isProcessing && onCancel && (
            <button
              type="button"
              onClick={() => onCancel(job.id)}
              className="px-3 py-1.5 text-xs font-medium text-red-400 hover:bg-red-500/10 rounded-lg border border-red-500/20 flex items-center gap-1.5 transition-colors"
            >
              <Ban className="w-3.5 h-3.5" />
              Cancel
            </button>
          )}

          <Link
            href={`/dashboard/analysis/${job.id}`}
            className="px-3 py-1.5 text-xs font-medium text-[#3b7dd8] hover:bg-[#3b7dd8]/10 rounded-lg border border-[#3b7dd8]/20 flex items-center gap-1.5 transition-colors"
          >
            View Details
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      </div>

      {/* Progress bar */}
      <div className="space-y-1.5">
        <div className="flex justify-between items-center text-xs text-[#8b96a8]">
          <span>
            {job.status === 'QUEUED'
              ? 'Queued in background processing worker…'
              : job.status === 'PROCESSING'
              ? 'Analyzing frames with OpenCV…'
              : job.status === 'COMPLETED'
              ? 'Processing pipeline completed'
              : 'Analysis stopped'}
          </span>
          <span className="font-mono font-medium text-[#e8edf5]">{job.progress}%</span>
        </div>
        <div className="w-full h-2 bg-[#161c28] rounded-full overflow-hidden">
          <div
            className={`h-full transition-all duration-300 rounded-full ${
              job.status === 'COMPLETED'
                ? 'bg-emerald-500'
                : job.status === 'FAILED'
                ? 'bg-red-500'
                : job.status === 'CANCELLED'
                ? 'bg-slate-500'
                : 'bg-[#3b7dd8]'
            }`}
            style={{ width: `${job.progress}%` }}
          />
        </div>
      </div>

      {/* Metadata stats bar */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2 border-t border-[#1e2736]/60 text-xs">
        <div>
          <span className="text-[#4e5a6b] block">Sampled Frames</span>
          <span className="text-[#e8edf5] font-mono font-medium mt-0.5 block">
            {job.processed_frames}
            {job.sampled_frames > 0 ? ` / ${job.sampled_frames}` : ''}
          </span>
        </div>
        <div>
          <span className="text-[#4e5a6b] block">Resolution</span>
          <span className="text-[#e8edf5] font-mono font-medium mt-0.5 block">
            {job.width && job.height ? `${job.width} × ${job.height}` : 'Extracting…'}
          </span>
        </div>
        <div>
          <span className="text-[#4e5a6b] block">FPS</span>
          <span className="text-[#e8edf5] font-mono font-medium mt-0.5 block">
            {job.fps ? `${job.fps} fps` : 'Extracting…'}
          </span>
        </div>
        <div>
          <span className="text-[#4e5a6b] block">Video Duration</span>
          <span className="text-[#e8edf5] font-mono font-medium mt-0.5 block">
            {job.duration_seconds ? `${job.duration_seconds.toFixed(1)}s` : 'Extracting…'}
          </span>
        </div>
      </div>
    </div>
  );
}
