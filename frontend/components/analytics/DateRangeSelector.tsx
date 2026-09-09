'use client';

import { useState } from 'react';
import { AlertCircle } from 'lucide-react';
import type { DateRangePreset } from '@/types';
import { cn } from '@/lib/utils';

interface DateRangeSelectorProps {
  preset: DateRangePreset;
  startDate?: string;
  endDate?: string;
  onPresetChange: (preset: DateRangePreset) => void;
  onCustomRangeChange: (start: string, end: string) => void;
  disabled?: boolean;
}

const PRESET_OPTIONS: { label: string; value: DateRangePreset }[] = [
  { label: 'Last 24 Hours', value: '24h' },
  { label: 'Last 7 Days', value: '7d' },
  { label: 'Last 30 Days', value: '30d' },
  { label: 'Last 90 Days', value: '90d' },
  { label: 'Custom Range', value: 'custom' },
];

export default function DateRangeSelector({
  preset,
  startDate,
  endDate,
  onPresetChange,
  onCustomRangeChange,
  disabled = false,
}: DateRangeSelectorProps) {
  const [customStart, setCustomStart] = useState<string>(
    startDate ? startDate.slice(0, 16) : ''
  );
  const [customEnd, setCustomEnd] = useState<string>(
    endDate ? endDate.slice(0, 16) : ''
  );
  const [dateError, setDateError] = useState<string | null>(null);

  const handleApplyCustom = () => {
    if (!customStart || !customEnd) {
      setDateError('Both start and end dates are required.');
      return;
    }
    const s = new Date(customStart);
    const e = new Date(customEnd);

    if (isNaN(s.getTime()) || isNaN(e.getTime())) {
      setDateError('Invalid date format.');
      return;
    }
    if (s > e) {
      setDateError('Start date cannot be after end date.');
      return;
    }
    const diffDays = (e.getTime() - s.getTime()) / (1000 * 3600 * 24);
    if (diffDays > 365) {
      setDateError('Date range cannot exceed 365 days.');
      return;
    }

    setDateError(null);
    onCustomRangeChange(s.toISOString(), e.toISOString());
  };

  return (
    <div className="flex flex-col gap-3">
      {/* Preset Pill Buttons */}
      <div className="flex flex-wrap items-center gap-1.5 p-1 bg-[#111620] border border-[#1e2736] rounded-lg">
        {PRESET_OPTIONS.map((opt) => {
          const isSelected = preset === opt.value;
          return (
            <button
              key={opt.value}
              type="button"
              disabled={disabled}
              onClick={() => {
                setDateError(null);
                onPresetChange(opt.value);
              }}
              className={cn(
                'px-3 py-1.5 rounded-md text-xs font-medium transition-all duration-150',
                isSelected
                  ? 'bg-[#3b7dd8] text-white shadow-sm'
                  : 'text-[#8b96a8] hover:text-[#e8edf5] hover:bg-[#1a2332]',
                disabled && 'opacity-50 cursor-not-allowed'
              )}
            >
              {opt.label}
            </button>
          );
        })}
      </div>

      {/* Custom Date Inputs Dropdown */}
      {preset === 'custom' && (
        <div className="flex flex-wrap items-center gap-3 p-3 bg-[#111620] border border-[#1e2736] rounded-lg">
          <div className="flex items-center gap-2">
            <span className="text-xs text-[#8b96a8] font-medium">From:</span>
            <input
              type="datetime-local"
              value={customStart}
              onChange={(e) => setCustomStart(e.target.value)}
              disabled={disabled}
              className="px-2.5 py-1.5 bg-[#161c28] border border-[#232f42] rounded text-xs text-[#e8edf5] focus:outline-none focus:border-[#3b7dd8]"
            />
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs text-[#8b96a8] font-medium">To:</span>
            <input
              type="datetime-local"
              value={customEnd}
              onChange={(e) => setCustomEnd(e.target.value)}
              disabled={disabled}
              className="px-2.5 py-1.5 bg-[#161c28] border border-[#232f42] rounded text-xs text-[#e8edf5] focus:outline-none focus:border-[#3b7dd8]"
            />
          </div>

          <button
            type="button"
            onClick={handleApplyCustom}
            disabled={disabled}
            className="px-3.5 py-1.5 bg-[#3b7dd8] hover:bg-[#2e68b8] text-white text-xs font-medium rounded transition-colors disabled:opacity-50"
          >
            Apply Range
          </button>

          {dateError && (
            <div className="flex items-center gap-1.5 text-xs text-red-400 w-full mt-1">
              <AlertCircle className="w-3.5 h-3.5 shrink-0" />
              <span>{dateError}</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
