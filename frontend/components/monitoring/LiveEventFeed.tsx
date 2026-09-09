'use client';

import React from 'react';
import Link from 'next/link';
import {
  AlertTriangle,
  Clock,
  CheckCircle2,
  ExternalLink,
  Shield,
  Activity,
  Users,
  Compass,
} from 'lucide-react';
import type { SecurityEvent, SecurityEventStatus } from '@/types';
import EventSeverityBadge from '@/components/security/EventSeverityBadge';
import EventStatusBadge from '@/components/security/EventStatusBadge';

interface LiveEventFeedProps {
  events: SecurityEvent[];
  onUpdateStatus: (eventId: string, status: SecurityEventStatus) => Promise<void>;
  updatingEventId?: string | null;
}

export default function LiveEventFeed({
  events,
  onUpdateStatus,
  updatingEventId,
}: LiveEventFeedProps) {
  const getEventIcon = (type: string) => {
    switch (type) {
      case 'INTRUSION':
        return <AlertTriangle className="w-3.5 h-3.5 text-orange-400" />;
      case 'LOITERING':
        return <Clock className="w-3.5 h-3.5 text-amber-400" />;
      case 'CROWD_DENSITY':
        return <Users className="w-3.5 h-3.5 text-purple-400" />;
      case 'UNUSUAL_MOVEMENT':
        return <Activity className="w-3.5 h-3.5 text-cyan-400" />;
      default:
        return <Compass className="w-3.5 h-3.5 text-blue-400" />;
    }
  };

  return (
    <div className="bg-[#111620] border border-[#1e2736] rounded-xl p-4 space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-xs font-semibold text-[#8b96a8] uppercase tracking-wider flex items-center gap-1.5">
          <AlertTriangle className="w-3.5 h-3.5 text-[#3b7dd8]" />
          Live Security Events Feed ({events.length})
        </h3>
        <span className="text-[10px] text-[#4e5a6b] font-mono">Near Real-Time Stream</span>
      </div>

      {events.length === 0 ? (
        <div className="py-8 text-center space-y-2">
          <div className="w-10 h-10 rounded-full bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400 mx-auto">
            <Shield className="w-5 h-5" />
          </div>
          <p className="text-xs text-[#8b96a8]">No security events detected during this session.</p>
          <p className="text-[11px] text-[#4e5a6b]">Configured rules are continuously monitoring frames.</p>
        </div>
      ) : (
        <div className="space-y-2 max-h-[380px] overflow-y-auto pr-1">
          {events.map((ev) => {
            const isUpdating = updatingEventId === ev.id;

            return (
              <div
                key={ev.id}
                className="p-3 rounded-lg bg-[#0e131d] border border-[#1e2736] hover:border-[#3b7dd8]/40 transition-all flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs"
              >
                <div className="flex items-start gap-3 min-w-0">
                  <div className="mt-0.5 shrink-0">
                    <EventSeverityBadge severity={ev.severity} />
                  </div>

                  <div className="min-w-0">
                    <div className="flex items-center gap-1.5 flex-wrap">
                      <span className="font-semibold text-[#e8edf5] truncate">{ev.title}</span>
                      {ev.class_name && (
                        <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-[#161c28] text-[#8b96a8]">
                          {ev.class_name.toUpperCase()} {ev.track_id !== null ? `#${ev.track_id}` : ''}
                        </span>
                      )}
                    </div>

                    <div className="flex items-center gap-3 text-[11px] text-[#8b96a8] mt-1 font-mono">
                      <span className="flex items-center gap-1">
                        {getEventIcon(ev.event_type)}
                        <span>{ev.event_type}</span>
                      </span>
                      <span>{ev.start_timestamp.toFixed(1)}s</span>
                      {ev.duration_seconds !== null && ev.duration_seconds > 0 && (
                        <span>({ev.duration_seconds.toFixed(1)}s)</span>
                      )}
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-2 shrink-0 self-end sm:self-center">
                  <EventStatusBadge status={ev.status} />

                  {ev.status === 'OPEN' && (
                    <button
                      type="button"
                      disabled={isUpdating}
                      onClick={() => onUpdateStatus(ev.id, 'ACKNOWLEDGED')}
                      className="px-2 py-1 rounded bg-[#161c28] hover:bg-[#1e2736] text-[11px] font-medium text-[#e8edf5] border border-[#1e2736] transition-colors disabled:opacity-50"
                    >
                      Acknowledge
                    </button>
                  )}

                  {(ev.status === 'OPEN' || ev.status === 'ACKNOWLEDGED') && (
                    <button
                      type="button"
                      disabled={isUpdating}
                      onClick={() => onUpdateStatus(ev.id, 'RESOLVED')}
                      className="px-2 py-1 rounded bg-emerald-500/10 hover:bg-emerald-500/20 text-[11px] font-medium text-emerald-400 border border-emerald-500/30 transition-colors disabled:opacity-50 flex items-center gap-1"
                    >
                      <CheckCircle2 className="w-3 h-3" />
                      Resolve
                    </button>
                  )}

                  <Link
                    href={`/dashboard/events/${ev.id}`}
                    className="p-1 rounded text-[#4e5a6b] hover:text-[#e8edf5] hover:bg-[#161c28] transition-colors"
                    title="Inspect Incident Intelligence"
                  >
                    <ExternalLink className="w-3.5 h-3.5" />
                  </Link>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
