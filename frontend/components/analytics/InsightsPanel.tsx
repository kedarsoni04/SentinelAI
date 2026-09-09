'use client';

import type { SecurityInsightsData } from '@/types';
import { Lightbulb, Camera, PieChart, Clock, ShieldAlert, AlertCircle } from 'lucide-react';

interface InsightsPanelProps {
  data: SecurityInsightsData;
  isLoading?: boolean;
}

export default function InsightsPanel({
  data,
  isLoading = false,
}: InsightsPanelProps) {
  if (isLoading) {
    return (
      <div className="h-[120px] bg-[#0d1117] border border-[#1e2736] rounded-xl p-4 animate-pulse" />
    );
  }

  const insights = data?.insights || [];
  if (insights.length === 0) {
    return null;
  }

  const getInsightIcon = (type: string) => {
    switch (type) {
      case 'TOP_CAMERA':
        return <Camera className="w-4 h-4 text-[#3b7dd8]" />;
      case 'TOP_EVENT_TYPE':
        return <PieChart className="w-4 h-4 text-emerald-400" />;
      case 'PEAK_ACTIVITY_TIME':
        return <Clock className="w-4 h-4 text-amber-400" />;
      case 'CAMERA_RISK':
        return <ShieldAlert className="w-4 h-4 text-red-400" />;
      case 'ANOMALY':
        return <AlertCircle className="w-4 h-4 text-orange-400" />;
      default:
        return <Lightbulb className="w-4 h-4 text-[#3b7dd8]" />;
    }
  };

  return (
    <div className="bg-[#0d1117] border border-[#1e2736] rounded-xl p-5">
      <div className="flex items-center gap-2 pb-3 border-b border-[#1a2332]">
        <Lightbulb className="w-4 h-4 text-[#3b7dd8]" />
        <h3 className="text-sm font-semibold text-[#e8edf5] tracking-tight">
          Operational Security Insights
        </h3>
        <span className="text-xs text-[#8b96a8]">({insights.length} active findings)</span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3.5 mt-3.5">
        {insights.map((insight) => (
          <div
            key={insight.id}
            className="p-3.5 rounded-lg bg-[#121824] border border-[#1f2c3e] hover:border-[#2e415b] transition-all flex flex-col justify-between"
          >
            <div>
              <div className="flex items-center gap-2 mb-1.5">
                {getInsightIcon(insight.type)}
                <h4 className="text-xs font-semibold text-white tracking-tight">
                  {insight.title}
                </h4>
              </div>
              <p className="text-xs text-[#cbd5e1] leading-relaxed">
                {insight.description}
              </p>
            </div>

            <div className="mt-2.5 pt-2 border-t border-[#1a2536] flex items-center justify-between text-[10px] text-[#627084]">
              <span className="font-mono">{insight.type.replace(/_/g, ' ')}</span>
              <span className="text-[#3b7dd8] font-medium">Grounded in historical data</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
