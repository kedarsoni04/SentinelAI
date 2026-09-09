'use client';

import { useCallback, useEffect, useState, useRef } from 'react';
import { Film, Plus, RefreshCw } from 'lucide-react';
import type { AnalysisJob } from '@/types';
import { getAnalysisJobs, cancelAnalysis } from '@/services/videoAnalysis';
import { extractErrorMessage } from '@/services/auth';
import VideoUploadZone from '@/components/analysis/VideoUploadZone';
import ProcessingProgressCard from '@/components/analysis/ProcessingProgressCard';
import AnalysisJobList from '@/components/analysis/AnalysisJobList';
import { Toast, useToast } from '@/components/ui/Toast';

export default function VideoAnalysisPage() {
  const [jobs, setJobs] = useState<AnalysisJob[]>([]);
  const [activeTab, setActiveTab] = useState<'upload' | 'history'>('upload');

  const { toasts, showToast, dismissToast } = useToast();

  const pollTimerRef = useRef<NodeJS.Timeout | null>(null);

  const fetchJobs = useCallback(async () => {
    try {
      const data = await getAnalysisJobs();
      setJobs(data);
    } catch {
      // Background poll failure is non-fatal
    }
  }, []);

  useEffect(() => {
    fetchJobs();
  }, [fetchJobs]);

  // Dynamic Polling: poll every 2.5s if any job is QUEUED or PROCESSING
  useEffect(() => {
    const hasActiveJob = jobs.some(
      (j) => j.status === 'QUEUED' || j.status === 'PROCESSING'
    );

    if (hasActiveJob) {
      pollTimerRef.current = setTimeout(() => {
        fetchJobs();
      }, 2500);
    }

    return () => {
      if (pollTimerRef.current) {
        clearTimeout(pollTimerRef.current);
      }
    };
  }, [jobs, fetchJobs]);

  const handleUploadSuccess = (jobId: string, filename: string) => {
    showToast('success', `Video '${filename}' uploaded. Analysis started in background.`);
    fetchJobs();
  };

  const handleCancelJob = async (jobId: string) => {
    try {
      await cancelAnalysis(jobId);
      showToast('success', 'Analysis job cancelled.');
      fetchJobs();
    } catch (err: unknown) {
      showToast('error', extractErrorMessage(err));
    }
  };

  const activeJob = jobs.find(
    (j) => j.status === 'PROCESSING' || j.status === 'QUEUED'
  );

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Toast Alert Stack */}
      <Toast toasts={toasts} onDismiss={dismissToast} />

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-semibold text-[#e8edf5]">Video Analysis</h1>
          <p className="text-sm text-[#8b96a8] mt-0.5">
            Analyze surveillance footage using SentinelAI&apos;s computer vision pipeline.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => fetchJobs()}
            className="px-3 py-1.5 text-xs font-medium text-[#8b96a8] hover:text-[#e8edf5] bg-[#111620] hover:bg-[#161c28] border border-[#1e2736] rounded-lg flex items-center gap-1.5 transition-colors"
            title="Refresh jobs list"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            Refresh
          </button>
        </div>
      </div>

      {/* Active Processing Card Banner */}
      {activeJob && (
        <div className="space-y-2">
          <h2 className="text-xs font-semibold text-[#4e5a6b] uppercase tracking-wider">
            Active Processing Job
          </h2>
          <ProcessingProgressCard job={activeJob} onCancel={handleCancelJob} />
        </div>
      )}

      {/* Tabs */}
      <div className="flex items-center gap-2 border-b border-[#1e2736] pb-2">
        <button
          type="button"
          onClick={() => setActiveTab('upload')}
          className={`px-4 py-2 text-xs font-medium rounded-lg transition-colors flex items-center gap-1.5 ${
            activeTab === 'upload'
              ? 'bg-[#3b7dd8]/10 text-[#3b7dd8] border border-[#3b7dd8]/20'
              : 'text-[#8b96a8] hover:text-[#e8edf5] hover:bg-[#161c28]'
          }`}
        >
          <Plus className="w-3.5 h-3.5" />
          Upload Surveillance Video
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('history')}
          className={`px-4 py-2 text-xs font-medium rounded-lg transition-colors flex items-center gap-1.5 ${
            activeTab === 'history'
              ? 'bg-[#3b7dd8]/10 text-[#3b7dd8] border border-[#3b7dd8]/20'
              : 'text-[#8b96a8] hover:text-[#e8edf5] hover:bg-[#161c28]'
          }`}
        >
          <Film className="w-3.5 h-3.5" />
          Analysis History ({jobs.length})
        </button>
      </div>

      {/* Content depending on tab */}
      {activeTab === 'upload' ? (
        <div className="space-y-6">
          <VideoUploadZone
            onUploadSuccess={handleUploadSuccess}
            isProcessing={!!activeJob}
          />

          <div className="pt-2">
            <h2 className="text-xs font-semibold text-[#4e5a6b] uppercase tracking-wider mb-3">
              Recent Video Analyses
            </h2>
            <AnalysisJobList jobs={jobs.slice(0, 5)} onCancel={handleCancelJob} />
          </div>
        </div>
      ) : (
        <AnalysisJobList jobs={jobs} onCancel={handleCancelJob} />
      )}
    </div>
  );
}
