'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import {
  Camera,
  Film,
  AlertTriangle,
  ShieldCheck,
  Activity,
  Circle,
  ArrowRight,
  Target,
  BarChart2,
} from 'lucide-react';
import MetricCard from '@/components/dashboard/MetricCard';
import { useAuth } from '@/hooks/useAuth';
import { checkHealth } from '@/services/auth';
import { getCameras } from '@/services/cameras';
import {
  getActiveJobsCount,
  getAnalysisJobs,
  getDetectionSummary,
} from '@/services/videoAnalysis';
import { getEventMetrics, getSecurityEvents } from '@/services/securityEvents';
import type {
  ActiveJobsCount,
  AnalysisJob,
  DetectionSummary,
  EventMetrics,
  SecurityEvent,
} from '@/types';
import JobStatusBadge from '@/components/analysis/JobStatusBadge';
import EventTable from '@/components/security/EventTable';

type ApiStatus = 'checking' | 'online' | 'offline';

export default function DashboardPage() {
  const { user } = useAuth();
  const [apiStatus, setApiStatus] = useState<ApiStatus>('checking');
  const [enabledCameraCount, setEnabledCameraCount] = useState<number>(0);
  const [totalCameraCount, setTotalCameraCount] = useState<number>(0);
  const [cameraLoaded, setCameraLoaded] = useState(false);

  // Analysis stats
  const [activeJobs, setActiveJobs] = useState<ActiveJobsCount>({
    active_jobs: 0,
    queued: 0,
    processing: 0,
  });
  const [recentJobs, setRecentJobs] = useState<AnalysisJob[]>([]);
  const [recentDetectionsCount, setRecentDetectionsCount] = useState<number>(0);
  const [analysisLoaded, setAnalysisLoaded] = useState(false);

  // Phase 6: Security Events & Metrics
  const [eventMetrics, setEventMetrics] = useState<EventMetrics>({
    total_events: 0,
    open_events: 0,
    high_severity_events: 0,
    medium_severity_events: 0,
    low_severity_events: 0,
    events_today: 0,
    by_type: {},
  });
  const [recentEvents, setRecentEvents] = useState<SecurityEvent[]>([]);

  useEffect(() => {
    const verifyApi = async () => {
      try {
        await checkHealth();
        setApiStatus('online');
      } catch {
        setApiStatus('offline');
      }
    };
    verifyApi();
  }, []);

  useEffect(() => {
    const loadCameraStats = async () => {
      try {
        const cameras = await getCameras();
        setTotalCameraCount(cameras.length);
        setEnabledCameraCount(cameras.filter((c) => c.is_enabled).length);
      } catch {
        // Non-critical — dashboard still works if camera fetch fails
      } finally {
        setCameraLoaded(true);
      }
    };
    loadCameraStats();
  }, []);

  useEffect(() => {
    const loadAnalysisStats = async () => {
      try {
        const [counts, jobs] = await Promise.all([
          getActiveJobsCount(),
          getAnalysisJobs(),
        ]);
        setActiveJobs(counts);
        setRecentJobs(jobs.slice(0, 3));

        // Aggregate detections across recent completed jobs
        const completed = jobs.filter((j) => j.status === 'COMPLETED');
        if (completed.length > 0) {
          const summaries = await Promise.all(
            completed.slice(0, 5).map((j) => getDetectionSummary(j.id).catch(() => null))
          );
          const total = summaries.reduce(
            (acc: number, s: DetectionSummary | null) => acc + (s?.total_detections || 0),
            0
          );
          setRecentDetectionsCount(total);
        }
      } catch {
        // Non-critical
      } finally {
        setAnalysisLoaded(true);
      }
    };
    loadAnalysisStats();
  }, []);

  useEffect(() => {
    const loadEventStats = async () => {
      try {
        const [metricsData, eventsData] = await Promise.all([
          getEventMetrics(),
          getSecurityEvents({ limit: 5 }),
        ]);
        setEventMetrics(metricsData);
        setRecentEvents(eventsData);
      } catch {
        // Non-critical
      }
    };
    loadEventStats();
  }, []);

  const metrics = [
    {
      label: 'Open Security Events',
      value: eventMetrics.open_events,
      subtext: `${eventMetrics.high_severity_events} High Priority / ${eventMetrics.events_today} Today`,
      icon: AlertTriangle,
      iconColor: eventMetrics.open_events > 0 ? '#ef4444' : '#22c55e',
      iconBg: eventMetrics.open_events > 0 ? 'rgba(239,68,68,0.1)' : 'rgba(34,197,94,0.1)',
    },
    {
      label: 'Active Cameras',
      value: cameraLoaded ? enabledCameraCount : '—',
      subtext: !cameraLoaded
        ? 'Loading…'
        : totalCameraCount === 0
        ? 'No surveillance cameras configured yet'
        : `${enabledCameraCount} of ${totalCameraCount} cameras enabled`,
      icon: Camera,
      iconColor: '#3b7dd8',
      iconBg: 'rgba(59,125,216,0.1)',
    },
    {
      label: 'Processing Jobs',
      value: analysisLoaded ? activeJobs.active_jobs : '—',
      subtext: !analysisLoaded
        ? 'Loading…'
        : activeJobs.active_jobs === 0
        ? 'Vision pipeline idle'
        : `${activeJobs.processing} processing, ${activeJobs.queued} queued`,
      icon: Film,
      iconColor: '#f59e0b',
      iconBg: 'rgba(245,158,11,0.1)',
    },
    {
      label: 'Recent Detections',
      value: analysisLoaded ? recentDetectionsCount : '—',
      subtext: 'From completed video analyses',
      icon: Target,
      iconColor: '#06b6d4',
      iconBg: 'rgba(6,182,212,0.1)',
    },
  ];

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Page Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-xl font-semibold text-[#e8edf5]">Security Overview</h1>
          <p className="text-sm text-[#8b96a8] mt-1">
            Welcome back, {user?.name?.split(' ')[0] || 'Operator'}.{' '}
            <span className="text-[#4e5a6b]">
              Platform initialized and operational.
            </span>
          </p>
        </div>

        {/* API Status indicator */}
        <div className="flex items-center gap-2 px-3 py-1.5 bg-[#111620] border border-[#1e2736] rounded-lg">
          <Circle
            className={`w-2 h-2 fill-current ${
              apiStatus === 'checking'
                ? 'text-[#f59e0b]'
                : apiStatus === 'online'
                ? 'text-[#22c55e]'
                : 'text-[#ef4444]'
            }`}
          />
          <span className="text-xs text-[#8b96a8]">
            API{' '}
            {apiStatus === 'checking'
              ? 'Connecting…'
              : apiStatus === 'online'
              ? 'Online'
              : 'Offline'}
          </span>
        </div>
      </div>

      {/* API offline warning */}
      {apiStatus === 'offline' && (
        <div className="flex items-start gap-3 bg-[rgba(245,158,11,0.06)] border border-[rgba(245,158,11,0.2)] rounded-xl px-4 py-3">
          <AlertTriangle className="w-4 h-4 text-[#f59e0b] mt-0.5 shrink-0" />
          <div>
            <p className="text-sm font-medium text-[#f59e0b]">API Connection Issue</p>
            <p className="text-xs text-[#8b96a8] mt-0.5">
              Unable to connect to SentinelAI services. Verify the backend is running at{' '}
              <code className="text-[#3b7dd8] font-mono">
                {process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}
              </code>
            </p>
          </div>
        </div>
      )}

      {/* Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        {metrics.map((metric) => (
          <MetricCard key={metric.label} {...metric} />
        ))}
      </div>

      {/* System Status & Platform Panels */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* System Status */}
        <div className="lg:col-span-2 bg-[#111620] border border-[#1e2736] rounded-xl p-5">
          <div className="flex items-center gap-2 mb-4">
            <Activity className="w-4 h-4 text-[#3b7dd8]" />
            <h2 className="text-sm font-semibold text-[#e8edf5]">System Status</h2>
          </div>

          <div className="space-y-3">
            {[
              { label: 'Authentication Service', status: 'operational' },
              { label: 'Database Connection', status: 'operational' },
              { label: 'Camera Management', status: 'operational' },
              { label: 'OpenCV Video Analysis Pipeline', status: 'operational' },
              {
                label: 'API Gateway',
                status:
                  apiStatus === 'online'
                    ? 'operational'
                    : apiStatus === 'offline'
                    ? 'degraded'
                    : 'checking',
              },
              { label: 'YOLOv11 Object Detection Engine', status: 'operational' },
              { label: 'Threat Classification Engine', status: 'not_configured' },
              { label: 'Incident Management', status: 'not_configured' },
            ].map((item) => (
              <div
                key={item.label}
                className="flex items-center justify-between py-2.5 border-b border-[#1a2030] last:border-0"
              >
                <span className="text-sm text-[#8b96a8]">{item.label}</span>
                <StatusBadge status={item.status} />
              </div>
            ))}
          </div>
        </div>

        {/* Platform Info */}
        <div className="bg-[#111620] border border-[#1e2736] rounded-xl p-5">
          <div className="flex items-center gap-2 mb-4">
            <ShieldCheck className="w-4 h-4 text-[#3b7dd8]" />
            <h2 className="text-sm font-semibold text-[#e8edf5]">Platform</h2>
          </div>

          <div className="space-y-3">
            {[
              { label: 'Version', value: '0.4.0 — Phase 4' },
              { label: 'Role', value: user?.role?.replace('_', ' ') || '—' },
              {
                label: 'Cameras',
                value: cameraLoaded ? `${totalCameraCount} configured` : '…',
              },
              {
                label: 'Analysis Jobs',
                value: analysisLoaded ? `${recentJobs.length} logged` : '…',
              },
              { label: 'Backend', value: 'FastAPI + OpenCV + YOLOv11' },
              { label: 'AI Model', value: 'YOLOv11n (CPU)' },
              { label: 'Auth', value: 'JWT / bcrypt' },
              { label: 'Database', value: 'SQLite (dev)' },
            ].map((item) => (
              <div
                key={item.label}
                className="flex items-start justify-between py-2 border-b border-[#1a2030] last:border-0 gap-3"
              >
                <span className="text-xs text-[#4e5a6b] shrink-0">{item.label}</span>
                <span className="text-xs text-[#8b96a8] text-right truncate">
                  {item.value}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Recent Video Analysis Preview */}
      <div className="bg-[#111620] border border-[#1e2736] rounded-xl p-5 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Film className="w-4 h-4 text-[#3b7dd8]" />
            <h2 className="text-sm font-semibold text-[#e8edf5]">Recent Video Analysis</h2>
          </div>
          <Link
            href="/dashboard/analysis"
            className="text-xs text-[#3b7dd8] hover:text-[#4d8fe8] flex items-center gap-1 font-medium transition-colors"
          >
            All Analyses
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        {recentJobs.length === 0 ? (
          <p className="text-xs text-[#4e5a6b] py-2">
            No video footage analyzed yet. Upload surveillance video in the{' '}
            <Link href="/dashboard/analysis" className="text-[#3b7dd8] hover:underline">
              Analysis section
            </Link>
            .
          </p>
        ) : (
          <div className="divide-y divide-[#1a2030]">
            {recentJobs.map((j) => (
              <div
                key={j.id}
                className="py-2.5 flex items-center justify-between text-xs gap-3"
              >
                <div className="flex items-center gap-2 min-w-0">
                  <span className="text-[#e8edf5] font-medium truncate">
                    {j.original_filename}
                  </span>
                  <JobStatusBadge status={j.status} />
                </div>
                <div className="flex items-center gap-3 text-[#4e5a6b] font-mono shrink-0">
                  <span>{j.progress}%</span>
                  <span>·</span>
                  <span>{j.sampled_frames} frames</span>
                  <Link
                    href={`/dashboard/analysis/${j.id}`}
                    className="text-[#3b7dd8] hover:underline ml-1"
                  >
                    View
                  </Link>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Recent Security Events Section */}
      <div className="bg-[#111620] border border-[#1e2736] rounded-xl p-5 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-orange-400" />
            <h2 className="text-sm font-semibold text-[#e8edf5]">Recent Security Events</h2>
          </div>
          <Link
            href="/dashboard/events"
            className="text-xs text-[#3b7dd8] hover:text-[#4d8fe8] flex items-center gap-1 font-medium transition-colors"
          >
            All Events ({eventMetrics.total_events})
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        <EventTable events={recentEvents} />
      </div>

      {/* Phase 9 Analytics & Anomaly Intelligence Snapshot */}
      <div className="bg-[#111620] border border-[#1e2736] rounded-xl p-5">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 pb-3 border-b border-[#1c2636]">
          <div className="flex items-center gap-2">
            <div className="p-1.5 rounded-md bg-[rgba(59,125,216,0.12)] text-[#3b7dd8]">
              <BarChart2 className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-sm font-semibold text-[#e8edf5]">Operational Intelligence & Analytics</h2>
              <p className="text-xs text-[#8b96a8]">Historical surveillance trends, fleet risk scoring, and rule-based anomaly intelligence</p>
            </div>
          </div>
          <Link
            href="/dashboard/analytics"
            className="text-xs text-[#3b7dd8] hover:text-[#4d8fe8] flex items-center gap-1 font-medium transition-colors"
          >
            Launch Analytics Workspace
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-3.5">
          <div className="p-2.5 rounded bg-[#161f2e] border border-[#233146]">
            <span className="text-[10px] text-[#8b96a8] uppercase font-semibold block">Total Events Logged</span>
            <span className="text-lg font-bold text-white mt-0.5 block">{eventMetrics.total_events}</span>
          </div>
          <div className="p-2.5 rounded bg-[#161f2e] border border-[#233146]">
            <span className="text-[10px] text-[#8b96a8] uppercase font-semibold block">Events Today</span>
            <span className="text-lg font-bold text-[#3b7dd8] mt-0.5 block">{eventMetrics.events_today}</span>
          </div>
          <div className="p-2.5 rounded bg-[#161f2e] border border-[#233146]">
            <span className="text-[10px] text-[#8b96a8] uppercase font-semibold block">High Severity</span>
            <span className="text-lg font-bold text-orange-400 mt-0.5 block">{eventMetrics.high_severity_events}</span>
          </div>
          <div className="p-2.5 rounded bg-[#161f2e] border border-[#233146]">
            <span className="text-[10px] text-[#8b96a8] uppercase font-semibold block">Active Surveillance</span>
            <span className="text-lg font-bold text-green-400 mt-0.5 block">{enabledCameraCount} online</span>
          </div>
        </div>
      </div>

      {/* Phase roadmap note */}
      <div className="bg-[#111620] border border-[#1e2736] rounded-xl px-5 py-4">
        <p className="text-xs text-[#4e5a6b] leading-relaxed">
          <span className="text-[#8b96a8] font-medium">
            Phase 9 — Advanced Analytics &amp; Anomaly Intelligence Active.
          </span>{' '}
          Historical surveillance analytics, time-based pattern heatmaps, deterministic fleet risk scoring,
          and explainable rule-based anomaly detection are fully operational.
        </p>
      </div>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const configs: Record<
    string,
    { label: string; dotColor: string; textColor: string }
  > = {
    operational: { label: 'Operational', dotColor: '#22c55e', textColor: '#22c55e' },
    degraded: { label: 'Degraded', dotColor: '#f59e0b', textColor: '#f59e0b' },
    checking: { label: 'Checking…', dotColor: '#f59e0b', textColor: '#4e5a6b' },
    not_configured: {
      label: 'Not Configured',
      dotColor: '#4e5a6b',
      textColor: '#4e5a6b',
    },
  };

  const config = configs[status] || configs.not_configured;

  return (
    <div className="flex items-center gap-1.5">
      <Circle
        className="w-1.5 h-1.5 fill-current shrink-0"
        style={{ color: config.dotColor }}
      />
      <span className="text-xs font-medium" style={{ color: config.textColor }}>
        {config.label}
      </span>
    </div>
  );
}
