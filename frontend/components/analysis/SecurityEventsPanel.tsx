'use client';

import React, { useEffect, useState, useCallback } from 'react';
import Link from 'next/link';
import {
  Shield,
  ChevronRight,
  RefreshCw,
  Clock,
  Target,
  ExternalLink,
} from 'lucide-react';
import type { SecurityEvent } from '@/types';
import { getJobSecurityEvents } from '@/services/securityEvents';
import { getAuthenticatedFrameUrl } from '@/services/videoAnalysis';
import EventSeverityBadge from '@/components/security/EventSeverityBadge';
import EventStatusBadge from '@/components/security/EventStatusBadge';

interface Props {
  jobId: string;
}

const EVENT_TYPE_LABELS: Record<string, string> = {
  INTRUSION: 'Zone Intrusion',
  LOITERING: 'Loitering',
  STATIONARY_OBJECT: 'Stationary Object',
  CROWD_DENSITY: 'Crowd Density',
  UNUSUAL_MOVEMENT: 'Unusual Movement',
};

function EventTypeTag({ type }: { type: string }) {
  const colorMap: Record<string, string> = {
    INTRUSION: 'text-red-400 bg-red-500/10 border-red-500/30',
    LOITERING: 'text-amber-400 bg-amber-500/10 border-amber-500/30',
    STATIONARY_OBJECT: 'text-orange-400 bg-orange-500/10 border-orange-500/30',
    CROWD_DENSITY: 'text-purple-400 bg-purple-500/10 border-purple-500/30',
    UNUSUAL_MOVEMENT: 'text-cyan-400 bg-cyan-500/10 border-cyan-500/30',
  };
  return (
    <span
      className={`px-1.5 py-0.5 rounded text-[10px] font-mono font-semibold uppercase border ${
        colorMap[type] || 'text-[#8b96a8] bg-[#0e131d] border-[#1e2736]'
      }`}
    >
      {EVENT_TYPE_LABELS[type] || type}
    </span>
  );
}

export default function SecurityEventsPanel({ jobId }: Props) {
  const [events, setEvents] = useState<SecurityEvent[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const load = useCallback(async () => {
    setIsLoading(true);
    try {
      const data = await getJobSecurityEvents(jobId);
      setEvents(data);
    } catch {
      setEvents([]);
    } finally {
      setIsLoading(false);
    }
  }, [jobId]);

  useEffect(() => {
    load();
  }, [load]);

  const criticalCount = events.filter((e) => e.severity === 'CRITICAL').length;
  const highCount = events.filter((e) => e.severity === 'HIGH').length;
  const openCount = events.filter((e) => e.status === 'OPEN').length;

  return (
    <div className="bg-[#111620] border border-[#1e2736] rounded-xl overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-5 py-4 border-b border-[#1e2736]">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-red-500/10 border border-red-500/20 flex items-center justify-center">
            <Shield className="w-4 h-4 text-red-400" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-[#e8edf5]">Security Events Detected</h3>
            <p className="text-[11px] text-[#8b96a8] mt-0.5">
              Rule-based threat intelligence from this analysis run
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {events.length > 0 && (
            <div className="hidden sm:flex items-center gap-2 text-xs">
              {openCount > 0 && (
                <span className="px-2 py-0.5 rounded bg-red-500/10 border border-red-500/20 text-red-400 font-semibold">
                  {openCount} open
                </span>
              )}
              {criticalCount > 0 && (
                <span className="px-2 py-0.5 rounded bg-red-900/20 border border-red-700/30 text-red-300 font-semibold">
                  {criticalCount} critical
                </span>
              )}
              {highCount > 0 && (
                <span className="px-2 py-0.5 rounded bg-orange-500/10 border border-orange-500/20 text-orange-400 font-semibold">
                  {highCount} high
                </span>
              )}
            </div>
          )}
          <button
            type="button"
            onClick={load}
            disabled={isLoading}
            className="p-1.5 rounded-lg text-[#8b96a8] hover:text-[#e8edf5] hover:bg-[#161c28] transition-colors disabled:opacity-50"
            title="Refresh events"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Body */}
      {isLoading ? (
        <div className="px-5 py-10 text-center text-xs text-[#8b96a8]">
          Scanning for security events...
        </div>
      ) : events.length === 0 ? (
        <div className="px-5 py-10 text-center space-y-2">
          <div className="w-10 h-10 rounded-full bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center mx-auto">
            <Shield className="w-5 h-5 text-emerald-400" />
          </div>
          <p className="text-sm font-semibold text-[#e8edf5]">No Security Events Triggered</p>
          <p className="text-xs text-[#8b96a8] max-w-xs mx-auto">
            No configured security rules were triggered during this analysis run. Configure rules on the{' '}
            <Link href="/dashboard/rules" className="text-[#3b7dd8] hover:underline">
              Security Rules
            </Link>{' '}
            page to begin monitoring.
          </p>
        </div>
      ) : (
        <div className="divide-y divide-[#1e2736]/60">
          {events.map((ev) => {
            const isExpanded = expandedId === ev.id;
            const evidenceUrl = ev.annotated_frame_url || ev.evidence_frame_url;

            return (
              <div key={ev.id} className="hover:bg-[#161c28]/50 transition-colors">
                {/* Row */}
                <button
                  type="button"
                  className="w-full text-left px-5 py-3 flex items-center gap-3"
                  onClick={() => setExpandedId(isExpanded ? null : ev.id)}
                >
                  <div
                    className={`w-0.5 h-8 rounded-full shrink-0 ${
                      ev.severity === 'CRITICAL'
                        ? 'bg-red-600'
                        : ev.severity === 'HIGH'
                        ? 'bg-orange-500'
                        : ev.severity === 'MEDIUM'
                        ? 'bg-amber-500'
                        : 'bg-slate-500'
                    }`}
                  />

                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap mb-1">
                      <EventSeverityBadge severity={ev.severity} />
                      <EventTypeTag type={ev.event_type} />
                      <EventStatusBadge status={ev.status} />
                    </div>
                    <p className="text-xs font-semibold text-[#e8edf5] truncate">{ev.title}</p>
                    <div className="flex items-center gap-3 mt-0.5 text-[11px] text-[#8b96a8] font-mono">
                      <span className="flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {ev.start_timestamp.toFixed(1)}s
                        {ev.end_timestamp != null && ` → ${ev.end_timestamp.toFixed(1)}s`}
                      </span>
                      {ev.class_name && (
                        <span className="flex items-center gap-1">
                          <Target className="w-3 h-3" />
                          {ev.class_name}
                        </span>
                      )}
                      {ev.duration_seconds != null && (
                        <span>{ev.duration_seconds.toFixed(1)}s</span>
                      )}
                    </div>
                  </div>

                  <ChevronRight
                    className={`w-3.5 h-3.5 text-[#8b96a8] shrink-0 transition-transform ${
                      isExpanded ? 'rotate-90' : ''
                    }`}
                  />
                </button>

                {/* Expanded detail */}
                {isExpanded && (
                  <div className="px-5 pb-4 pt-1 space-y-4 border-t border-[#1e2736]/40 bg-[#0e131d]/50">
                    <p className="text-xs text-[#8b96a8] leading-relaxed">{ev.description}</p>

                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                      <div className="bg-[#111620] border border-[#1e2736] rounded-lg p-2.5">
                        <span className="text-[#4e5a6b] block text-[10px] uppercase mb-0.5">Track ID</span>
                        <span className="font-mono font-bold text-cyan-400">
                          {ev.track_id != null ? `#${ev.track_id}` : '—'}
                        </span>
                      </div>
                      <div className="bg-[#111620] border border-[#1e2736] rounded-lg p-2.5">
                        <span className="text-[#4e5a6b] block text-[10px] uppercase mb-0.5">Confidence</span>
                        <span className="font-mono font-bold text-[#e8edf5]">
                          {ev.confidence != null ? `${(ev.confidence * 100).toFixed(1)}%` : '—'}
                        </span>
                      </div>
                      <div className="bg-[#111620] border border-[#1e2736] rounded-lg p-2.5">
                        <span className="text-[#4e5a6b] block text-[10px] uppercase mb-0.5">Rule</span>
                        <span className="font-medium text-[#e8edf5] truncate block">
                          {ev.rule_name || 'Default'}
                        </span>
                      </div>
                      <div className="bg-[#111620] border border-[#1e2736] rounded-lg p-2.5">
                        <span className="text-[#4e5a6b] block text-[10px] uppercase mb-0.5">Subject</span>
                        <span className="font-mono font-bold text-[#e8edf5] uppercase">
                          {ev.class_name || '—'}
                        </span>
                      </div>
                    </div>

                    {ev.metadata_json && Object.keys(ev.metadata_json).length > 0 && (
                      <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 font-mono text-xs">
                        {Object.entries(ev.metadata_json).map(([k, v]) => (
                          <div key={k} className="bg-[#111620] border border-[#1e2736]/40 rounded p-2">
                            <span className="text-[#4e5a6b] block text-[10px] uppercase">
                              {k.replace(/_/g, ' ')}
                            </span>
                            <span className="text-[#e8edf5] font-semibold">
                              {typeof v === 'object' ? JSON.stringify(v) : String(v)}
                            </span>
                          </div>
                        ))}
                      </div>
                    )}

                    <div className="flex items-start gap-4">
                      {evidenceUrl && (
                        <div className="relative w-40 shrink-0 aspect-video bg-[#0a0d13] border border-[#1e2736] rounded-lg overflow-hidden">
                          {/* eslint-disable-next-line @next/next/no-img-element */}
                          <img
                            src={getAuthenticatedFrameUrl(evidenceUrl)}
                            alt="Evidence frame"
                            className="w-full h-full object-cover"
                          />
                        </div>
                      )}
                      <div className="flex flex-col gap-2 mt-1">
                        {evidenceUrl && (
                          <span className="text-[11px] text-[#8b96a8]">Evidence frame capture</span>
                        )}
                        <Link
                          href={`/dashboard/events/${ev.id}`}
                          className="inline-flex items-center gap-1 text-xs text-[#3b7dd8] hover:underline"
                        >
                          View Full Event Detail
                          <ExternalLink className="w-3 h-3" />
                        </Link>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {events.length > 0 && (
        <div className="px-5 py-3 border-t border-[#1e2736] flex items-center justify-between text-xs text-[#8b96a8]">
          <span>
            {events.length} event{events.length !== 1 ? 's' : ''} triggered
          </span>
          <Link
            href={`/dashboard/events`}
            className="flex items-center gap-1 text-[#3b7dd8] hover:underline"
          >
            View All Events
            <ExternalLink className="w-3 h-3" />
          </Link>
        </div>
      )}
    </div>
  );
}
