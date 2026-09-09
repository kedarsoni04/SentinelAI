'use client';

import React from 'react';
import { Camera, Film, Radio, ShieldAlert } from 'lucide-react';
import type { RealtimeStatus } from '@/types';

interface LiveFramePreviewProps {
  frameUrl: string | null;
  status: RealtimeStatus;
  cameraName?: string | null;
  timestampSeconds: number;
  frameIndex?: number | null;
  activeTracksCount: number;
  fps: number;
}

export default function LiveFramePreview({
  frameUrl,
  status,
  cameraName,
  timestampSeconds,
  frameIndex,
  activeTracksCount,
  fps,
}: LiveFramePreviewProps) {
  const isLive = status === 'RUNNING';

  return (
    <div className="relative aspect-video w-full bg-[#0a0d13] border border-[#1e2736] rounded-xl overflow-hidden shadow-2xl flex flex-col justify-between select-none">
      {/* Background Frame or Standby Placeholder */}
      {frameUrl ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          src={frameUrl}
          alt="Live Stream Frame"
          className="absolute inset-0 w-full h-full object-contain"
        />
      ) : (
        <div className="absolute inset-0 flex flex-col items-center justify-center text-center p-6 space-y-3 bg-[radial-gradient(#1e2736_1px,transparent_1px)] [background-size:24px_24px]">
          <div className="w-14 h-14 rounded-full bg-[#111620] border border-[#1e2736] flex items-center justify-center text-[#4e5a6b]">
            <Film className="w-6 h-6" />
          </div>
          <div>
            <h4 className="text-xs font-semibold text-[#8b96a8] uppercase tracking-wider">
              Surveillance Stream Standby
            </h4>
            <p className="text-[11px] text-[#4e5a6b] mt-1 max-w-xs">
              {isLive
                ? 'Awaiting first decoded frame from pipeline...'
                : 'Select an active video analysis session and start monitoring to stream live annotated frames.'}
            </p>
          </div>
        </div>
      )}

      {/* Top Overlay HUD */}
      <div className="relative z-10 p-3 bg-gradient-to-b from-black/80 via-black/40 to-transparent flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div
            className={`flex items-center gap-1.5 px-2 py-0.5 rounded text-[11px] font-mono font-semibold tracking-wider ${
              isLive
                ? 'bg-red-500/20 text-red-400 border border-red-500/30 animate-pulse'
                : 'bg-zinc-800/60 text-zinc-400 border border-zinc-700/40'
            }`}
          >
            <Radio className="w-3 h-3" />
            <span>{isLive ? 'REC ● LIVE' : status}</span>
          </div>

          {cameraName && (
            <div className="hidden sm:flex items-center gap-1 text-[11px] font-medium text-[#e8edf5] bg-black/60 px-2 py-0.5 rounded border border-[#1e2736]">
              <Camera className="w-3 h-3 text-[#3b7dd8]" />
              <span>{cameraName}</span>
            </div>
          )}
        </div>

        <div className="flex items-center gap-2 font-mono text-[11px] text-[#8b96a8] bg-black/60 px-2.5 py-0.5 rounded border border-[#1e2736]">
          <span className="text-[#e8edf5]">{timestampSeconds.toFixed(1)}s</span>
          {frameIndex !== undefined && frameIndex !== null && (
            <span className="text-[#4e5a6b]">#{frameIndex}</span>
          )}
        </div>
      </div>

      {/* Bottom Overlay HUD */}
      <div className="relative z-10 p-3 bg-gradient-to-t from-black/80 via-black/40 to-transparent flex items-center justify-between text-[11px] font-mono">
        <div className="flex items-center gap-3">
          <span className="text-[#8b96a8] flex items-center gap-1">
            <span className="text-[#4e5a6b]">FPS:</span>
            <span className="text-[#e8edf5] font-semibold">{fps > 0 ? fps.toFixed(1) : '—'}</span>
          </span>

          <span className="text-[#8b96a8] flex items-center gap-1">
            <span className="text-[#4e5a6b]">TARGETS:</span>
            <span className="text-cyan-400 font-semibold">{activeTracksCount}</span>
          </span>
        </div>

        <div className="flex items-center gap-1.5 text-[#8b96a8]">
          <ShieldAlert className="w-3.5 h-3.5 text-[#3b7dd8]" />
          <span className="text-[10px] tracking-widest text-[#4e5a6b]">SENTINEL AI VISION</span>
        </div>
      </div>
    </div>
  );
}
