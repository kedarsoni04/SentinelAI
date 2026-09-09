'use client';

import React, { useEffect, useState, useCallback } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import {
  ChevronLeft,
  Check,
  ExternalLink,
  Image as ImageIcon,
} from 'lucide-react';
import type { SecurityEvent, SecurityEventStatus } from '@/types';
import { getSecurityEvent, updateSecurityEventStatus } from '@/services/securityEvents';
import { getAuthenticatedFrameUrl } from '@/services/videoAnalysis';
import EventSeverityBadge from '@/components/security/EventSeverityBadge';
import EventStatusBadge from '@/components/security/EventStatusBadge';
import { Toast, useToast } from '@/components/ui/Toast';

export default function SecurityEventDetailPage() {
  const params = useParams();
  const eventId = params.id as string;

  const [event, setEvent] = useState<SecurityEvent | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isUpdating, setIsUpdating] = useState(false);

  const { toasts, showToast, dismissToast } = useToast();

  const loadEvent = useCallback(async () => {
    setIsLoading(true);
    try {
      const data = await getSecurityEvent(eventId);
      setEvent(data);
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } };
      setError(e?.response?.data?.detail || 'Unable to load security event.');
    } finally {
      setIsLoading(false);
    }
  }, [eventId]);

  useEffect(() => {
    loadEvent();
  }, [loadEvent]);

  const handleStatusChange = async (targetStatus: SecurityEventStatus) => {
    setIsUpdating(true);
    try {
      const updated = await updateSecurityEventStatus(eventId, targetStatus);
      setEvent(updated);
      showToast('success', `Event status updated to ${targetStatus}`);
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } };
      showToast('error', e?.response?.data?.detail || 'Failed to update event status');
    } finally {
      setIsUpdating(false);
    }
  };

  if (isLoading) {
    return (
      <div className="max-w-4xl mx-auto py-12 text-center text-xs text-[#8b96a8]">
        Loading security event details...
      </div>
    );
  }

  if (error || !event) {
    return (
      <div className="max-w-4xl mx-auto space-y-4">
        <Link
          href="/dashboard/events"
          className="inline-flex items-center gap-1.5 text-xs text-[#8b96a8] hover:text-[#e8edf5]"
        >
          <ChevronLeft className="w-4 h-4" />
          Back to Security Events
        </Link>
        <div className="bg-[#111620] border border-red-500/20 rounded-xl p-6 text-center space-y-2">
          <p className="text-sm font-semibold text-red-400">Security Event Not Found</p>
          <p className="text-xs text-[#8b96a8]">{error || 'Event does not exist or access denied.'}</p>
        </div>
      </div>
    );
  }

  const evidenceImageUrl = event.annotated_frame_url || event.evidence_frame_url;

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      {/* Toast notifications */}
      <Toast toasts={toasts} onDismiss={dismissToast} />


      {/* Top breadcrumb & Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <Link
          href="/dashboard/events"
          className="inline-flex items-center gap-1.5 text-xs text-[#8b96a8] hover:text-[#e8edf5] transition-colors"
        >
          <ChevronLeft className="w-4 h-4" />
          Back to Security Events
        </Link>

        {/* Workflow Status Actions */}
        <div className="flex items-center gap-2">
          {event.status === 'OPEN' && (
            <button
              type="button"
              onClick={() => handleStatusChange('ACKNOWLEDGED')}
              disabled={isUpdating}
              className="px-3 py-1.5 rounded-lg bg-amber-500/10 hover:bg-amber-500/20 border border-amber-500/30 text-amber-400 text-xs font-semibold transition-colors disabled:opacity-50"
            >
              Acknowledge Event
            </button>
          )}

          {event.status !== 'RESOLVED' && (
            <button
              type="button"
              onClick={() => handleStatusChange('RESOLVED')}
              disabled={isUpdating}
              className="px-3 py-1.5 rounded-lg bg-emerald-500/10 hover:bg-emerald-500/20 border border-emerald-500/30 text-emerald-400 text-xs font-semibold transition-colors disabled:opacity-50 flex items-center gap-1"
            >
              <Check className="w-3.5 h-3.5" />
              Resolve Event
            </button>
          )}

          {event.status !== 'DISMISSED' && (
            <button
              type="button"
              onClick={() => handleStatusChange('DISMISSED')}
              disabled={isUpdating}
              className="px-3 py-1.5 rounded-lg bg-[#161c28] hover:bg-[#1e2736] border border-[#1e2736] text-[#8b96a8] hover:text-[#e8edf5] text-xs font-medium transition-colors disabled:opacity-50"
            >
              Dismiss
            </button>
          )}
        </div>
      </div>

      {/* Primary Card */}
      <div className="bg-[#111620] border border-[#1e2736] rounded-xl p-6 space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4 border-b border-[#1e2736] pb-5">
          <div className="space-y-1.5">
            <div className="flex items-center gap-2.5">
              <EventSeverityBadge severity={event.severity} />
              <EventStatusBadge status={event.status} />
              <span className="text-xs font-mono text-[#8b96a8]">
                ID: {event.id.slice(0, 8)}…
              </span>
            </div>
            <h2 className="text-lg font-bold text-[#e8edf5]">{event.title}</h2>
            <p className="text-xs text-[#8b96a8] max-w-2xl leading-relaxed">
              {event.description}
            </p>
          </div>

          <div className="text-right sm:self-center font-mono text-xs">
            <span className="text-[#8b96a8] block text-[11px]">Timeline Point</span>
            <span className="text-cyan-400 font-bold text-base">
              {event.start_timestamp.toFixed(1)}s
            </span>
          </div>
        </div>

        {/* Timeline Visualization Bar */}
        <div className="bg-[#0a0d13] border border-[#1e2736] rounded-lg p-4 space-y-2">
          <div className="flex items-center justify-between text-xs text-[#8b96a8] font-mono">
            <span>Start: {event.start_timestamp.toFixed(1)}s</span>
            {event.end_timestamp !== null && (
              <span>End: {event.end_timestamp.toFixed(1)}s</span>
            )}
            <span>
              Duration: {event.duration_seconds !== null ? `${event.duration_seconds.toFixed(1)}s` : 'Instantaneous'}
            </span>
          </div>
          <div className="w-full bg-[#161c28] h-2 rounded-full overflow-hidden relative">
            <div className="h-full bg-gradient-to-r from-orange-400 to-red-400 rounded-full w-full" />
          </div>
        </div>

        {/* Metadata Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
          <div className="bg-[#0e131d] border border-[#1e2736] rounded-lg p-3">
            <span className="text-[#8b96a8] block text-[11px] mb-1">Subject Class</span>
            <span className="font-mono font-bold text-[#e8edf5] uppercase">
              {event.class_name || 'N/A'}
            </span>
          </div>

          <div className="bg-[#0e131d] border border-[#1e2736] rounded-lg p-3">
            <span className="text-[#8b96a8] block text-[11px] mb-1">Track Association</span>
            <span className="font-mono font-bold text-cyan-400">
              {event.track_id !== null ? `#${event.track_id}` : 'None'}
            </span>
          </div>

          <div className="bg-[#0e131d] border border-[#1e2736] rounded-lg p-3">
            <span className="text-[#8b96a8] block text-[11px] mb-1">Triggering Rule</span>
            <span className="font-medium text-[#e8edf5] truncate block">
              {event.rule_name || 'Default System Rule'}
            </span>
          </div>

          <div className="bg-[#0e131d] border border-[#1e2736] rounded-lg p-3">
            <span className="text-[#8b96a8] block text-[11px] mb-1">Analysis Job</span>
            <Link
              href={`/dashboard/analysis/${event.analysis_job_id}`}
              className="text-[#3b7dd8] hover:underline font-mono inline-flex items-center gap-1"
            >
              Job Detail
              <ExternalLink className="w-3 h-3" />
            </Link>
          </div>
        </div>

        {/* Structured Metadata Inspector if present */}
        {event.metadata_json && Object.keys(event.metadata_json).length > 0 && (
          <div className="bg-[#0e131d] border border-[#1e2736] rounded-lg p-4 space-y-2">
            <h4 className="text-xs font-semibold text-[#8b96a8] uppercase tracking-wider">
              Rule Parameters &amp; Sensor Telemetry
            </h4>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 font-mono text-xs">
              {Object.entries(event.metadata_json).map(([k, v]) => (
                <div key={k} className="bg-[#111620] p-2 rounded border border-[#1e2736]/40">
                  <span className="text-[#4e5a6b] block text-[10px] uppercase">{k.replace(/_/g, ' ')}</span>
                  <span className="text-[#e8edf5] font-semibold">
                    {typeof v === 'object' ? JSON.stringify(v) : String(v)}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Event Evidence Frame */}
        <div className="space-y-2">
          <h4 className="text-xs font-semibold text-[#8b96a8] uppercase tracking-wider flex items-center gap-1.5">
            <ImageIcon className="w-4 h-4 text-[#3b7dd8]" />
            Evidence Frame Capture
          </h4>

          {evidenceImageUrl ? (
            <div className="relative aspect-video w-full max-w-2xl bg-[#0a0d13] border border-[#1e2736] rounded-lg overflow-hidden">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={getAuthenticatedFrameUrl(evidenceImageUrl)}
                alt="Event Evidence"
                className="w-full h-full object-contain"
              />
            </div>
          ) : (
            <div className="bg-[#0e131d] border border-[#1e2736] rounded-lg p-8 text-center text-xs text-[#4e5a6b]">
              No evidence frame snapshot associated with this event.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
