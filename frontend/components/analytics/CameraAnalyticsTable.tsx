'use client';

import { useState } from 'react';
import type { CameraAnalyticsData } from '@/types';
import { cn } from '@/lib/utils';
import { Camera, ChevronDown, ChevronUp, Info } from 'lucide-react';

interface CameraAnalyticsTableProps {
  data: CameraAnalyticsData;
  isLoading?: boolean;
}

export default function CameraAnalyticsTable({
  data,
  isLoading = false,
}: CameraAnalyticsTableProps) {
  const [expandedCameraId, setExpandedCameraId] = useState<string | null>(null);
  const [filterText, setFilterText] = useState('');

  if (isLoading) {
    return (
      <div className="h-[320px] bg-[#0d1117] border border-[#1e2736] rounded-xl p-5 animate-pulse" />
    );
  }

  const cameras = data?.cameras || [];
  const filteredCameras = cameras.filter(
    (c) =>
      c.camera_name.toLowerCase().includes(filterText.toLowerCase()) ||
      c.location.toLowerCase().includes(filterText.toLowerCase())
  );

  const getRiskBadge = (score: number, level: string) => {
    if (score >= 75) {
      return (
        <span className="px-2 py-0.5 rounded text-[11px] font-bold bg-red-500/15 border border-red-500/30 text-red-400">
          {score} · {level}
        </span>
      );
    }
    if (score >= 50) {
      return (
        <span className="px-2 py-0.5 rounded text-[11px] font-bold bg-orange-500/15 border border-orange-500/30 text-orange-400">
          {score} · {level}
        </span>
      );
    }
    if (score >= 25) {
      return (
        <span className="px-2 py-0.5 rounded text-[11px] font-bold bg-amber-500/15 border border-amber-500/30 text-amber-400">
          {score} · {level}
        </span>
      );
    }
    return (
      <span className="px-2 py-0.5 rounded text-[11px] font-bold bg-green-500/15 border border-green-500/30 text-green-400">
        {score} · {level}
      </span>
    );
  };

  return (
    <div className="bg-[#0d1117] border border-[#1e2736] rounded-xl overflow-hidden flex flex-col">
      {/* Header & Filter */}
      <div className="p-5 border-b border-[#1a2332] flex flex-wrap items-center justify-between gap-4">
        <div>
          <h3 className="text-sm font-semibold text-[#e8edf5] tracking-tight">
            Surveillance Fleet Analytics & Operational Risk Scoring
          </h3>
          <p className="text-xs text-[#8b96a8] mt-0.5">
            Deterministic risk ranking based on severity, frequency, and incident correlation
          </p>
        </div>

        <div className="flex items-center gap-3">
          <input
            type="text"
            placeholder="Filter camera or location..."
            value={filterText}
            onChange={(e) => setFilterText(e.target.value)}
            className="px-3 py-1.5 bg-[#161c28] border border-[#232f42] rounded-lg text-xs text-[#e8edf5] placeholder-[#556377] focus:outline-none focus:border-[#3b7dd8] w-56"
          />
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs text-[#8b96a8]">
          <thead className="bg-[#121824] text-[#627084] font-medium border-b border-[#1e2736]">
            <tr>
              <th className="py-3 px-4">Camera & Location</th>
              <th className="py-3 px-3">Total Events</th>
              <th className="py-3 px-3">High / Critical</th>
              <th className="py-3 px-3">Open Incidents</th>
              <th className="py-3 px-3">Velocity (Avg/Day)</th>
              <th className="py-3 px-3">Top Event Type</th>
              <th className="py-3 px-3">Operational Risk</th>
              <th className="py-3 px-4 text-right">Details</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#18202d]">
            {filteredCameras.length > 0 ? (
              filteredCameras.map((cam) => {
                const isExpanded = expandedCameraId === cam.camera_id;
                return (
                  <tr
                    key={cam.camera_id}
                    className="hover:bg-[#141b26] transition-colors group"
                  >
                    <td className="py-3.5 px-4 font-medium text-[#e8edf5]">
                      <div className="flex items-center gap-2.5">
                        <div className="p-1.5 rounded-md bg-[#182130] text-[#3b7dd8]">
                          <Camera className="w-3.5 h-3.5" />
                        </div>
                        <div>
                          <div className="font-semibold text-white">{cam.camera_name}</div>
                          <div className="text-[11px] text-[#627084]">{cam.location}</div>
                        </div>
                      </div>
                    </td>

                    <td className="py-3.5 px-3 font-semibold text-[#e8edf5]">
                      {cam.total_events}
                    </td>

                    <td className="py-3.5 px-3">
                      <span className={cn(
                        'font-medium',
                        (cam.high_severity_events + cam.critical_events) > 0 ? 'text-orange-400' : 'text-[#627084]'
                      )}>
                        {cam.high_severity_events + cam.critical_events}
                      </span>
                    </td>

                    <td className="py-3.5 px-3 font-medium">
                      {cam.incidents > 0 ? (
                        <span className="text-red-400 font-semibold">{cam.incidents} open</span>
                      ) : (
                        <span className="text-[#627084]">0</span>
                      )}
                    </td>

                    <td className="py-3.5 px-3 text-[#e8edf5]">
                      {cam.avg_events_per_day} / day
                    </td>

                    <td className="py-3.5 px-3 text-[#cbd5e1]">
                      {cam.most_common_event_type ? (
                        <span className="px-2 py-0.5 rounded bg-[#182232] text-[#93c5fd] font-medium text-[11px]">
                          {cam.most_common_event_type.replace(/_/g, ' ')}
                        </span>
                      ) : (
                        <span className="text-[#556377]">None</span>
                      )}
                    </td>

                    <td className="py-3.5 px-3">
                      {getRiskBadge(cam.risk_score, cam.risk_level)}
                    </td>

                    <td className="py-3.5 px-4 text-right">
                      <button
                        type="button"
                        onClick={() =>
                          setExpandedCameraId(isExpanded ? null : cam.camera_id)
                        }
                        className="p-1.5 rounded hover:bg-[#1f2a3c] text-[#8b96a8] hover:text-[#e8edf5] transition-colors"
                        title="View mathematical risk factors"
                      >
                        {isExpanded ? (
                          <ChevronUp className="w-4 h-4" />
                        ) : (
                          <ChevronDown className="w-4 h-4" />
                        )}
                      </button>
                    </td>
                  </tr>
                );
              })
            ) : (
              <tr>
                <td colSpan={8} className="py-8 text-center text-xs text-[#8b96a8]">
                  No cameras match your search or fleet configuration.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Expanded Risk Factors View */}
      {expandedCameraId && (
        <div className="p-4 bg-[#121824] border-t border-[#1e2736]">
          {(() => {
            const cam = cameras.find((c) => c.camera_id === expandedCameraId);
            if (!cam) return null;
            return (
              <div className="space-y-2">
                <div className="flex items-center gap-2 text-xs font-semibold text-[#e8edf5]">
                  <Info className="w-3.5 h-3.5 text-[#3b7dd8]" />
                  <span>
                    Deterministic Risk Score Formula for &apos;{cam.camera_name}&apos; ({cam.risk_score}/100):
                  </span>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2 mt-2">
                  {cam.risk_factors.map((f, i) => (
                    <div
                      key={i}
                      className="p-2.5 rounded bg-[#182130] border border-[#24334a] text-xs text-[#cbd5e1]"
                    >
                      • {f}
                    </div>
                  ))}
                </div>
              </div>
            );
          })()}
        </div>
      )}
    </div>
  );
}
