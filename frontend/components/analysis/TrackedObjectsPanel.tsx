'use client';

import React, { useEffect, useState, useMemo } from 'react';
import {
  Filter,
  Layers,
  ChevronRight,
  X,
} from 'lucide-react';
import type { TrackedObject, TrackDetail } from '@/types';
import { getTrackedObjects, getTrackDetail } from '@/services/videoAnalysis';

interface TrackedObjectsPanelProps {
  jobId: string;
  onSelectTrack?: (trackId: number) => void;
}

export default function TrackedObjectsPanel({ jobId, onSelectTrack }: TrackedObjectsPanelProps) {
  const [tracks, setTracks] = useState<TrackedObject[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedClass, setSelectedClass] = useState<string>('all');
  const [minDuration, setMinDuration] = useState<number>(0);

  // Detail drawer / modal state
  const [activeTrackDetail, setActiveTrackDetail] = useState<TrackDetail | null>(null);

  useEffect(() => {
    let isMounted = true;
    setIsLoading(true);

    getTrackedObjects(jobId)
      .then((data) => {
        if (isMounted) {
          setTracks(data);
        }
      })
      .catch(() => {
        if (isMounted) {
          setTracks([]);
        }
      })
      .finally(() => {
        if (isMounted) {
          setIsLoading(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, [jobId]);

  // Unique classes for filter pill list
  const availableClasses = useMemo(() => {
    const classes = new Set<string>();
    tracks.forEach((t) => classes.add(t.class_name));
    return Array.from(classes).sort();
  }, [tracks]);

  // Filtered tracks
  const filteredTracks = useMemo(() => {
    return tracks.filter((t) => {
      if (selectedClass !== 'all' && t.class_name.toLowerCase() !== selectedClass.toLowerCase()) {
        return false;
      }
      if (minDuration > 0 && t.duration_seconds < minDuration) {
        return false;
      }
      return true;
    });
  }, [tracks, selectedClass, minDuration]);

  const handleOpenDetail = async (trackId: number) => {
    try {
      const detail = await getTrackDetail(jobId, trackId);
      setActiveTrackDetail(detail);
      if (onSelectTrack) onSelectTrack(trackId);
    } catch {
      setActiveTrackDetail(null);
    }
  };

  if (!isLoading && tracks.length === 0) {
    return null;
  }

  return (
    <div className="bg-[#111620] border border-[#1e2736] rounded-xl overflow-hidden p-5 space-y-4">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[#1e2736] pb-4">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-[#3b7dd8]/10 border border-[#3b7dd8]/20 flex items-center justify-center text-[#3b7dd8]">
            <Layers className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-[#e8edf5]">
              Tracked Objects Explorer
            </h3>
            <p className="text-xs text-[#8b96a8]">
              Inspect continuous temporal tracks, lifecycle duration, and spatial displacement
            </p>
          </div>
        </div>

        <span className="text-xs font-mono text-[#8b96a8] bg-[#0e131d] px-2.5 py-1 rounded border border-[#1e2736] self-start sm:self-auto">
          {filteredTracks.length} of {tracks.length} tracks
        </span>
      </div>

      {/* Filter Controls Bar */}
      <div className="flex flex-wrap items-center gap-2 text-xs">
        <div className="flex items-center gap-1.5 text-[#8b96a8] mr-2">
          <Filter className="w-3.5 h-3.5" />
          <span>Class:</span>
        </div>

        <button
          type="button"
          onClick={() => setSelectedClass('all')}
          className={`px-2.5 py-1 rounded text-xs transition-colors ${
            selectedClass === 'all'
              ? 'bg-[#3b7dd8] text-white font-medium'
              : 'bg-[#0e131d] text-[#8b96a8] hover:text-[#e8edf5] border border-[#1e2736]'
          }`}
        >
          All
        </button>

        {availableClasses.map((cls) => (
          <button
            key={cls}
            type="button"
            onClick={() => setSelectedClass(cls)}
            className={`px-2.5 py-1 rounded text-xs uppercase font-mono transition-colors ${
              selectedClass === cls
                ? 'bg-[#3b7dd8] text-white font-medium'
                : 'bg-[#0e131d] text-[#8b96a8] hover:text-[#e8edf5] border border-[#1e2736]'
            }`}
          >
            {cls}
          </button>
        ))}

        <div className="ml-auto flex items-center gap-2 text-xs text-[#8b96a8]">
          <span>Min Duration:</span>
          <select
            value={minDuration}
            onChange={(e) => setMinDuration(Number(e.target.value))}
            aria-label="Filter tracks by minimum duration"
            className="bg-[#0e131d] border border-[#1e2736] rounded px-2 py-1 text-xs text-[#e8edf5] focus:outline-none focus:border-[#3b7dd8]"
          >
            <option value={0}>All Durations</option>
            <option value={2}>&gt;= 2s</option>
            <option value={4}>&gt;= 4s</option>
            <option value={6}>&gt;= 6s</option>
          </select>
        </div>
      </div>

      {/* Track List Table / Grid */}
      {isLoading ? (
        <div className="py-12 text-center text-xs text-[#8b96a8]">
          Loading tracked objects...
        </div>
      ) : filteredTracks.length === 0 ? (
        <div className="py-8 text-center text-xs text-[#4e5a6b]">
          No tracked objects match the specified filters.
        </div>
      ) : (
        <div className="overflow-x-auto border border-[#1e2736] rounded-lg">
          <table className="w-full text-left text-xs">
            <thead className="bg-[#0e131d] border-b border-[#1e2736] text-[#8b96a8] font-mono">
              <tr>
                <th className="py-2.5 px-3">Track ID</th>
                <th className="py-2.5 px-3">Class</th>
                <th className="py-2.5 px-3">First Seen</th>
                <th className="py-2.5 px-3">Last Seen</th>
                <th className="py-2.5 px-3">Duration</th>
                <th className="py-2.5 px-3">Observations</th>
                <th className="py-2.5 px-3">Avg Conf</th>
                <th className="py-2.5 px-3 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#1e2736]/60 bg-[#111620]">
              {filteredTracks.map((t) => (
                <tr
                  key={t.id}
                  className="hover:bg-[#161c28] transition-colors cursor-pointer"
                  onClick={() => handleOpenDetail(t.track_id)}
                >
                  <td className="py-2.5 px-3 font-mono font-bold text-cyan-400">
                    #{t.track_id}
                  </td>
                  <td className="py-2.5 px-3 font-semibold text-[#e8edf5] uppercase">
                    {t.class_name}
                  </td>
                  <td className="py-2.5 px-3 font-mono text-[#8b96a8]">
                    {t.first_seen_timestamp.toFixed(1)}s (F#{t.first_seen_frame})
                  </td>
                  <td className="py-2.5 px-3 font-mono text-[#8b96a8]">
                    {t.last_seen_timestamp.toFixed(1)}s (F#{t.last_seen_frame})
                  </td>
                  <td className="py-2.5 px-3 font-mono text-[#e8edf5]">
                    {t.duration_seconds.toFixed(1)}s
                  </td>
                  <td className="py-2.5 px-3 font-mono text-[#8b96a8]">
                    {t.total_frames} frames
                  </td>
                  <td className="py-2.5 px-3 font-mono text-emerald-400">
                    {Math.round(t.average_confidence * 100)}%
                  </td>
                  <td className="py-2.5 px-3 text-right">
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleOpenDetail(t.track_id);
                      }}
                      className="inline-flex items-center gap-1 text-[11px] text-[#3b7dd8] hover:text-[#5a9bf5] font-medium"
                    >
                      Trajectory
                      <ChevronRight className="w-3.5 h-3.5" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Trajectory & Detail Modal */}
      {activeTrackDetail && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
          <div className="bg-[#111620] border border-[#1e2736] rounded-xl max-w-2xl w-full max-h-[90vh] overflow-hidden flex flex-col shadow-2xl animate-in fade-in zoom-in-95 duration-150">
            {/* Modal Header */}
            <div className="p-4 border-b border-[#1e2736] flex items-center justify-between bg-[#0e131d]">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400 font-mono font-bold text-sm">
                  #{activeTrackDetail.track_id}
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-[#e8edf5] flex items-center gap-2">
                    <span className="uppercase">{activeTrackDetail.class_name}</span>
                    <span className="text-xs text-[#8b96a8] font-normal">Trajectory History</span>
                  </h3>
                  <p className="text-[11px] text-[#8b96a8] font-mono">
                    Lifetime: {activeTrackDetail.duration_seconds.toFixed(1)}s ({activeTrackDetail.first_seen_timestamp.toFixed(1)}s &rarr; {activeTrackDetail.last_seen_timestamp.toFixed(1)}s)
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setActiveTrackDetail(null)}
                className="w-8 h-8 rounded-lg bg-[#161c28] hover:bg-[#1e2736] border border-[#1e2736] text-[#8b96a8] hover:text-white flex items-center justify-center transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Metrics Row */}
            <div className="p-4 bg-[#0a0d13] border-b border-[#1e2736] grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
              <div>
                <span className="text-[#8b96a8] block text-[11px]">Net Displacement</span>
                <span className="font-mono font-bold text-cyan-400 text-sm">
                  {activeTrackDetail.displacement_pixels.toFixed(1)} px
                </span>
              </div>
              <div>
                <span className="text-[#8b96a8] block text-[11px]">Cumulative Distance</span>
                <span className="font-mono font-bold text-purple-400 text-sm">
                  {activeTrackDetail.trajectory_distance_pixels.toFixed(1)} px
                </span>
              </div>
              <div>
                <span className="text-[#8b96a8] block text-[11px]">Observations</span>
                <span className="font-mono font-bold text-[#e8edf5] text-sm">
                  {activeTrackDetail.total_frames} frames
                </span>
              </div>
              <div>
                <span className="text-[#8b96a8] block text-[11px]">Confidence Window</span>
                <span className="font-mono font-bold text-emerald-400 text-sm">
                  {Math.round(activeTrackDetail.average_confidence * 100)}% &ndash; {Math.round(activeTrackDetail.max_confidence * 100)}%
                </span>
              </div>
            </div>

            {/* Trajectory Points Table */}
            <div className="flex-1 overflow-y-auto p-4 space-y-2">
              <h4 className="text-xs font-semibold text-[#8b96a8] uppercase tracking-wider mb-2">
                Sampled Coordinate Observations ({activeTrackDetail.trajectory.length} points)
              </h4>
              <div className="border border-[#1e2736] rounded-lg overflow-hidden">
                <table className="w-full text-left text-xs">
                  <thead className="bg-[#0e131d] border-b border-[#1e2736] text-[#8b96a8] font-mono">
                    <tr>
                      <th className="py-2 px-3">Frame</th>
                      <th className="py-2 px-3">Timestamp</th>
                      <th className="py-2 px-3">Center (X, Y)</th>
                      <th className="py-2 px-3">Bounding Box (W × H)</th>
                      <th className="py-2 px-3 text-right">Confidence</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#1e2736]/40 bg-[#111620]">
                    {activeTrackDetail.trajectory.map((pt, idx) => (
                      <tr key={idx} className="font-mono hover:bg-[#161c28]">
                        <td className="py-2 px-3 text-[#e8edf5]">F#{pt.frame_index}</td>
                        <td className="py-2 px-3 text-[#8b96a8]">{pt.timestamp_seconds.toFixed(2)}s</td>
                        <td className="py-2 px-3 text-cyan-400">
                          ({pt.center_x.toFixed(1)}, {pt.center_y.toFixed(1)})
                        </td>
                        <td className="py-2 px-3 text-[#8b96a8]">
                          {pt.x2 - pt.x1} × {pt.y2 - pt.y1}
                        </td>
                        <td className="py-2 px-3 text-right text-emerald-400">
                          {Math.round(pt.confidence * 100)}%
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Modal Footer */}
            <div className="p-3 bg-[#0e131d] border-t border-[#1e2736] flex justify-end">
              <button
                type="button"
                onClick={() => setActiveTrackDetail(null)}
                className="px-4 py-1.5 rounded-lg bg-[#161c28] hover:bg-[#1e2736] border border-[#1e2736] text-xs font-medium text-[#e8edf5] transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
