'use client';

import React, { useEffect, useState, useCallback, useRef } from 'react';
import { useSearchParams } from 'next/navigation';
import {
  Play,
  Square,
  RefreshCw,
  Bell,
  Sliders,
  Shield,
  Clock,
  Activity,
  CheckCircle2,
} from 'lucide-react';
import type {
  AnalysisJob,
  ConnectionStatus,
  NotificationPreferences,
  RealtimeMessage,
  RealtimeSessionMetrics,
  RealtimeStatus,
  SecurityEvent,
  SecurityEventStatus,
} from '@/types';
import {
  getRealtimeFrameUrl,
  getRealtimeStatus,
  startRealtimeMonitoring,
  stopRealtimeMonitoring,
  RealtimeWebSocketClient,
} from '@/services/realtime';
import { getAnalysisJobs } from '@/services/videoAnalysis';
import { getJobSecurityEvents, updateSecurityEventStatus } from '@/services/securityEvents';
import { Toast, useToast } from '@/components/ui/Toast';
import MetricCard from '@/components/dashboard/MetricCard';
import LiveFramePreview from '@/components/monitoring/LiveFramePreview';
import ActiveTracksList from '@/components/monitoring/ActiveTracksList';
import LiveEventFeed from '@/components/monitoring/LiveEventFeed';

export default function RealtimeMonitoringPage() {
  const searchParams = useSearchParams();
  const initialJobId = searchParams.get('jobId') || '';

  const [jobs, setJobs] = useState<AnalysisJob[]>([]);
  const [selectedJobId, setSelectedJobId] = useState<string>(initialJobId);
  const [sessionStatus, setSessionStatus] = useState<RealtimeStatus>('STOPPED');
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>('OFFLINE');
  const [metrics, setMetrics] = useState<RealtimeSessionMetrics | null>(null);
  const [events, setEvents] = useState<SecurityEvent[]>([]);
  const [previewFrameUrl, setPreviewFrameUrl] = useState<string | null>(null);

  const [isStarting, setIsStarting] = useState(false);
  const [isStopping, setIsStopping] = useState(false);
  const [updatingEventId, setUpdatingEventId] = useState<string | null>(null);
  const [isLoadingJobs, setIsLoadingJobs] = useState(true);

  const [preferences, setPreferences] = useState<NotificationPreferences>({
    desktop_notifications: false,
    alert_sound: false,
    min_severity: 'HIGH',
  });

  const { toasts, showToast, dismissToast } = useToast();
  const wsClientRef = useRef<RealtimeWebSocketClient | null>(null);

  // Load available analysis jobs
  const loadJobs = useCallback(async () => {
    setIsLoadingJobs(true);
    try {
      const data = await getAnalysisJobs();
      setJobs(data);
      if (!selectedJobId && data.length > 0) {
        setSelectedJobId(data[0].id);
      }
    } catch {
      showToast('error', 'Unable to fetch analysis jobs.');
    } finally {
      setIsLoadingJobs(false);
    }
  }, [selectedJobId, showToast]);

  useEffect(() => {
    loadJobs();
  }, [loadJobs]);

  // Handle incoming real-time WebSocket messages
  const handleWebSocketMessage = useCallback(
    (msg: RealtimeMessage) => {
      if (msg.type === 'status_update') {
        const data = msg.data as unknown as RealtimeSessionMetrics;
        if (data.status) {
          setSessionStatus(data.status);
        }
        setMetrics(data);

        // Update preview frame if a frame index is available
        if (data.latest_frame_index !== undefined && data.latest_frame_index !== null) {
          setPreviewFrameUrl(getRealtimeFrameUrl(data.job_id || selectedJobId, data.current_timestamp));
        }
      } else if (msg.type === 'security_event') {
        const newEvent = msg.data as unknown as SecurityEvent;
        setEvents((prev) => {
          if (prev.some((e) => e.id === newEvent.id)) {
            return prev.map((e) => (e.id === newEvent.id ? newEvent : e));
          }
          return [newEvent, ...prev];
        });

        // Trigger in-app toast based on severity policy
        if (newEvent.severity === 'CRITICAL' || newEvent.severity === 'HIGH') {
          showToast('error', `[${newEvent.severity}] ${newEvent.title}`);
        }

        // Trigger native desktop notification if user opted in
        if (
          preferences.desktop_notifications &&
          typeof window !== 'undefined' &&
          'Notification' in window &&
          Notification.permission === 'granted'
        ) {
          try {
            new Notification(`SentinelAI: ${newEvent.title}`, {
              body: `${newEvent.event_type} (${newEvent.severity}) detected in active surveillance feed.`,
              icon: '/favicon.ico',
            });
          } catch {
            // Ignore notification failure
          }
        }
      } else if (msg.type === 'event_updated') {
        const updatedEvent = msg.data as unknown as SecurityEvent;
        setEvents((prev) =>
          prev.map((e) => (e.id === updatedEvent.id ? { ...e, ...updatedEvent } : e))
        );
      }
    },
    [selectedJobId, preferences.desktop_notifications, showToast]
  );

  // Synchronize state and establish WebSocket connection for selected job
  useEffect(() => {
    if (!selectedJobId) return;

    let isSubscribed = true;

    // 1. Reconcile current REST state
    const reconcileState = async () => {
      try {
        const [stat, existingEvents] = await Promise.all([
          getRealtimeStatus(selectedJobId).catch(() => null),
          getJobSecurityEvents(selectedJobId).catch(() => []),
        ]);

        if (isSubscribed) {
          if (stat) {
            setSessionStatus(stat.status);
            setMetrics(stat);
            if (stat.latest_frame_index !== undefined && stat.latest_frame_index !== null) {
              setPreviewFrameUrl(getRealtimeFrameUrl(selectedJobId, stat.current_timestamp));
            }
          }
          setEvents(existingEvents);
        }
      } catch {
        // Fallback gracefully
      }
    };

    reconcileState();

    // 2. Tear down previous WebSocket client
    if (wsClientRef.current) {
      wsClientRef.current.disconnect();
      wsClientRef.current = null;
    }

    // 3. Establish new resilient WebSocket client
    const client = new RealtimeWebSocketClient(selectedJobId, {
      onMessage: handleWebSocketMessage,
      onStatusChange: (status) => {
        if (isSubscribed) {
          setConnectionStatus(status);
        }
      },
    });

    wsClientRef.current = client;
    client.connect();

    return () => {
      isSubscribed = false;
      client.disconnect();
    };
  }, [selectedJobId, handleWebSocketMessage]);

  // Start Real-Time Monitoring Session
  const handleStartMonitoring = async () => {
    if (!selectedJobId) return;
    setIsStarting(true);
    try {
      const res = await startRealtimeMonitoring(selectedJobId);
      setSessionStatus(res.status);
      setMetrics(res);
      showToast('success', 'Real-time monitoring session initialized.');
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } };
      showToast('error', e?.response?.data?.detail || 'Failed to start monitoring session.');
    } finally {
      setIsStarting(false);
    }
  };

  // Stop Real-Time Monitoring Session
  const handleStopMonitoring = async () => {
    if (!selectedJobId) return;
    setIsStopping(true);
    try {
      const res = await stopRealtimeMonitoring(selectedJobId);
      setSessionStatus(res.status);
      setMetrics(res);
      showToast('success', 'Monitoring session stopped safely.');
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } };
      showToast('error', e?.response?.data?.detail || 'Failed to stop monitoring session.');
    } finally {
      setIsStopping(false);
    }
  };

  // Inline Triage: Update Event Status
  const handleUpdateEventStatus = async (eventId: string, newStatus: SecurityEventStatus) => {
    setUpdatingEventId(eventId);
    try {
      const updated = await updateSecurityEventStatus(eventId, newStatus);
      setEvents((prev) => prev.map((e) => (e.id === eventId ? updated : e)));
      showToast('success', `Event status transitioned to ${newStatus}`);
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } };
      showToast('error', e?.response?.data?.detail || 'Failed to update event status');
    } finally {
      setUpdatingEventId(null);
    }
  };

  // Toggle Browser Desktop Notifications
  const handleToggleDesktopNotifications = async () => {
    if (typeof window === 'undefined' || !('Notification' in window)) {
      showToast('error', 'Desktop notifications are not supported in this browser.');
      return;
    }

    if (!preferences.desktop_notifications) {
      const permission = await Notification.requestPermission();
      if (permission === 'granted') {
        setPreferences((prev) => ({ ...prev, desktop_notifications: true }));
        showToast('success', 'Desktop threat alerts enabled.');
      } else {
        showToast('error', 'Notification permission was denied.');
      }
    } else {
      setPreferences((prev) => ({ ...prev, desktop_notifications: false }));
      showToast('success', 'Desktop threat alerts disabled.');
    }
  };

  const selectedJob = jobs.find((j) => j.id === selectedJobId);
  const openEventsCount = events.filter((e) => e.status === 'OPEN').length;
  const highThreatsCount = events.filter(
    (e) => (e.severity === 'HIGH' || e.severity === 'CRITICAL') && e.status === 'OPEN'
  ).length;

  // Derived connection label and colours (Fix #1 & #7)
  const connectionLabel =
    connectionStatus === 'LIVE'
      ? 'Connected'
      : connectionStatus === 'RECONNECTING'
      ? 'Reconnecting…'
      : 'Disconnected';

  const connectionDotClass =
    connectionStatus === 'LIVE'
      ? 'bg-emerald-400'
      : connectionStatus === 'RECONNECTING'
      ? 'bg-amber-400 animate-pulse'
      : 'bg-zinc-500';

  const connectionPillClass =
    connectionStatus === 'LIVE'
      ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'
      : connectionStatus === 'RECONNECTING'
      ? 'bg-amber-500/10 border-amber-500/30 text-amber-400'
      : 'bg-zinc-800/60 border-zinc-700 text-zinc-400';

  // Format current_timestamp as HH:MM:SS (Fix #4)
  const formatVideoTime = (secs: number): string => {
    const h = Math.floor(secs / 3600);
    const m = Math.floor((secs % 3600) / 60);
    const s = Math.floor(secs % 60);
    return [h, m, s].map((v) => String(v).padStart(2, '0')).join(':');
  };

  const isSessionActive = sessionStatus === 'RUNNING' || sessionStatus === 'STARTING';

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Toast notifications */}
      <Toast toasts={toasts} onDismiss={dismissToast} />

      {/* ── Header ── */}
      <div className="flex flex-col gap-4 border-b border-[#1e2736] pb-5">
        {/* Row 1: title + connection pill */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div className="flex items-center gap-3 flex-wrap">
            <h1 className="text-xl font-semibold text-[#e8edf5]">SOC Live Operations &amp; Monitoring</h1>
            {/* Fix #1 & #7 — visible connection indicator with readable labels */}
            <div className={`flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-mono font-semibold border ${connectionPillClass}`}>
              <span className={`w-2 h-2 rounded-full ${connectionDotClass}`} />
              <span>{connectionLabel}</span>
            </div>
            {/* Fix #1 — monitoring session status badge */}
            <div className={`flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-mono font-semibold border ${
              sessionStatus === 'RUNNING'
                ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'
                : sessionStatus === 'STARTING'
                ? 'bg-blue-500/10 border-blue-500/30 text-blue-400 animate-pulse'
                : sessionStatus === 'STOPPING'
                ? 'bg-amber-500/10 border-amber-500/30 text-amber-400 animate-pulse'
                : sessionStatus === 'FAILED'
                ? 'bg-red-500/10 border-red-500/30 text-red-400'
                : sessionStatus === 'COMPLETED'
                ? 'bg-sky-500/10 border-sky-500/30 text-sky-400'
                : 'bg-zinc-800/60 border-zinc-700 text-zinc-400'
            }`}>
              <span>Monitoring: {sessionStatus}</span>
            </div>
          </div>

          {/* Bell toggle */}
          <button
            type="button"
            onClick={handleToggleDesktopNotifications}
            className={`p-2 rounded-lg border text-xs transition-colors self-start sm:self-auto ${
              preferences.desktop_notifications
                ? 'bg-[#3b7dd8]/20 border-[#3b7dd8] text-[#3b7dd8]'
                : 'bg-[#111620] border-[#1e2736] text-[#8b96a8] hover:text-[#e8edf5]'
            }`}
            title={preferences.desktop_notifications ? 'Desktop Alerts Active' : 'Enable Desktop Alerts'}
          >
            <Bell className="w-4 h-4" />
          </button>
        </div>

        {/* Row 2: Fix #2 — labelled session selector + contextual info + start/stop */}
        <div className="flex flex-col sm:flex-row sm:items-end gap-3">
          <div className="flex flex-col gap-1 flex-1 min-w-0">
            <label className="text-[10px] font-semibold text-[#4e5a6b] uppercase tracking-widest">
              Analysis Session
            </label>
            <select
              value={selectedJobId}
              onChange={(e) => setSelectedJobId(e.target.value)}
              disabled={isSessionActive || isLoadingJobs}
              className="w-full px-3 py-1.5 rounded-lg bg-[#111620] border border-[#1e2736] text-xs text-[#e8edf5] focus:outline-none focus:border-[#3b7dd8] disabled:opacity-50 truncate"
            >
              {isLoadingJobs ? (
                <option>Loading sessions…</option>
              ) : jobs.length === 0 ? (
                <option value="">No analysis sessions available</option>
              ) : (
                jobs.map((job) => (
                  <option key={job.id} value={job.id}>
                    #{job.id.slice(0, 8)} · {job.camera?.name ?? 'No Camera'} · {job.original_filename} · {job.status}
                  </option>
                ))
              )}
            </select>
            {/* Contextual session info (Fix #8) */}
            {selectedJob && (
              <p className="text-[10px] text-[#4e5a6b] truncate">
                Camera: <span className="text-[#8b96a8]">{selectedJob.camera?.name ?? '—'}</span>
                {selectedJob.camera?.location ? (
                  <>&nbsp;·&nbsp;Location: <span className="text-[#8b96a8]">{selectedJob.camera.location}</span></>
                ) : null}
                &nbsp;·&nbsp;Status: <span className="text-[#8b96a8]">{selectedJob.status}</span>
              </p>
            )}
            {!selectedJobId && !isLoadingJobs && (
              <p className="text-[10px] text-amber-400">Select a session to enable monitoring.</p>
            )}
          </div>

          {/* Start / Stop button */}
          {isSessionActive ? (
            <button
              type="button"
              disabled={isStopping}
              onClick={handleStopMonitoring}
              className="px-3.5 py-1.5 rounded-lg bg-red-600 hover:bg-red-700 text-xs font-semibold text-white flex items-center gap-1.5 transition-colors shadow-sm disabled:opacity-50 shrink-0"
            >
              <Square className="w-3.5 h-3.5 fill-current" />
              <span>{isStopping ? 'Stopping…' : 'Stop Monitoring'}</span>
            </button>
          ) : (
            <button
              type="button"
              disabled={isStarting || !selectedJobId || jobs.length === 0}
              onClick={handleStartMonitoring}
              className="px-3.5 py-1.5 rounded-lg bg-[#3b7dd8] hover:bg-[#2b6dc8] text-xs font-semibold text-white flex items-center gap-1.5 transition-colors shadow-sm disabled:opacity-50 shrink-0"
              title={!selectedJobId ? 'Select a session first' : undefined}
            >
              <Play className="w-3.5 h-3.5 fill-current" />
              <span>{isStarting ? 'Starting…' : '▶ Start Monitoring'}</span>
            </button>
          )}
        </div>
      </div>

      {/* ── KPI Telemetry Banner (Fix #3 #4) ── */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
        <MetricCard
          label="Processing FPS"
          value={metrics?.processing_fps ? `${metrics.processing_fps} FPS` : '—'}
          subtext="Real-time decode & inference"
          icon={Activity}
          iconColor="#3b7dd8"
          iconBg="rgba(59,125,216,0.1)"
        />

        {/* Fix #4 — VIDEO TIME, formatted HH:MM:SS */}
        <MetricCard
          label="Video Time"
          value={metrics?.current_timestamp !== undefined ? formatVideoTime(metrics.current_timestamp) : '00:00:00'}
          subtext="Playback position"
          icon={Clock}
          iconColor="#06b6d4"
          iconBg="rgba(6,182,212,0.1)"
        />

        <MetricCard
          label="Frames Processed"
          value={metrics?.frames_processed ?? 0}
          subtext="Inference cycles"
          icon={RefreshCw}
          iconColor="#8b5cf6"
          iconBg="rgba(139,92,246,0.1)"
        />

        {/* Fix #3 — ACTIVE TRACKS */}
        <MetricCard
          label="Active Tracks"
          value={metrics?.active_tracks ?? 0}
          subtext="ByteTrack objects in scene"
          icon={Sliders}
          iconColor="#10b981"
          iconBg="rgba(16,185,129,0.1)"
        />

        {/* Fix #3 — OPEN SECURITY EVENTS */}
        <MetricCard
          label="Open Security Events"
          value={openEventsCount}
          subtext={`${highThreatsCount} high / critical`}
          icon={Shield}
          iconColor={highThreatsCount > 0 ? '#ef4444' : '#22c55e'}
          iconBg={highThreatsCount > 0 ? 'rgba(239,68,68,0.1)' : 'rgba(34,197,94,0.1)'}
        />
      </div>

      {/* Fix #5 — Stopped / empty state banner */}
      {!isSessionActive && !selectedJobId && (
        <div className="flex flex-col items-center justify-center gap-3 rounded-xl border border-dashed border-[#1e2736] bg-[#111620] py-10 text-center">
          <Shield className="w-8 h-8 text-[#4e5a6b]" />
          <p className="text-sm font-semibold text-[#e8edf5]">NO ACTIVE MONITORING SESSION</p>
          <p className="text-xs text-[#8b96a8] max-w-xs">
            Select an active video analysis session to begin real-time security monitoring.
          </p>
        </div>
      )}

      {/* ── Main SOC Operations Console (Fix #6 #8 #9) ── */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Live Frame Preview + Active Tracks */}
        <div className="lg:col-span-7 space-y-4">
          {/* Fix #8 — monitoring context when active */}
          {isSessionActive && selectedJob && (
            <div className="flex flex-wrap gap-x-4 gap-y-1 px-3 py-2 rounded-lg bg-[#111620] border border-[#1e2736] text-[11px] text-[#8b96a8]">
              <span>Camera: <span className="text-[#e8edf5]">{selectedJob.camera?.name ?? '—'}</span></span>
              {selectedJob.camera?.location && (
                <span>Location: <span className="text-[#e8edf5]">{selectedJob.camera.location}</span></span>
              )}
              <span>Analysis: <span className="text-[#e8edf5] font-mono">#{selectedJob.id.slice(0, 8)}</span></span>
              <span>Status: <span className="text-emerald-400 font-semibold">{sessionStatus}</span></span>
            </div>
          )}

          <LiveFramePreview
            frameUrl={previewFrameUrl}
            status={sessionStatus}
            cameraName={selectedJob?.camera?.name}
            timestampSeconds={metrics?.current_timestamp || 0}
            frameIndex={metrics?.latest_frame_index}
            activeTracksCount={metrics?.active_tracks || 0}
            fps={metrics?.processing_fps || 0}
          />

          <ActiveTracksList tracks={metrics?.active_tracks_list || []} />
        </div>

        {/* Right: Live Security Events Feed + Escalation legend */}
        <div className="lg:col-span-5 space-y-4">
          {/* Fix #6 — correct feed header based on session state */}
          <div className="p-3 rounded-xl bg-[#111620] border border-[#1e2736]">
            <div className="flex items-center justify-between mb-3">
              {/* Fix #3 — LIVE SECURITY EVENTS terminology */}
              <span className="text-xs font-semibold text-[#e8edf5] uppercase tracking-wider">
                {isSessionActive
                  ? `Live Security Events · ${openEventsCount}`
                  : 'Security Events'}
              </span>
              {!isSessionActive && (
                <span className="text-[10px] text-[#4e5a6b]">No monitoring session active</span>
              )}
              {isSessionActive && (
                <span className="inline-flex items-center gap-1 text-[10px] text-emerald-400">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                  LIVE
                </span>
              )}
            </div>
            <LiveEventFeed
              events={events}
              onUpdateStatus={handleUpdateEventStatus}
              updatingEventId={updatingEventId}
            />
          </div>

          {/* Fix #9 — concise escalation copy */}
          <div className="p-3.5 rounded-xl bg-[#111620] border border-[#1e2736] text-[11px] text-[#8b96a8] space-y-2">
            <div className="flex items-center gap-1.5 font-semibold text-[#e8edf5] uppercase tracking-wider text-[10px]">
              <CheckCircle2 className="w-3.5 h-3.5 text-[#3b7dd8]" />
              Alert Escalation
            </div>
            <p className="leading-relaxed">
              High and critical security events trigger real-time operator notifications.
            </p>
            <p className="leading-relaxed">
              Operators can acknowledge or resolve events directly from the event feed.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
