'use client';

import { useCallback, useEffect, useState, useRef } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import {
  ChevronLeft,
  Clock,
  Layers,
  Cpu,
  Calendar,
  AlertCircle,
  CheckCircle2,
  RefreshCw,
  Maximize,
  Radio,
} from 'lucide-react';
import type { AnalysisJob, AnalysisResult, DetectionSummary, TrackingSummary } from '@/types';
import {
  getAnalysisJob,
  getAnalysisResults,
  getDetectionSummary,
  getTrackingSummary,
  cancelAnalysis,
} from '@/services/videoAnalysis';
import { extractErrorMessage } from '@/services/auth';
import JobStatusBadge from '@/components/analysis/JobStatusBadge';
import ProcessingProgressCard from '@/components/analysis/ProcessingProgressCard';
import FrameGallery from '@/components/analysis/FrameGallery';
import DetectionSummaryCard from '@/components/analysis/DetectionSummaryCard';
import TrackingSummaryCard from '@/components/analysis/TrackingSummaryCard';
import TrackedObjectsPanel from '@/components/analysis/TrackedObjectsPanel';
import SecurityEventsPanel from '@/components/analysis/SecurityEventsPanel';
import { Toast, useToast } from '@/components/ui/Toast';

export default function AnalysisDetailPage() {
  const params = useParams();
  const jobId = params.id as string;

  const [job, setJob] = useState<AnalysisJob | null>(null);
  const [results, setResults] = useState<AnalysisResult[]>([]);
  const [summary, setSummary] = useState<DetectionSummary | null>(null);
  const [trackingSummary, setTrackingSummary] = useState<TrackingSummary | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const { toasts, showToast, dismissToast } = useToast();

  const pollTimerRef = useRef<NodeJS.Timeout | null>(null);

  const loadData = useCallback(async (initial = false) => {
    if (initial) setIsLoading(true);
    try {
      const jobData = await getAnalysisJob(jobId);
      setJob(jobData);

      // If job is completed, fetch results, detection summary, and tracking summary
      if (jobData.status === 'COMPLETED') {
        const [resultsData, summaryData, trackingData] = await Promise.all([
          getAnalysisResults(jobId),
          getDetectionSummary(jobId).catch(() => null),
          getTrackingSummary(jobId).catch(() => null),
        ]);
        setResults(resultsData);
        if (summaryData) setSummary(summaryData);
        if (trackingData) setTrackingSummary(trackingData);
      }
    } catch (err: unknown) {
      if (initial) {
        setError(extractErrorMessage(err));
      }
    } finally {
      if (initial) setIsLoading(false);
    }
  }, [jobId]);

  useEffect(() => {
    loadData(true);
  }, [loadData]);

  // Polling if job is still QUEUED or PROCESSING
  useEffect(() => {
    if (job?.status === 'QUEUED' || job?.status === 'PROCESSING') {
      pollTimerRef.current = setTimeout(() => {
        loadData(false);
      }, 2000);
    }

    return () => {
      if (pollTimerRef.current) {
        clearTimeout(pollTimerRef.current);
      }
    };
  }, [job, loadData]);

  const handleCancel = async () => {
    try {
      await cancelAnalysis(jobId);
      showToast('success', 'Analysis job cancelled.');
      loadData(false);
    } catch (err: unknown) {
      showToast('error', extractErrorMessage(err));
    }
  };

  const formatSeconds = (sec: number | null) => {
    if (!sec) return '—';
    const m = Math.floor(sec / 60);
    const s = Math.floor(sec % 60);
    return `${m}m ${s}s (${sec.toFixed(1)}s)`;
  };

  const formatTimestamp = (dStr: string | null) => {
    if (!dStr) return '—';
    try {
      return new Date(dStr).toLocaleString(undefined, {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
      });
    } catch {
      return dStr;
    }
  };

  if (isLoading) {
    return (
      <div className="max-w-6xl mx-auto py-16 text-center space-y-3">
        <div className="w-8 h-8 border-2 border-[#3b7dd8] border-t-transparent rounded-full animate-spin mx-auto" />
        <p className="text-sm text-[#8b96a8]">Loading analysis pipeline data…</p>
      </div>
    );
  }

  if (error || !job) {
    return (
      <div className="max-w-6xl mx-auto space-y-4">
        <Link
          href="/dashboard/analysis"
          className="inline-flex items-center gap-1.5 text-xs text-[#8b96a8] hover:text-[#e8edf5] transition-colors"
        >
          <ChevronLeft className="w-4 h-4" />
          Back to Video Analysis
        </Link>
        <div className="bg-[#111620] border border-red-500/20 rounded-xl p-8 text-center space-y-3">
          <AlertCircle className="w-8 h-8 text-red-400 mx-auto" />
          <h2 className="text-base font-semibold text-[#e8edf5]">Analysis Not Found</h2>
          <p className="text-sm text-[#8b96a8] max-w-sm mx-auto">
            {error || 'This analysis job could not be retrieved.'}
          </p>
        </div>
      </div>
    );
  }

  const isProcessing = job.status === 'QUEUED' || job.status === 'PROCESSING';

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Toast Alert Stack */}
      <Toast toasts={toasts} onDismiss={dismissToast} />

      {/* Navigation & Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <Link
            href="/dashboard/analysis"
            className="inline-flex items-center gap-1 text-xs text-[#8b96a8] hover:text-[#e8edf5] mb-2 transition-colors"
          >
            <ChevronLeft className="w-3.5 h-3.5" />
            Back to Video Analysis
          </Link>
          <div className="flex items-center gap-3 flex-wrap">
            <h1 className="text-xl font-semibold text-[#e8edf5]">{job.original_filename}</h1>
            <JobStatusBadge status={job.status} />
          </div>
          <p className="text-xs text-[#4e5a6b] font-mono mt-0.5">Job ID: {job.id}</p>
        </div>

        <div className="flex items-center gap-2">
          <Link
            href={`/dashboard/monitoring?jobId=${job.id}`}
            className="px-3 py-1.5 text-xs font-medium text-white bg-[#3b7dd8] hover:bg-[#2b6dc8] rounded-lg flex items-center gap-1.5 transition-colors shadow-sm"
          >
            <Radio className="w-3.5 h-3.5" />
            Live Monitoring
          </Link>
          <button
            type="button"
            onClick={() => loadData(false)}
            className="px-3 py-1.5 text-xs font-medium text-[#8b96a8] hover:text-[#e8edf5] bg-[#111620] hover:bg-[#161c28] border border-[#1e2736] rounded-lg flex items-center gap-1.5 transition-colors"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            Refresh
          </button>
        </div>
      </div>

      {/* Active Processing Card if still running */}
      {isProcessing && (
        <ProcessingProgressCard job={job} onCancel={handleCancel} />
      )}

      {/* Video Specifications & Pipeline Metrics Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        <div className="bg-[#111620] border border-[#1e2736] rounded-xl p-4">
          <div className="flex items-center gap-1.5 text-xs text-[#8b96a8] mb-1">
            <Clock className="w-3.5 h-3.5 text-[#3b7dd8]" />
            Duration
          </div>
          <p className="text-sm font-semibold font-mono text-[#e8edf5]">
            {formatSeconds(job.duration_seconds)}
          </p>
        </div>

        <div className="bg-[#111620] border border-[#1e2736] rounded-xl p-4">
          <div className="flex items-center gap-1.5 text-xs text-[#8b96a8] mb-1">
            <Maximize className="w-3.5 h-3.5 text-[#3b7dd8]" />
            Resolution
          </div>
          <p className="text-sm font-semibold font-mono text-[#e8edf5]">
            {job.width && job.height ? `${job.width} × ${job.height}` : '—'}
          </p>
        </div>

        <div className="bg-[#111620] border border-[#1e2736] rounded-xl p-4">
          <div className="flex items-center gap-1.5 text-xs text-[#8b96a8] mb-1">
            <Cpu className="w-3.5 h-3.5 text-[#3b7dd8]" />
            FPS
          </div>
          <p className="text-sm font-semibold font-mono text-[#e8edf5]">
            {job.fps ? `${job.fps} fps` : '—'}
          </p>
        </div>

        <div className="bg-[#111620] border border-[#1e2736] rounded-xl p-4">
          <div className="flex items-center gap-1.5 text-xs text-[#8b96a8] mb-1">
            <Layers className="w-3.5 h-3.5 text-[#3b7dd8]" />
            Total Frames
          </div>
          <p className="text-sm font-semibold font-mono text-[#e8edf5]">
            {job.frame_count ? job.frame_count.toLocaleString() : '—'}
          </p>
        </div>

        <div className="bg-[#111620] border border-[#1e2736] rounded-xl p-4">
          <div className="flex items-center gap-1.5 text-xs text-[#8b96a8] mb-1">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
            Sampled Frames
          </div>
          <p className="text-sm font-semibold font-mono text-[#e8edf5]">
            {job.sampled_frames}
          </p>
        </div>

        <div className="bg-[#111620] border border-[#1e2736] rounded-xl p-4">
          <div className="flex items-center gap-1.5 text-xs text-[#8b96a8] mb-1">
            <Calendar className="w-3.5 h-3.5 text-[#3b7dd8]" />
            Started At
          </div>
          <p className="text-xs font-mono text-[#e8edf5] truncate">
            {formatTimestamp(job.started_at || job.created_at)}
          </p>
        </div>
      </div>

      {/* Error Banner if Failed */}
      {job.status === 'FAILED' && (
        <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400 text-xs flex items-start gap-3">
          <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
          <div>
            <h4 className="font-semibold text-sm text-red-300 mb-0.5">Processing Failed</h4>
            <p>{job.error_message || 'OpenCV was unable to decode the video stream.'}</p>
          </div>
        </div>
      )}

      {/* Object Detection Summary Card */}
      {job.status === 'COMPLETED' && summary && (
        <DetectionSummaryCard
          summary={summary}
          totalSampledFrames={job.sampled_frames || results.length}
        />
      )}

      {/* Phase 5: Temporal Tracking Intelligence Card */}
      {job.status === 'COMPLETED' && trackingSummary && (
        <TrackingSummaryCard summary={trackingSummary} />
      )}

      {/* Phase 5: Tracked Objects Explorer */}
      {job.status === 'COMPLETED' && (
        <TrackedObjectsPanel jobId={job.id} />
      )}

      {/* Phase 6: Security Events Panel */}
      {job.status === 'COMPLETED' && (
        <SecurityEventsPanel jobId={job.id} />
      )}

      {/* Frame Gallery */}
      {job.status === 'COMPLETED' && (
        <FrameGallery results={results} />
      )}
    </div>
  );
}
