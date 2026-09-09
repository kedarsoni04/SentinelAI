'use client';

import React from 'react';
import { Crosshair, User, Car, Clock } from 'lucide-react';
import type { ActiveTrackInfo } from '@/types';

interface ActiveTracksListProps {
  tracks: ActiveTrackInfo[];
}

export default function ActiveTracksList({ tracks }: ActiveTracksListProps) {
  const getIcon = (className: string) => {
    switch (className.toLowerCase()) {
      case 'person':
        return <User className="w-3.5 h-3.5 text-cyan-400" />;
      case 'car':
      case 'truck':
      case 'bus':
        return <Car className="w-3.5 h-3.5 text-blue-400" />;
      default:
        return <Crosshair className="w-3.5 h-3.5 text-purple-400" />;
    }
  };

  return (
    <div className="bg-[#111620] border border-[#1e2736] rounded-xl p-4 space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-xs font-semibold text-[#8b96a8] uppercase tracking-wider flex items-center gap-1.5">
          <Crosshair className="w-3.5 h-3.5 text-[#3b7dd8]" />
          Active Tracked Objects ({tracks.length})
        </h3>
        <span className="text-[10px] text-[#4e5a6b] font-mono">ByteTrack Engine</span>
      </div>

      {tracks.length === 0 ? (
        <div className="py-6 text-center text-xs text-[#4e5a6b]">
          No active objects currently tracked in this frame.
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 max-h-48 overflow-y-auto pr-1">
          {tracks.map((t) => (
            <div
              key={t.track_id}
              className="flex items-center justify-between p-2 rounded-lg bg-[#0e131d] border border-[#1e2736] text-xs hover:border-[#3b7dd8]/40 transition-colors"
            >
              <div className="flex items-center gap-2">
                <div className="p-1 rounded bg-[#161c28]">
                  {getIcon(t.class_name)}
                </div>
                <div>
                  <div className="font-medium text-[#e8edf5] flex items-center gap-1">
                    <span>{t.class_name.toUpperCase()}</span>
                    <span className="font-mono text-cyan-400">#{t.track_id}</span>
                  </div>
                  <div className="text-[10px] text-[#8b96a8] font-mono">
                    Conf: {(t.confidence * 100).toFixed(0)}%
                  </div>
                </div>
              </div>

              <div className="text-right font-mono text-[11px] text-[#8b96a8] flex items-center gap-1">
                <Clock className="w-3 h-3 text-[#4e5a6b]" />
                <span>{t.duration_seconds.toFixed(1)}s</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
