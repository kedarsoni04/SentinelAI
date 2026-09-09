'use client';

import { useState } from 'react';
import { Camera, MapPin, Wifi, Power, Edit2, Trash2, Circle } from 'lucide-react';
import type { Camera as CameraType } from '@/types';

interface CameraCardProps {
  camera: CameraType;
  onEdit: (camera: CameraType) => void;
  onDelete: (camera: CameraType) => void;
  onToggle: (camera: CameraType, enabled: boolean) => Promise<void>;
}

const SOURCE_TYPE_LABELS: Record<string, string> = {
  WEBCAM: 'Webcam',
  RTSP: 'RTSP',
  HTTP_STREAM: 'HTTP Stream',
  VIDEO_FILE: 'Video File',
};

const STATUS_CONFIG: Record<string, { dot: string; label: string; textColor: string }> = {
  ONLINE:  { dot: '#22c55e', label: 'Online',  textColor: '#22c55e' },
  OFFLINE: { dot: '#ef4444', label: 'Offline', textColor: '#ef4444' },
  UNKNOWN: { dot: '#4e5a6b', label: 'Unknown', textColor: '#4e5a6b' },
};

/**
 * CameraCard — displays a single camera's configuration in the camera grid.
 */
export default function CameraCard({ camera, onEdit, onDelete, onToggle }: CameraCardProps) {
  const [toggling, setToggling] = useState(false);
  const statusCfg = STATUS_CONFIG[camera.status] || STATUS_CONFIG.UNKNOWN;

  const handleToggle = async () => {
    setToggling(true);
    try {
      await onToggle(camera, !camera.is_enabled);
    } finally {
      setToggling(false);
    }
  };

  return (
    <div className="bg-[#111620] border border-[#1e2736] rounded-xl p-5 hover:border-[#2a3748] transition-colors duration-200 flex flex-col gap-4">
      {/* Header */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-3 min-w-0">
          <div className="w-9 h-9 rounded-lg bg-[rgba(59,125,216,0.1)] flex items-center justify-center shrink-0 mt-0.5">
            <Camera className="w-4.5 h-4.5 text-[#3b7dd8]" style={{ width: '18px', height: '18px' }} />
          </div>
          <div className="min-w-0">
            <p className="text-sm font-semibold text-[#e8edf5] truncate">{camera.name}</p>
            <div className="flex items-center gap-1.5 mt-0.5">
              <MapPin className="w-3 h-3 text-[#4e5a6b] shrink-0" />
              <span className="text-xs text-[#8b96a8] truncate">{camera.location}</span>
            </div>
          </div>
        </div>

        {/* Enabled badge */}
        <div className={`
          shrink-0 flex items-center gap-1.5 px-2 py-1 rounded-md text-[10px] font-semibold uppercase tracking-wider
          ${camera.is_enabled
            ? 'bg-[rgba(34,197,94,0.08)] text-[#22c55e] border border-[rgba(34,197,94,0.15)]'
            : 'bg-[rgba(78,90,107,0.12)] text-[#4e5a6b] border border-[#1e2736]'
          }
        `}>
          <Circle className="w-1.5 h-1.5 fill-current" />
          {camera.is_enabled ? 'Enabled' : 'Disabled'}
        </div>
      </div>

      {/* Details */}
      <div className="grid grid-cols-2 gap-2">
        <div className="bg-[#0d1117] rounded-lg px-3 py-2">
          <p className="text-[9px] text-[#4e5a6b] uppercase tracking-widest mb-0.5">Source</p>
          <div className="flex items-center gap-1.5">
            <Wifi className="w-3 h-3 text-[#3b7dd8]" />
            <span className="text-xs text-[#8b96a8]">{SOURCE_TYPE_LABELS[camera.source_type] || camera.source_type}</span>
          </div>
        </div>
        <div className="bg-[#0d1117] rounded-lg px-3 py-2">
          <p className="text-[9px] text-[#4e5a6b] uppercase tracking-widest mb-0.5">Status</p>
          <div className="flex items-center gap-1.5">
            <Circle className="w-1.5 h-1.5 fill-current shrink-0" style={{ color: statusCfg.dot }} />
            <span className="text-xs font-medium" style={{ color: statusCfg.textColor }}>{statusCfg.label}</span>
          </div>
        </div>
      </div>

      {/* Stream URL */}
      {camera.stream_url && (
        <div className="bg-[#0d1117] rounded-lg px-3 py-2">
          <p className="text-[9px] text-[#4e5a6b] uppercase tracking-widest mb-0.5">Stream URL</p>
          <p className="text-xs text-[#8b96a8] font-mono truncate">{camera.stream_url}</p>
        </div>
      )}

      {/* Last Active */}
      <p className="text-[10px] text-[#4e5a6b]">
        Last active:{' '}
        <span className="text-[#4e5a6b]">
          {camera.last_active
            ? new Date(camera.last_active).toLocaleString()
            : 'Not available — monitoring starts in Phase 3'}
        </span>
      </p>

      {/* Actions */}
      <div className="flex items-center gap-2 pt-1 border-t border-[#1a2030]">
        {/* Toggle */}
        <button
          onClick={handleToggle}
          disabled={toggling}
          className={`
            flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium
            transition-colors duration-150
            ${camera.is_enabled
              ? 'text-[#f59e0b] hover:bg-[rgba(245,158,11,0.08)] border border-[rgba(245,158,11,0.15)]'
              : 'text-[#22c55e] hover:bg-[rgba(34,197,94,0.08)] border border-[rgba(34,197,94,0.15)]'
            }
            disabled:opacity-50 disabled:cursor-not-allowed
          `}
          title={camera.is_enabled ? 'Disable camera' : 'Enable camera'}
        >
          <Power className="w-3 h-3" />
          {toggling ? 'Updating…' : camera.is_enabled ? 'Disable' : 'Enable'}
        </button>

        <div className="flex-1" />

        {/* Edit */}
        <button
          onClick={() => onEdit(camera)}
          className="
            flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium
            text-[#8b96a8] hover:text-[#e8edf5] hover:bg-[#161c28]
            border border-[#1e2736] hover:border-[#2a3748]
            transition-colors duration-150
          "
        >
          <Edit2 className="w-3 h-3" />
          Edit
        </button>

        {/* Delete */}
        <button
          onClick={() => onDelete(camera)}
          className="
            flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium
            text-[#ef4444] hover:bg-[rgba(239,68,68,0.08)]
            border border-[rgba(239,68,68,0.15)]
            transition-colors duration-150
          "
        >
          <Trash2 className="w-3 h-3" />
          Delete
        </button>
      </div>
    </div>
  );
}
