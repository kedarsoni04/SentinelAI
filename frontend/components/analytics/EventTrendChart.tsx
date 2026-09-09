'use client';

import { useState, useMemo } from 'react';
import type { EventTrendItem } from '@/types';
import { cn } from '@/lib/utils';
import { Calendar } from 'lucide-react';

interface EventTrendChartProps {
  data: EventTrendItem[];
  interval: string;
  totalEvents: number;
  isLoading?: boolean;
}

export default function EventTrendChart({
  data,
  interval,
  totalEvents,
  isLoading = false,
}: EventTrendChartProps) {
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null);
  const [visibleSeverities, setVisibleSeverities] = useState({
    critical: true,
    high: true,
    medium: true,
    low: true,
  });

  const toggleSeverity = (sev: 'critical' | 'high' | 'medium' | 'low') => {
    setVisibleSeverities((prev) => ({ ...prev, [sev]: !prev[sev] }));
  };

  // Dimensions
  const height = 260;
  const padding = { top: 20, right: 20, bottom: 40, left: 45 };

  // Calculate scales
  const { maxVal } = useMemo(() => {
    if (!data || data.length === 0) {
      return { maxVal: 10 };
    }

    let calculatedMax = 1;
    data.forEach((d) => {
      let sum = 0;
      if (visibleSeverities.critical) sum += d.critical;
      if (visibleSeverities.high) sum += d.high;
      if (visibleSeverities.medium) sum += d.medium;
      if (visibleSeverities.low) sum += d.low;
      if (sum > calculatedMax) calculatedMax = sum;
    });

    // Round max to comfortable nice number
    const maxVal = Math.max(Math.ceil(calculatedMax * 1.15), 5);

    return { maxVal };
  }, [data, visibleSeverities]);

  if (isLoading) {
    return (
      <div className="h-[340px] bg-[#0d1117] border border-[#1e2736] rounded-xl p-6 flex flex-col justify-center items-center">
        <div className="w-8 h-8 border-2 border-[#3b7dd8] border-t-transparent rounded-full animate-spin" />
        <p className="text-xs text-[#8b96a8] mt-3">Loading event trends...</p>
      </div>
    );
  }

  if (!data || data.length === 0 || totalEvents === 0) {
    return (
      <div className="h-[340px] bg-[#0d1117] border border-[#1e2736] rounded-xl p-6 flex flex-col justify-center items-center text-center">
        <div className="w-12 h-12 rounded-full bg-[#161c28] flex items-center justify-center text-[#4e5a6b] mb-3">
          <Calendar className="w-6 h-6" />
        </div>
        <h4 className="text-sm font-semibold text-[#e8edf5]">No Historical Event Activity</h4>
        <p className="text-xs text-[#8b96a8] mt-1 max-w-sm">
          No security events were recorded during this selected date range.
        </p>
      </div>
    );
  }

  const chartWidth = 800;
  const innerWidth = chartWidth - padding.left - padding.right;
  const innerHeight = height - padding.top - padding.bottom;

  const getX = (index: number) => {
    if (data.length <= 1) return padding.left + innerWidth / 2;
    return padding.left + (index / (data.length - 1)) * innerWidth;
  };

  const getY = (val: number) => {
    return padding.top + innerHeight - (val / maxVal) * innerHeight;
  };

  // Build SVG path for total line
  const totalLinePath = data.map((d, i) => {
    let sum = 0;
    if (visibleSeverities.critical) sum += d.critical;
    if (visibleSeverities.high) sum += d.high;
    if (visibleSeverities.medium) sum += d.medium;
    if (visibleSeverities.low) sum += d.low;
    const x = getX(i);
    const y = getY(sum);
    return `${i === 0 ? 'M' : 'L'} ${x} ${y}`;
  }).join(' ');

  const totalAreaPath = `${totalLinePath} L ${getX(data.length - 1)} ${padding.top + innerHeight} L ${getX(0)} ${padding.top + innerHeight} Z`;

  const hoveredData = hoveredIndex !== null ? data[hoveredIndex] : null;

  return (
    <div className="bg-[#0d1117] border border-[#1e2736] rounded-xl p-5 flex flex-col">
      {/* Header & Legend */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-4 border-b border-[#1a2332]">
        <div>
          <h3 className="text-sm font-semibold text-[#e8edf5] tracking-tight">
            Security Event Velocity & Trends
          </h3>
          <p className="text-xs text-[#8b96a8] mt-0.5">
            Temporal distribution bucketed by {interval} intervals ({totalEvents} total events)
          </p>
        </div>

        {/* Severity Toggle Pills */}
        <div className="flex flex-wrap items-center gap-2">
          <button
            type="button"
            onClick={() => toggleSeverity('critical')}
            className={cn(
              'px-2.5 py-1 rounded text-[11px] font-medium transition-all flex items-center gap-1.5 border',
              visibleSeverities.critical
                ? 'bg-red-500/10 border-red-500/40 text-red-400'
                : 'bg-[#161c28] border-[#243042] text-[#556377] opacity-60'
            )}
          >
            <span className="w-2 h-2 rounded-full bg-red-500" />
            Critical
          </button>
          <button
            type="button"
            onClick={() => toggleSeverity('high')}
            className={cn(
              'px-2.5 py-1 rounded text-[11px] font-medium transition-all flex items-center gap-1.5 border',
              visibleSeverities.high
                ? 'bg-orange-500/10 border-orange-500/40 text-orange-400'
                : 'bg-[#161c28] border-[#243042] text-[#556377] opacity-60'
            )}
          >
            <span className="w-2 h-2 rounded-full bg-orange-500" />
            High
          </button>
          <button
            type="button"
            onClick={() => toggleSeverity('medium')}
            className={cn(
              'px-2.5 py-1 rounded text-[11px] font-medium transition-all flex items-center gap-1.5 border',
              visibleSeverities.medium
                ? 'bg-amber-500/10 border-amber-500/40 text-amber-400'
                : 'bg-[#161c28] border-[#243042] text-[#556377] opacity-60'
            )}
          >
            <span className="w-2 h-2 rounded-full bg-amber-500" />
            Medium
          </button>
          <button
            type="button"
            onClick={() => toggleSeverity('low')}
            className={cn(
              'px-2.5 py-1 rounded text-[11px] font-medium transition-all flex items-center gap-1.5 border',
              visibleSeverities.low
                ? 'bg-blue-500/10 border-blue-500/40 text-blue-400'
                : 'bg-[#161c28] border-[#243042] text-[#556377] opacity-60'
            )}
          >
            <span className="w-2 h-2 rounded-full bg-blue-500" />
            Low
          </button>
        </div>
      </div>

      {/* SVG Canvas */}
      <div className="relative mt-4 w-full overflow-hidden">
        <svg
          viewBox={`0 0 ${chartWidth} ${height}`}
          className="w-full h-auto overflow-visible select-none"
        >
          <defs>
            <linearGradient id="trendGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#3b7dd8" stopOpacity="0.35" />
              <stop offset="100%" stopColor="#3b7dd8" stopOpacity="0.0" />
            </linearGradient>
          </defs>

          {/* Grid lines */}
          {[0, 0.25, 0.5, 0.75, 1].map((ratio) => {
            const y = padding.top + innerHeight * (1 - ratio);
            const val = Math.round(maxVal * ratio);
            return (
              <g key={ratio}>
                <line
                  x1={padding.left}
                  y1={y}
                  x2={chartWidth - padding.right}
                  y2={y}
                  stroke="#1c2536"
                  strokeDasharray="3 3"
                />
                <text
                  x={padding.left - 8}
                  y={y + 4}
                  fill="#627084"
                  fontSize="10"
                  textAnchor="end"
                >
                  {val}
                </text>
              </g>
            );
          })}

          {/* Area Fill */}
          <path d={totalAreaPath} fill="url(#trendGradient)" />

          {/* Total Line */}
          <path
            d={totalLinePath}
            fill="none"
            stroke="#3b7dd8"
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          />

          {/* Data Points */}
          {data.map((d, i) => {
            let sum = 0;
            if (visibleSeverities.critical) sum += d.critical;
            if (visibleSeverities.high) sum += d.high;
            if (visibleSeverities.medium) sum += d.medium;
            if (visibleSeverities.low) sum += d.low;

            const cx = getX(i);
            const cy = getY(sum);
            const isHovered = hoveredIndex === i;

            return (
              <g key={i} className="cursor-pointer">
                {/* Hit area */}
                <rect
                  x={cx - (innerWidth / data.length) / 2}
                  y={padding.top}
                  width={innerWidth / data.length}
                  height={innerHeight}
                  fill="transparent"
                  onMouseEnter={() => setHoveredIndex(i)}
                  onMouseLeave={() => setHoveredIndex(null)}
                />

                {isHovered && (
                  <line
                    x1={cx}
                    y1={padding.top}
                    x2={cx}
                    y2={padding.top + innerHeight}
                    stroke="#3b7dd8"
                    strokeWidth="1.5"
                    strokeDasharray="2 2"
                  />
                )}

                {(sum > 0 || isHovered) && (
                  <circle
                    cx={cx}
                    cy={cy}
                    r={isHovered ? 5 : 3}
                    fill={isHovered ? '#60a5fa' : '#3b7dd8'}
                    stroke="#0d1117"
                    strokeWidth="1.5"
                  />
                )}
              </g>
            );
          })}

          {/* X Axis Labels */}
          {data.map((d, i) => {
            // Show every nth label to avoid crowding
            const step = Math.max(1, Math.floor(data.length / 8));
            if (i % step !== 0 && i !== data.length - 1) return null;
            const x = getX(i);
            return (
              <text
                key={i}
                x={x}
                y={height - 15}
                fill="#627084"
                fontSize="10"
                textAnchor="middle"
              >
                {d.label}
              </text>
            );
          })}
        </svg>

        {/* Floating Tooltip */}
        {hoveredData && hoveredIndex !== null && (
          <div
            className="absolute z-20 pointer-events-none bg-[#161c28] border border-[#2d3b52] rounded-lg p-2.5 shadow-xl text-xs w-44"
            style={{
              left: `${(hoveredIndex / (data.length - 1 || 1)) * 80 + 5}%`,
              top: '10px',
            }}
          >
            <div className="font-semibold text-[#e8edf5] border-b border-[#243042] pb-1 mb-1.5 flex justify-between">
              <span>{hoveredData.label}</span>
              <span className="text-[#3b7dd8]">{hoveredData.total} events</span>
            </div>
            <div className="space-y-1 text-[11px]">
              <div className="flex justify-between text-red-400">
                <span>Critical:</span>
                <span className="font-medium">{hoveredData.critical}</span>
              </div>
              <div className="flex justify-between text-orange-400">
                <span>High:</span>
                <span className="font-medium">{hoveredData.high}</span>
              </div>
              <div className="flex justify-between text-amber-400">
                <span>Medium:</span>
                <span className="font-medium">{hoveredData.medium}</span>
              </div>
              <div className="flex justify-between text-blue-400">
                <span>Low:</span>
                <span className="font-medium">{hoveredData.low}</span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
