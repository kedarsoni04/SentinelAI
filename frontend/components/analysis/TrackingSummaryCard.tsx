'use client';

import React from 'react';
import {
  Activity,
  Users,
  Car,
  Clock,
  Navigation,
  Compass,
  TrendingUp,
} from 'lucide-react';
import type { TrackingSummary } from '@/types';

interface TrackingSummaryCardProps {
  summary: TrackingSummary;
}

export default function TrackingSummaryCard({ summary }: TrackingSummaryCardProps) {
  if (summary.total_tracked_objects === 0) {
    return (
      <div className="bg-[#111620] border border-[#1e2736] rounded-xl p-5 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-blue-400">
            <Activity className="w-4 h-4" />
          </div>
          <div>
            <h4 className="text-sm font-semibold text-[#e8edf5]">
              Temporal Tracking Intelligence
            </h4>
            <p className="text-xs text-[#8b96a8]">
              No persistent multi-frame tracks identified for this video.
            </p>
          </div>
        </div>
        <span className="text-xs font-mono text-[#4e5a6b] bg-[#161c28] px-2.5 py-1 rounded border border-[#1e2736]">
          ByteTrack Active
        </span>
      </div>
    );
  }

  return (
    <div className="bg-[#111620] border border-[#1e2736] rounded-xl p-5 space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-[#1e2736] pb-3.5">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400">
            <Navigation className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-[#e8edf5]">
              Temporal Tracking &amp; Trajectory Intelligence
            </h3>
            <p className="text-xs text-[#8b96a8]">
              ByteTrack multi-object persistent association across video frames
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-[11px] font-mono px-2.5 py-1 rounded bg-[#161c28] border border-[#1e2736] text-[#8b96a8]">
            Tracker: <strong className="text-cyan-400">ByteTrack</strong>
          </span>
        </div>
      </div>

      {/* Primary KPI Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        {/* Total Tracked Objects */}
        <div className="bg-[#0e131d] border border-[#1e2736] rounded-lg p-3.5">
          <div className="flex items-center justify-between text-xs text-[#8b96a8] mb-1">
            <span>Unique Tracked Objects</span>
            <Activity className="w-3.5 h-3.5 text-cyan-400" />
          </div>
          <p className="text-xl font-bold font-mono text-[#e8edf5]">
            {summary.total_tracked_objects.toLocaleString()}
          </p>
          <span className="text-[10px] text-[#4e5a6b] font-mono">
            Isolated per analysis job
          </span>
        </div>

        {/* Tracked Persons */}
        <div className="bg-[#0e131d] border border-[#1e2736] rounded-lg p-3.5">
          <div className="flex items-center justify-between text-xs text-[#8b96a8] mb-1">
            <span>Tracked Persons</span>
            <Users className="w-3.5 h-3.5 text-blue-400" />
          </div>
          <p className="text-xl font-bold font-mono text-[#e8edf5]">
            {summary.tracked_persons.toLocaleString()}
          </p>
          <span className="text-[10px] text-[#4e5a6b] font-mono">
            {summary.total_tracked_objects > 0
              ? `${Math.round((summary.tracked_persons / summary.total_tracked_objects) * 100)}% of tracked subjects`
              : '—'}
          </span>
        </div>

        {/* Tracked Vehicles */}
        <div className="bg-[#0e131d] border border-[#1e2736] rounded-lg p-3.5">
          <div className="flex items-center justify-between text-xs text-[#8b96a8] mb-1">
            <span>Tracked Vehicles</span>
            <Car className="w-3.5 h-3.5 text-amber-400" />
          </div>
          <p className="text-xl font-bold font-mono text-[#e8edf5]">
            {summary.tracked_vehicles.toLocaleString()}
          </p>
          <span className="text-[10px] text-[#4e5a6b] font-mono">
            {summary.total_tracked_objects > 0
              ? `${Math.round((summary.tracked_vehicles / summary.total_tracked_objects) * 100)}% of tracked subjects`
              : '—'}
          </span>
        </div>

        {/* Longest Track Duration */}
        <div className="bg-[#0e131d] border border-[#1e2736] rounded-lg p-3.5">
          <div className="flex items-center justify-between text-xs text-[#8b96a8] mb-1">
            <span>Max Track Duration</span>
            <Clock className="w-3.5 h-3.5 text-purple-400" />
          </div>
          <p className="text-xl font-bold font-mono text-[#e8edf5]">
            {summary.longest_track_duration_seconds.toFixed(1)}s
          </p>
          <span className="text-[10px] text-[#4e5a6b] font-mono">
            Avg: {summary.average_track_duration_seconds.toFixed(1)}s / track
          </span>
        </div>
      </div>

      {/* Secondary Metrics Bar */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 bg-[#0a0d13] border border-[#1e2736]/60 rounded-lg p-3 text-xs">
        <div className="flex items-center gap-2">
          <TrendingUp className="w-4 h-4 text-emerald-400 shrink-0" />
          <span className="text-[#8b96a8]">Avg Observations Per Track:</span>
          <span className="font-mono font-semibold text-[#e8edf5]">
            {summary.average_observations_per_track.toFixed(1)} frames
          </span>
        </div>

        <div className="flex items-center gap-2">
          <Compass className="w-4 h-4 text-cyan-400 shrink-0" />
          <span className="text-[#8b96a8]">Predominant Class:</span>
          <span className="font-mono font-semibold text-[#e8edf5] uppercase">
            {summary.most_frequently_tracked_class || 'N/A'}
          </span>
        </div>
      </div>
    </div>
  );
}
