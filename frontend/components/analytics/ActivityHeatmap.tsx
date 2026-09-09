'use client';

import { useState, useMemo } from 'react';
import type { ActivityHeatmapData } from '@/types';
import { cn } from '@/lib/utils';
import { Flame, Moon, Calendar } from 'lucide-react';

interface ActivityHeatmapProps {
  data: ActivityHeatmapData;
  isLoading?: boolean;
}

const DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
const HOURS = Array.from({ length: 24 }, (_, i) => i);

export default function ActivityHeatmap({
  data,
  isLoading = false,
}: ActivityHeatmapProps) {
  const [hoveredCell, setHoveredCell] = useState<{
    day: number;
    day_name: string;
    hour: number;
    count: number;
  } | null>(null);

  // Matrix map for quick O(1) cell lookup: [day][hour] -> count
  const { matrix, maxCount } = useMemo(() => {
    const map: Record<string, number> = {};
    let max = 0;

    if (data?.cells) {
      data.cells.forEach((c) => {
        const key = `${c.day}-${c.hour}`;
        map[key] = c.count;
        if (c.count > max) max = c.count;
      });
    }

    return { matrix: map, maxCount: Math.max(max, 1) };
  }, [data]);

  const getCellColor = (count: number) => {
    if (count === 0) return 'bg-[#111722] hover:border-[#2a384f]';
    const ratio = count / maxCount;
    if (ratio < 0.25) return 'bg-[#1e3a5f] text-blue-200 hover:border-blue-400';
    if (ratio < 0.5) return 'bg-[#2563eb] text-white hover:border-blue-300';
    if (ratio < 0.75) return 'bg-[#38bdf8] text-gray-900 font-bold hover:border-white';
    return 'bg-[#f59e0b] text-gray-900 font-bold hover:border-white';
  };

  if (isLoading) {
    return (
      <div className="h-[340px] bg-[#0d1117] border border-[#1e2736] rounded-xl p-5 animate-pulse" />
    );
  }

  return (
    <div className="bg-[#0d1117] border border-[#1e2736] rounded-xl p-5 flex flex-col">
      {/* Header & Pattern KPIs */}
      <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-[#1a2332]">
        <div>
          <h3 className="text-sm font-semibold text-[#e8edf5] tracking-tight">
            Security Activity Matrix (Day of Week vs Hour)
          </h3>
          <p className="text-xs text-[#8b96a8] mt-0.5">
            Temporal heat density based on {data.total_events} detected events
          </p>
        </div>

        {/* Pattern Badges */}
        <div className="flex flex-wrap items-center gap-2">
          {data.peak_hour !== null && (
            <div className="flex items-center gap-1.5 px-2.5 py-1 bg-amber-500/10 border border-amber-500/30 text-amber-400 rounded-md text-xs font-medium">
              <Flame className="w-3.5 h-3.5 shrink-0" />
              <span>Peak Hour: {data.peak_hour.toString().padStart(2, '0')}:00</span>
            </div>
          )}

          {data.peak_day && (
            <div className="flex items-center gap-1.5 px-2.5 py-1 bg-blue-500/10 border border-blue-500/30 text-blue-400 rounded-md text-xs font-medium">
              <Calendar className="w-3.5 h-3.5 shrink-0" />
              <span>Peak Day: {data.peak_day}</span>
            </div>
          )}

          {data.quiet_hours && data.quiet_hours.length > 0 && (
            <div className="flex items-center gap-1.5 px-2.5 py-1 bg-indigo-500/10 border border-indigo-500/30 text-indigo-300 rounded-md text-xs font-medium">
              <Moon className="w-3.5 h-3.5 shrink-0" />
              <span>Quiet Windows: {data.quiet_hours.length} hrs</span>
            </div>
          )}
        </div>
      </div>

      {/* Matrix Table */}
      <div className="mt-4 overflow-x-auto">
        <div className="min-w-[640px]">
          {/* Hour headers */}
          <div className="grid grid-cols-[48px_repeat(24,1fr)] gap-1 mb-1">
            <div className="text-[10px] text-[#627084] font-medium text-right pr-2">
              Day
            </div>
            {HOURS.map((h) => (
              <div
                key={h}
                className="text-[10px] text-[#627084] font-medium text-center"
              >
                {h % 3 === 0 ? `${h}h` : '·'}
              </div>
            ))}
          </div>

          {/* Day rows */}
          <div className="space-y-1">
            {DAYS.map((dayName, dayIndex) => (
              <div
                key={dayName}
                className="grid grid-cols-[48px_repeat(24,1fr)] gap-1 items-center"
              >
                <div className="text-[11px] text-[#8b96a8] font-medium text-right pr-2">
                  {dayName}
                </div>

                {HOURS.map((hour) => {
                  const key = `${dayIndex}-${hour}`;
                  const count = matrix[key] || 0;
                  const isHovered =
                    hoveredCell?.day === dayIndex && hoveredCell?.hour === hour;

                  return (
                    <div
                      key={hour}
                      onMouseEnter={() =>
                        setHoveredCell({
                          day: dayIndex,
                          day_name: dayName,
                          hour,
                          count,
                        })
                      }
                      onMouseLeave={() => setHoveredCell(null)}
                      className={cn(
                        'h-6 rounded cursor-pointer transition-all border border-transparent flex items-center justify-center text-[10px]',
                        getCellColor(count),
                        isHovered && 'scale-110 z-10 shadow-lg ring-1 ring-white'
                      )}
                    >
                      {count > 0 ? (count >= 10 ? '9+' : count) : ''}
                    </div>
                  );
                })}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Legend & Hover Status */}
      <div className="mt-5 pt-3 border-t border-[#1a2332] flex flex-wrap items-center justify-between text-xs text-[#8b96a8] gap-3">
        <div className="flex items-center gap-2">
          <span>Density:</span>
          <div className="flex items-center gap-1">
            <div className="w-3.5 h-3.5 rounded bg-[#111722] border border-[#232d3d]" />
            <span className="text-[10px]">0</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-3.5 h-3.5 rounded bg-[#1e3a5f]" />
            <span className="text-[10px]">Low</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-3.5 h-3.5 rounded bg-[#2563eb]" />
            <span className="text-[10px]">Med</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-3.5 h-3.5 rounded bg-[#38bdf8]" />
            <span className="text-[10px]">High</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-3.5 h-3.5 rounded bg-[#f59e0b]" />
            <span className="text-[10px]">Peak</span>
          </div>
        </div>

        <div>
          {hoveredCell ? (
            <span className="font-medium text-[#e8edf5]">
              {hoveredCell.day_name} at {hoveredCell.hour.toString().padStart(2, '0')}:00 —{' '}
              <span className="text-[#3b7dd8]">{hoveredCell.count} events</span>
            </span>
          ) : (
            <span className="text-[#556377]">Hover over any slot to view exact count</span>
          )}
        </div>
      </div>
    </div>
  );
}
