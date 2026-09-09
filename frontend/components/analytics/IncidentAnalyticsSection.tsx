'use client';

import type { IncidentAnalyticsData } from '@/types';
import { Brain } from 'lucide-react';

interface IncidentAnalyticsSectionProps {
  data: IncidentAnalyticsData;
  isLoading?: boolean;
}

export default function IncidentAnalyticsSection({
  data,
  isLoading = false,
}: IncidentAnalyticsSectionProps) {
  if (isLoading) {
    return (
      <div className="h-[240px] bg-[#0d1117] border border-[#1e2736] rounded-xl p-5 animate-pulse" />
    );
  }

  const formatDuration = (minutes: number | null) => {
    if (minutes === null) return 'N/A';
    if (minutes < 60) return `${Math.round(minutes)}m`;
    const hours = Math.floor(minutes / 60);
    const remainingMins = Math.round(minutes % 60);
    if (hours < 24) return `${hours}h ${remainingMins}m`;
    const days = Math.floor(hours / 24);
    return `${days}d ${hours % 24}h`;
  };

  const byStatus = data?.by_status || {};
  const byRisk = data?.by_risk_level || {};

  return (
    <div className="bg-[#0d1117] border border-[#1e2736] rounded-xl p-5 flex flex-col justify-between">
      <div>
        <div className="flex items-center justify-between pb-3 border-b border-[#1a2332]">
          <div>
            <h3 className="text-sm font-semibold text-[#e8edf5] tracking-tight">
              Incident Intelligence & Resolution Analytics
            </h3>
            <p className="text-xs text-[#8b96a8] mt-0.5">
              Lifecycle status, AI risk assessments, and resolution velocity
            </p>
          </div>
          <Brain className="w-4 h-4 text-[#3b7dd8]" />
        </div>

        {/* Top metrics row */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-4">
          <div className="p-3 bg-[#121824] border border-[#1e2736] rounded-lg">
            <span className="text-[10px] uppercase font-semibold text-[#8b96a8] block">
              Total Incidents
            </span>
            <div className="text-xl font-bold text-white mt-1">
              {data?.total_incidents || 0}
            </div>
          </div>

          <div className="p-3 bg-[#121824] border border-[#1e2736] rounded-lg">
            <span className="text-[10px] uppercase font-semibold text-[#8b96a8] block">
              Resolution Rate
            </span>
            <div className="text-xl font-bold text-green-400 mt-1">
              {data?.resolution_rate || 0}%
            </div>
          </div>

          <div className="p-3 bg-[#121824] border border-[#1e2736] rounded-lg">
            <span className="text-[10px] uppercase font-semibold text-[#8b96a8] block">
              Avg Resolution Time
            </span>
            <div className="text-xl font-bold text-blue-400 mt-1">
              {formatDuration(data?.average_resolution_time_minutes)}
            </div>
          </div>

          <div className="p-3 bg-[#121824] border border-[#1e2736] rounded-lg">
            <span className="text-[10px] uppercase font-semibold text-[#8b96a8] block">
              Resolved / Closed
            </span>
            <div className="text-xl font-bold text-[#e8edf5] mt-1">
              {data?.resolved_count || 0}
            </div>
          </div>
        </div>

        {/* Statuses & Risk Levels */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4 pt-3 border-t border-[#182232]">
          {/* Status breakdown */}
          <div>
            <span className="text-xs font-semibold text-[#cbd5e1] block mb-2">
              Lifecycle Status
            </span>
            <div className="grid grid-cols-2 gap-2">
              <div className="p-2 rounded bg-[#161f2e] border border-[#233146] flex justify-between items-center text-xs">
                <span className="text-amber-400 font-medium">OPEN</span>
                <span className="font-bold text-white">{byStatus.OPEN || 0}</span>
              </div>
              <div className="p-2 rounded bg-[#161f2e] border border-[#233146] flex justify-between items-center text-xs">
                <span className="text-blue-400 font-medium">INVESTIGATING</span>
                <span className="font-bold text-white">{byStatus.INVESTIGATING || 0}</span>
              </div>
              <div className="p-2 rounded bg-[#161f2e] border border-[#233146] flex justify-between items-center text-xs">
                <span className="text-green-400 font-medium">RESOLVED</span>
                <span className="font-bold text-white">{byStatus.RESOLVED || 0}</span>
              </div>
              <div className="p-2 rounded bg-[#161f2e] border border-[#233146] flex justify-between items-center text-xs">
                <span className="text-gray-400 font-medium">CLOSED</span>
                <span className="font-bold text-white">{byStatus.CLOSED || 0}</span>
              </div>
            </div>
          </div>

          {/* AI Risk Breakdown */}
          <div>
            <span className="text-xs font-semibold text-[#cbd5e1] block mb-2">
              AI Risk Levels
            </span>
            <div className="grid grid-cols-2 gap-2">
              <div className="p-2 rounded bg-[#161f2e] border border-[#233146] flex justify-between items-center text-xs">
                <span className="text-red-400 font-medium">CRITICAL</span>
                <span className="font-bold text-white">{byRisk.CRITICAL || 0}</span>
              </div>
              <div className="p-2 rounded bg-[#161f2e] border border-[#233146] flex justify-between items-center text-xs">
                <span className="text-orange-400 font-medium">HIGH</span>
                <span className="font-bold text-white">{byRisk.HIGH || 0}</span>
              </div>
              <div className="p-2 rounded bg-[#161f2e] border border-[#233146] flex justify-between items-center text-xs">
                <span className="text-amber-400 font-medium">MEDIUM</span>
                <span className="font-bold text-white">{byRisk.MEDIUM || 0}</span>
              </div>
              <div className="p-2 rounded bg-[#161f2e] border border-[#233146] flex justify-between items-center text-xs">
                <span className="text-blue-400 font-medium">LOW</span>
                <span className="font-bold text-white">{byRisk.LOW || 0}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
