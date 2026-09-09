'use client';

import type { AnomalyDetectionData } from '@/types';
import { AlertTriangle, CheckCircle2, HelpCircle } from 'lucide-react';

interface AnomaliesPanelProps {
  data: AnomalyDetectionData;
  isLoading?: boolean;
}

export default function AnomaliesPanel({
  data,
  isLoading = false,
}: AnomaliesPanelProps) {
  if (isLoading) {
    return (
      <div className="h-[260px] bg-[#0d1117] border border-[#1e2736] rounded-xl p-5 animate-pulse" />
    );
  }

  const getSeverityBadge = (sev: string) => {
    switch (sev) {
      case 'HIGH':
        return (
          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-red-500/15 border border-red-500/30 text-red-400">
            HIGH PRIORITY
          </span>
        );
      case 'MEDIUM':
        return (
          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-500/15 border border-amber-500/30 text-amber-400">
            MEDIUM PRIORITY
          </span>
        );
      case 'LOW':
        return (
          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-blue-500/15 border border-blue-500/30 text-blue-400">
            LOW PRIORITY
          </span>
        );
      default:
        return (
          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-gray-500/15 border border-gray-500/30 text-gray-400">
            INFO
          </span>
        );
    }
  };

  return (
    <div className="bg-[#0d1117] border border-[#1e2736] rounded-xl p-5 flex flex-col">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between pb-4 border-b border-[#1a2332] gap-3">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-sm font-semibold text-[#e8edf5] tracking-tight">
              Rule-Based Anomaly Intelligence
            </h3>
            <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-[#162030] text-[#70a4ea] border border-[#23334c]">
              Deterministic
            </span>
          </div>
          <p className="text-xs text-[#8b96a8] mt-0.5">
            Statistical deviations from historical baseline rates (volume, severity & temporal patterns)
          </p>
        </div>

        <div>
          {!data?.has_sufficient_data ? (
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium bg-[#1a2332] text-[#8b96a8] border border-[#253346]">
              <HelpCircle className="w-3.5 h-3.5" />
              Insufficient Baseline
            </span>
          ) : data.anomalies.length === 0 ? (
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium bg-green-500/10 text-green-400 border border-green-500/30">
              <CheckCircle2 className="w-3.5 h-3.5" />
              Operating Nominally
            </span>
          ) : (
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium bg-red-500/10 text-red-400 border border-red-500/30">
              <AlertTriangle className="w-3.5 h-3.5" />
              {data.anomalies.length} Flagged
            </span>
          )}
        </div>
      </div>

      {/* Content States */}
      <div className="mt-4">
        {!data?.has_sufficient_data ? (
          <div className="py-8 px-4 text-center rounded-lg bg-[#111722] border border-[#1c2636]">
            <HelpCircle className="w-8 h-8 text-[#556377] mx-auto mb-2" />
            <h4 className="text-xs font-semibold text-[#cbd5e1]">
              Not enough historical data to detect anomalies yet
            </h4>
            <p className="text-[11px] text-[#627084] mt-1 max-w-md mx-auto">
              SentinelAI requires at least 5 baseline historical security events to calculate statistical operational deviations without false positives.
            </p>
          </div>
        ) : data.anomalies.length === 0 ? (
          <div className="py-8 px-4 text-center rounded-lg bg-[#111722] border border-[#1c2636]">
            <CheckCircle2 className="w-8 h-8 text-green-400 mx-auto mb-2" />
            <h4 className="text-xs font-semibold text-[#cbd5e1]">
              No unusual activity patterns detected
            </h4>
            <p className="text-[11px] text-[#627084] mt-1 max-w-md mx-auto">
              All event rates, camera frequencies, and severity proportions are currently operating within calculated baseline bounds.
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {data.anomalies.map((anomaly) => (
              <div
                key={anomaly.id}
                className="p-4 rounded-xl bg-[#121824] border border-[#202c3e] hover:border-[#2f425d] transition-all space-y-2.5"
              >
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />
                    <span className="text-xs font-semibold text-white">
                      {anomaly.title}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    {getSeverityBadge(anomaly.severity)}
                    <span className="text-[10px] text-[#556377] font-mono">
                      {anomaly.type}
                    </span>
                  </div>
                </div>

                <p className="text-xs text-[#cbd5e1]">
                  {anomaly.description}
                </p>

                {/* Metric comparison cards */}
                <div className="grid grid-cols-3 gap-2 pt-1">
                  <div className="p-2 rounded bg-[#161f2e] border border-[#223146] text-center">
                    <span className="text-[10px] text-[#627084] block">Observed</span>
                    <span className="text-xs font-bold text-white">
                      {anomaly.observed_value}
                    </span>
                  </div>
                  <div className="p-2 rounded bg-[#161f2e] border border-[#223146] text-center">
                    <span className="text-[10px] text-[#627084] block">Baseline</span>
                    <span className="text-xs font-bold text-[#94a3b8]">
                      {anomaly.baseline_value}
                    </span>
                  </div>
                  <div className="p-2 rounded bg-[#161f2e] border border-[#223146] text-center">
                    <span className="text-[10px] text-[#627084] block">Deviation</span>
                    <span className="text-xs font-bold text-amber-400">
                      +{anomaly.deviation_percentage}%
                    </span>
                  </div>
                </div>

                <div className="text-[11px] text-[#8b96a8] bg-[#0d121c] p-2 rounded border border-[#1b2535]">
                  <span className="font-medium text-[#3b7dd8]">Mathematical Explanation: </span>
                  {anomaly.why_flagged}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
