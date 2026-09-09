'use client';

import React, { useState, useRef } from 'react';
import {
  Trash2,
  Undo2,
  Save,
  AlertCircle,
} from 'lucide-react';
import type { Camera as CameraType, CoordinatePoint, CreateSecurityZoneData, ZoneType } from '@/types';

interface SecurityZoneEditorProps {
  cameras: CameraType[];
  onSave: (data: CreateSecurityZoneData) => Promise<void>;
  onCancel: () => void;
}

export default function SecurityZoneEditor({ cameras, onSave, onCancel }: SecurityZoneEditorProps) {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [cameraId, setCameraId] = useState<string>('');
  const [zoneType, setZoneType] = useState<ZoneType>('RESTRICTED');
  const [points, setPoints] = useState<CoordinatePoint[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const canvasRef = useRef<SVGSVGElement | null>(null);

  const handleCanvasClick = (e: React.MouseEvent<SVGSVGElement>) => {
    if (!canvasRef.current) return;
    const rect = canvasRef.current.getBoundingClientRect();
    const x = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
    const y = Math.max(0, Math.min(1, (e.clientY - rect.top) / rect.height));

    setPoints((prev) => [...prev, { x: Number(x.toFixed(4)), y: Number(y.toFixed(4)) }]);
    setError(null);
  };

  const handleUndo = () => {
    setPoints((prev) => prev.slice(0, -1));
  };

  const handleClear = () => {
    setPoints([]);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) {
      setError('Please provide a zone name.');
      return;
    }
    if (points.length < 3) {
      setError('A polygon zone requires at least 3 vertex points.');
      return;
    }

    setIsSubmitting(true);
    try {
      await onSave({
        name: name.trim(),
        description: description.trim() || null,
        camera_id: cameraId || null,
        zone_type: zoneType,
        coordinates: points,
        is_enabled: true,
      });
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } };
      setError(e?.response?.data?.detail || 'Failed to save security zone.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="bg-[#111620] border border-[#1e2736] rounded-xl p-5 space-y-5">
      <div className="flex items-center justify-between border-b border-[#1e2736] pb-4">
        <div>
          <h3 className="text-sm font-semibold text-[#e8edf5]">Interactive Security Zone Editor</h3>
          <p className="text-xs text-[#8b96a8]">
            Click inside the canvas to draw polygon vertices. Coordinates are normalized (0.0 &ndash; 1.0).
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={handleUndo}
            disabled={points.length === 0}
            className="px-2.5 py-1 rounded bg-[#161c28] border border-[#1e2736] text-xs text-[#8b96a8] hover:text-[#e8edf5] disabled:opacity-40 flex items-center gap-1"
          >
            <Undo2 className="w-3.5 h-3.5" />
            Undo
          </button>
          <button
            type="button"
            onClick={handleClear}
            disabled={points.length === 0}
            className="px-2.5 py-1 rounded bg-[#161c28] border border-[#1e2736] text-xs text-red-400 hover:text-red-300 disabled:opacity-40 flex items-center gap-1"
          >
            <Trash2 className="w-3.5 h-3.5" />
            Clear
          </button>
        </div>
      </div>

      {error && (
        <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-xs text-red-400 flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Interactive Canvas Area */}
      <div className="relative aspect-video w-full bg-[#0a0d13] border border-[#1e2736] rounded-lg overflow-hidden select-none cursor-crosshair">
        {/* Subtle grid pattern */}
        <div className="absolute inset-0 opacity-10 bg-[radial-gradient(#3b7dd8_1px,transparent_1px)] [background-size:16px_16px]" />

        <svg
          ref={canvasRef}
          onClick={handleCanvasClick}
          className="absolute inset-0 w-full h-full"
        >
          {points.length >= 3 && (
            <polygon
              points={points.map((p) => `${p.x * 1000},${p.y * 1000}`).join(' ')}
              viewBox="0 0 1000 1000"
              className={
                zoneType === 'RESTRICTED'
                  ? 'fill-red-500/20 stroke-red-400 stroke-2'
                  : 'fill-purple-500/20 stroke-purple-400 stroke-2'
              }
            />
          )}

          {points.map((p, idx) => (
            <g key={idx}>
              <circle
                cx={`${p.x * 100}%`}
                cy={`${p.y * 100}%`}
                r="4"
                className="fill-cyan-400 stroke-[#0a0d13] stroke-1"
              />
              <text
                x={`${p.x * 100}%`}
                y={`${p.y * 100}%`}
                dx="6"
                dy="-6"
                className="text-[10px] fill-[#8b96a8] font-mono select-none"
              >
                P{idx + 1}
              </text>
            </g>
          ))}
        </svg>

        {points.length === 0 && (
          <div className="absolute inset-0 flex items-center justify-center pointer-events-none text-xs text-[#4e5a6b]">
            Click anywhere on this canvas to place your first polygon point
          </div>
        )}
      </div>

      {/* Form Fields */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
        <div>
          <label className="block text-[#8b96a8] mb-1">Zone Name *</label>
          <input
            type="text"
            required
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="e.g. Server Room Entrance"
            className="w-full px-3 py-1.5 rounded-lg bg-[#0e131d] border border-[#1e2736] text-[#e8edf5] focus:outline-none focus:border-[#3b7dd8]"
          />
        </div>

        <div>
          <label className="block text-[#8b96a8] mb-1">Zone Type</label>
          <select
            value={zoneType}
            onChange={(e) => setZoneType(e.target.value as ZoneType)}
            className="w-full px-3 py-1.5 rounded-lg bg-[#0e131d] border border-[#1e2736] text-[#e8edf5] focus:outline-none focus:border-[#3b7dd8]"
          >
            <option value="RESTRICTED">RESTRICTED (Intrusion / Loitering)</option>
            <option value="CROWD">CROWD (High Density Monitoring)</option>
            <option value="MONITORING">MONITORING (General Spatial Watch)</option>
          </select>
        </div>

        <div>
          <label className="block text-[#8b96a8] mb-1">Associated Camera (Optional)</label>
          <select
            value={cameraId}
            onChange={(e) => setCameraId(e.target.value)}
            className="w-full px-3 py-1.5 rounded-lg bg-[#0e131d] border border-[#1e2736] text-[#e8edf5] focus:outline-none focus:border-[#3b7dd8]"
          >
            <option value="">All / Direct Uploads</option>
            {cameras.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name} ({c.location})
              </option>
            ))}
          </select>
        </div>
      </div>

      <div>
        <label className="block text-xs text-[#8b96a8] mb-1">Description (Optional)</label>
        <input
          type="text"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Purpose and operational context of this restricted zone..."
          className="w-full px-3 py-1.5 rounded-lg bg-[#0e131d] border border-[#1e2736] text-xs text-[#e8edf5] focus:outline-none focus:border-[#3b7dd8]"
        />
      </div>

      <div className="flex items-center justify-between pt-3 border-t border-[#1e2736]">
        <span className="text-xs font-mono text-[#8b96a8]">
          Vertices: <strong className="text-cyan-400">{points.length}</strong> (min: 3)
        </span>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={onCancel}
            className="px-3 py-1.5 rounded-lg bg-[#161c28] hover:bg-[#1e2736] text-xs text-[#8b96a8] transition-colors"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={isSubmitting || points.length < 3}
            className="px-4 py-1.5 rounded-lg bg-[#3b7dd8] hover:bg-[#2b6dc8] text-xs font-semibold text-white transition-colors disabled:opacity-50 flex items-center gap-1.5"
          >
            <Save className="w-3.5 h-3.5" />
            {isSubmitting ? 'Saving Zone...' : 'Save Security Zone'}
          </button>
        </div>
      </div>
    </form>
  );
}
