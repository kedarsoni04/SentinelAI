'use client';

import React from 'react';
import Link from 'next/link';
import {
  AlertTriangle,
  Clock,
  Camera,
  ChevronRight,
  Shield,
  Activity,
  Users,
  Compass,
} from 'lucide-react';
import type { SecurityEvent } from '@/types';
import EventSeverityBadge from './EventSeverityBadge';
import EventStatusBadge from './EventStatusBadge';

interface EventTableProps {
  events: SecurityEvent[];
}

export default function EventTable({ events }: EventTableProps) {
  if (events.length === 0) {
    return (
      <div className="bg-[#111620] border border-[#1e2736] rounded-xl p-12 text-center space-y-3">
        <div className="w-12 h-12 rounded-full bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400 mx-auto">
          <Shield className="w-6 h-6" />
        </div>
        <h3 className="text-sm font-semibold text-[#e8edf5]">No Security Events Detected</h3>
        <p className="text-xs text-[#8b96a8] max-w-sm mx-auto">
          Your video analyses have not triggered any configured security rules.
        </p>
      </div>
    );
  }

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
      case 'STATIONARY_OBJECT':
      default:
        return <Compass className="w-3.5 h-3.5 text-blue-400" />;
    }
  };

  return (
    <div className="overflow-x-auto border border-[#1e2736] rounded-xl bg-[#111620]">
      <table className="w-full text-left text-xs">
        <thead className="bg-[#0e131d] border-b border-[#1e2736] text-[#8b96a8] font-mono">
          <tr>
            <th className="py-3 px-4">Severity</th>
            <th className="py-3 px-4">Event Type</th>
            <th className="py-3 px-4">Object / Subject</th>
            <th className="py-3 px-4">Timestamp</th>
            <th className="py-3 px-4">Duration</th>
            <th className="py-3 px-4">Camera / Source</th>
            <th className="py-3 px-4">Status</th>
            <th className="py-3 px-4 text-right">Action</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-[#1e2736]/60">
          {events.map((ev) => (
            <tr key={ev.id} className="hover:bg-[#161c28] transition-colors">
              <td className="py-3 px-4">
                <EventSeverityBadge severity={ev.severity} />
              </td>
              <td className="py-3 px-4 font-medium text-[#e8edf5]">
                <div className="flex items-center gap-1.5">
                  {getEventIcon(ev.event_type)}
                  <span>{ev.title}</span>
                </div>
              </td>
              <td className="py-3 px-4 font-mono text-[#8b96a8]">
                {ev.class_name ? (
                  <span className="text-[#e8edf5]">
                    {ev.class_name.toUpperCase()} {ev.track_id !== null ? `#${ev.track_id}` : ''}
                  </span>
                ) : (
                  '—'
                )}
              </td>
              <td className="py-3 px-4 font-mono text-cyan-400">
                {ev.start_timestamp.toFixed(1)}s
              </td>
              <td className="py-3 px-4 font-mono text-[#8b96a8]">
                {ev.duration_seconds !== null && ev.duration_seconds > 0
                  ? `${ev.duration_seconds.toFixed(1)}s`
                  : '—'}
              </td>
              <td className="py-3 px-4 text-[#8b96a8]">
                {ev.camera_name ? (
                  <div className="flex items-center gap-1">
                    <Camera className="w-3 h-3 text-[#3b7dd8]" />
                    <span>{ev.camera_name}</span>
                  </div>
                ) : (
                  <span className="font-mono text-[11px] text-[#4e5a6b]">Direct Upload</span>
                )}
              </td>
              <td className="py-3 px-4">
                <EventStatusBadge status={ev.status} />
              </td>
              <td className="py-3 px-4 text-right">
                <Link
                  href={`/dashboard/events/${ev.id}`}
                  className="inline-flex items-center gap-1 text-xs text-[#3b7dd8] hover:text-[#5a9bf5] font-medium transition-colors"
                >
                  Inspect
                  <ChevronRight className="w-3.5 h-3.5" />
                </Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
