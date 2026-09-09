'use client';

import React, { useEffect } from 'react';
import { AlertOctagon, RotateCcw } from 'lucide-react';

export default function DashboardError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error('SentinelAI Dashboard Module Error:', error);
  }, [error]);

  return (
    <div className="p-8 flex items-center justify-center min-h-[50vh]">
      <div className="max-w-lg w-full bg-slate-900/90 border border-amber-500/30 rounded-xl p-6 shadow-xl text-center">
        <div className="mx-auto w-12 h-12 rounded-full bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400 mb-4">
          <AlertOctagon className="h-6 w-6" />
        </div>

        <h2 className="text-lg font-semibold text-white mb-1">SOC Module Disruption</h2>
        <p className="text-xs text-slate-400 mb-4">
          The requested dashboard view encountered an unexpected error while rendering data.
        </p>

        <div className="bg-slate-950 border border-slate-800 rounded-lg p-3 mb-6 text-left">
          <p className="text-xs font-mono text-amber-300/90 break-words">
            {error.message || 'Unknown operational error.'}
          </p>
        </div>

        <button
          onClick={() => reset()}
          className="inline-flex items-center gap-2 py-2 px-5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-sm font-medium transition-colors shadow-lg shadow-emerald-600/20"
        >
          <RotateCcw className="h-4 w-4" />
          Reload Module View
        </button>
      </div>
    </div>
  );
}
