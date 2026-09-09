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

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Toast notifications */}
      <Toast toasts={toasts} onDismiss={dismissToast} />

      {/* Header & Connection Status */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#1e2736] pb-5">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-xl font-semibold text-[#e8edf5]">SOC Live Operations & Monitoring</h1>

            {/* Connection Status Pill */}
            <div
              className={`flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-mono font-semibold border ${
                connectionStatus === 'LIVE'
                  ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'
                  : connectionStatus === 'RECONNECTING'
                  ? 'bg-amber-500/10 border-amber-500/30 text-amber-400 animate-pulse'
                  : 'bg-zinc-800/60 border-zinc-700 text-zinc-400'
              }`}
            >
              <span
                className={`w-2 h-2 rounded-full ${
                  connectionStatus === 'LIVE'
                    ? 'bg-emerald-400'
                    : connectionStatus === 'RECONNECTING'
                    ? 'bg-amber-400'
                    : 'bg-zinc-500'
                }`}
              />
              <span>{connectionStatus}</span>
            </div>
          </div>
          <p className="text-xs text-[#8b96a8] mt-1">
            Real-time surveillance stream telemetry, instant threat detection, and active incident response.
          </p>
        </div>

        {/* Action Controls & Session Selector */}
        <div className="flex items-center gap-2.5 flex-wrap">
          <div className="relative">
            <select
              value={selectedJobId}
              onChange={(e) => setSelectedJobId(e.target.value)}
              disabled={sessionStatus === 'RUNNING' || isLoadingJobs}
              className="px-3 py-1.5 rounded-lg bg-[#111620] border border-[#1e2736] text-xs text-[#e8edf5] focus:outline-none focus:border-[#3b7dd8] disabled:opacity-50"
            >
              {jobs.map((job) => (
                <option key={job.id} value={job.id}>
                  {job.camera?.name ? `[${job.camera.name}] ` : ''}
                  {job.original_filename} ({job.status})
                </option>
              ))}
            </select>
          </div>

          {sessionStatus === 'RUNNING' || sessionStatus === 'STARTING' ? (
            <button
              type="button"
              disabled={isStopping}
              onClick={handleStopMonitoring}
              className="px-3.5 py-1.5 rounded-lg bg-red-600 hover:bg-red-700 text-xs font-semibold text-white flex items-center gap-1.5 transition-colors shadow-sm disabled:opacity-50"
            >
              <Square className="w-3.5 h-3.5 fill-current" />
              <span>{isStopping ? 'Stopping...' : 'Stop Monitoring'}</span>
            </button>
          ) : (
            <button
              type="button"
              disabled={isStarting || !selectedJobId}
              onClick={handleStartMonitoring}
              className="px-3.5 py-1.5 rounded-lg bg-[#3b7dd8] hover:bg-[#2b6dc8] text-xs font-semibold text-white flex items-center gap-1.5 transition-colors shadow-sm disabled:opacity-50"
            >
              <Play className="w-3.5 h-3.5 fill-current" />
              <span>{isStarting ? 'Starting...' : 'Start Monitoring'}</span>
            </button>
          )}

          <button
            type="button"
            onClick={handleToggleDesktopNotifications}
            className={`p-2 rounded-lg border text-xs transition-colors ${
              preferences.desktop_notifications
                ? 'bg-[#3b7dd8]/20 border-[#3b7dd8] text-[#3b7dd8]'
                : 'bg-[#111620] border-[#1e2736] text-[#8b96a8] hover:text-[#e8edf5]'
            }`}
            title={
              preferences.desktop_notifications
                ? 'Desktop Threat Alerts Active'
                : 'Enable Desktop Threat Alerts'
            }
          >
            <Bell className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* KPI Telemetry Banner */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
        <MetricCard
          label="Processing FPS"
          value={metrics?.processing_fps ? `${metrics.processing_fps} FPS` : '—'}
          subtext="Real-time decode & inference"
          icon={Activity}
          iconColor="#3b7dd8"
          iconBg="rgba(59,125,216,0.1)"
        />

        <MetricCard
          label="Stream Timestamp"
          value={metrics?.current_timestamp !== undefined ? `${metrics.current_timestamp.toFixed(1)}s` : '0.0s'}
          subtext="Elapsed playback"
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

        <MetricCard
          label="Active Targets"
          value={metrics?.active_tracks ?? 0}
          subtext="Tracked objects in scene"
          icon={Sliders}
          iconColor="#10b981"
          iconBg="rgba(16,185,129,0.1)"
        />

        <MetricCard
          label="Open Threats"
          value={openEventsCount}
          subtext={`${highThreatsCount} high / critical`}
          icon={Shield}
          iconColor={highThreatsCount > 0 ? '#ef4444' : '#22c55e'}
          iconBg={highThreatsCount > 0 ? 'rgba(239,68,68,0.1)' : 'rgba(34,197,94,0.1)'}
        />
      </div>

      {/* Main SOC Operations Console Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Live Frame Preview & Active Tracks List */}
        <div className="lg:col-span-7 space-y-4">
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

        {/* Right Column: Live Event Stream Feed */}
        <div className="lg:col-span-5 space-y-4">
          <LiveEventFeed
            events={events}
            onUpdateStatus={handleUpdateEventStatus}
            updatingEventId={updatingEventId}
          />

          {/* Incident Response Policy Legend */}
          <div className="p-3.5 rounded-xl bg-[#111620] border border-[#1e2736] text-[11px] text-[#8b96a8] space-y-2">
            <div className="flex items-center gap-1.5 font-semibold text-[#e8edf5]">
              <CheckCircle2 className="w-3.5 h-3.5 text-[#3b7dd8]" />
              <span>SOC Escalation Protocol</span>
            </div>
            <p className="leading-relaxed">
              New threat events trigger real-time toast alerts and desktop notifications based on configured rule severities. 
              Operators can directly Acknowledge or Resolve incidents above to update threat status across all operational feeds.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
