'use client';

import { useState, FormEvent, useEffect } from 'react';
import { X, Loader2, AlertCircle } from 'lucide-react';
import type { Camera, CameraSourceType, CreateCameraData, UpdateCameraData } from '@/types';

interface CameraFormModalProps {
  mode: 'create' | 'edit';
  camera?: Camera | null;
  onSubmit: (data: CreateCameraData | UpdateCameraData) => Promise<void>;
  onClose: () => void;
}

const SOURCE_TYPE_OPTIONS: { value: CameraSourceType; label: string; example: string }[] = [
  { value: 'RTSP',        label: 'RTSP',        example: 'rtsp://username:password@camera-ip:554/stream' },
  { value: 'HTTP_STREAM', label: 'HTTP Stream',  example: 'http://camera-ip:8080/video' },
  { value: 'WEBCAM',      label: 'Webcam',       example: 'Local device — no URL required' },
  { value: 'VIDEO_FILE',  label: 'Video File',   example: 'http://server/path/to/video.mp4' },
];

/**
 * CameraFormModal — handles both Add and Edit camera workflows.
 * Pre-fills fields in edit mode. Validates required fields before submission.
 */
export default function CameraFormModal({ mode, camera, onSubmit, onClose }: CameraFormModalProps) {
  const [name, setName] = useState('');
  const [location, setLocation] = useState('');
  const [sourceType, setSourceType] = useState<CameraSourceType>('RTSP');
  const [streamUrl, setStreamUrl] = useState('');
  const [isEnabled, setIsEnabled] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  // Pre-fill for edit mode
  useEffect(() => {
    if (mode === 'edit' && camera) {
      setName(camera.name);
      setLocation(camera.location);
      setSourceType(camera.source_type);
      setStreamUrl(camera.stream_url || '');
      setIsEnabled(camera.is_enabled);
    }
  }, [mode, camera]);

  const selectedSourceOption = SOURCE_TYPE_OPTIONS.find((o) => o.value === sourceType);
  const requiresUrl = sourceType !== 'WEBCAM';

  const validate = (): string | null => {
    if (!name.trim()) return 'Camera name is required.';
    if (!location.trim()) return 'Camera location is required.';
    if (!sourceType) return 'Source type is required.';
    if (streamUrl.trim()) {
      const url = streamUrl.trim();
      if (!url.startsWith('rtsp://') && !url.startsWith('rtsps://') &&
          !url.startsWith('http://') && !url.startsWith('https://')) {
        return 'Stream URL must start with rtsp://, rtsps://, http://, or https://';
      }
    }
    return null;
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);

    const validationError = validate();
    if (validationError) {
      setError(validationError);
      return;
    }

    setIsLoading(true);
    try {
      const data: CreateCameraData = {
        name: name.trim(),
        location: location.trim(),
        source_type: sourceType,
        stream_url: streamUrl.trim() || null,
        is_enabled: isEnabled,
      };
      await onSubmit(data);
    } catch (err: unknown) {
      const msg =
        err instanceof Error
          ? err.message
          : 'An unexpected error occurred. Please try again.';
      setError(msg);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative w-full max-w-md bg-[#111620] border border-[#1e2736] rounded-xl shadow-2xl shadow-black/60 max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-[#1e2736]">
          <div>
            <h2 className="text-sm font-semibold text-[#e8edf5]">
              {mode === 'create' ? 'Add Camera' : 'Edit Camera'}
            </h2>
            <p className="text-xs text-[#8b96a8] mt-0.5">
              {mode === 'create'
                ? 'Configure a new surveillance camera source.'
                : 'Update camera configuration.'}
            </p>
          </div>
          <button
            onClick={onClose}
            className="w-7 h-7 flex items-center justify-center rounded-lg text-[#4e5a6b] hover:text-[#8b96a8] hover:bg-[#161c28] transition-colors"
            aria-label="Close"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Body */}
        <form onSubmit={handleSubmit} className="px-6 py-5 space-y-4">
          {/* Error */}
          {error && (
            <div className="flex items-start gap-2.5 bg-[rgba(239,68,68,0.08)] border border-[rgba(239,68,68,0.2)] rounded-lg px-4 py-3">
              <AlertCircle className="w-4 h-4 text-[#ef4444] mt-0.5 shrink-0" />
              <p className="text-sm text-[#ef4444]">{error}</p>
            </div>
          )}

          {/* Camera Name */}
          <div>
            <label className="block text-xs font-medium text-[#8b96a8] mb-1.5 uppercase tracking-wider">
              Camera Name <span className="text-[#ef4444]">*</span>
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              disabled={isLoading}
              placeholder="e.g. Main Entrance Camera"
              className="
                w-full h-10 px-3 rounded-lg
                bg-[#161c28] border border-[#1e2736]
                text-sm text-[#e8edf5] placeholder:text-[#4e5a6b]
                focus:outline-none focus:border-[#3b7dd8] focus:ring-1 focus:ring-[#3b7dd8]
                transition-colors duration-150 disabled:opacity-50
              "
            />
          </div>

          {/* Location */}
          <div>
            <label className="block text-xs font-medium text-[#8b96a8] mb-1.5 uppercase tracking-wider">
              Location <span className="text-[#ef4444]">*</span>
            </label>
            <input
              type="text"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              disabled={isLoading}
              placeholder="e.g. Main Entrance, Parking Area"
              className="
                w-full h-10 px-3 rounded-lg
                bg-[#161c28] border border-[#1e2736]
                text-sm text-[#e8edf5] placeholder:text-[#4e5a6b]
                focus:outline-none focus:border-[#3b7dd8] focus:ring-1 focus:ring-[#3b7dd8]
                transition-colors duration-150 disabled:opacity-50
              "
            />
          </div>

          {/* Source Type */}
          <div>
            <label className="block text-xs font-medium text-[#8b96a8] mb-1.5 uppercase tracking-wider">
              Source Type <span className="text-[#ef4444]">*</span>
            </label>
            <select
              value={sourceType}
              onChange={(e) => setSourceType(e.target.value as CameraSourceType)}
              disabled={isLoading}
              className="
                w-full h-10 px-3 rounded-lg
                bg-[#161c28] border border-[#1e2736]
                text-sm text-[#e8edf5]
                focus:outline-none focus:border-[#3b7dd8] focus:ring-1 focus:ring-[#3b7dd8]
                transition-colors duration-150 disabled:opacity-50
              "
            >
              {SOURCE_TYPE_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value} className="bg-[#161c28]">
                  {opt.label}
                </option>
              ))}
            </select>
          </div>

          {/* Stream URL */}
          <div>
            <label className="block text-xs font-medium text-[#8b96a8] mb-1.5 uppercase tracking-wider">
              Stream URL
              {!requiresUrl && <span className="ml-1 text-[#4e5a6b] normal-case font-normal">(not required for Webcam)</span>}
            </label>
            <input
              type="text"
              value={streamUrl}
              onChange={(e) => setStreamUrl(e.target.value)}
              disabled={isLoading}
              placeholder={selectedSourceOption?.example || 'rtsp://...'}
              className="
                w-full h-10 px-3 rounded-lg
                bg-[#161c28] border border-[#1e2736]
                text-sm text-[#e8edf5] placeholder:text-[#4e5a6b] font-mono
                focus:outline-none focus:border-[#3b7dd8] focus:ring-1 focus:ring-[#3b7dd8]
                transition-colors duration-150 disabled:opacity-50
              "
            />
            {selectedSourceOption && (
              <p className="text-[10px] text-[#4e5a6b] mt-1.5">
                Example: <span className="text-[#3b7dd8] font-mono">{selectedSourceOption.example}</span>
              </p>
            )}
          </div>

          {/* Enabled toggle */}
          <div className="flex items-center justify-between py-2 border-t border-[#1a2030]">
            <div>
              <p className="text-sm text-[#e8edf5] font-medium">Enable Camera</p>
              <p className="text-xs text-[#4e5a6b] mt-0.5">Camera will be active and visible in the system</p>
            </div>
            <button
              type="button"
              onClick={() => setIsEnabled(!isEnabled)}
              disabled={isLoading}
              className={`
                relative w-11 h-6 rounded-full transition-colors duration-200
                ${isEnabled ? 'bg-[#3b7dd8]' : 'bg-[#1e2736]'}
                disabled:opacity-50
              `}
              role="switch"
              aria-checked={isEnabled}
            >
              <span className={`
                absolute top-0.5 left-0.5 w-5 h-5 rounded-full bg-white shadow
                transition-transform duration-200
                ${isEnabled ? 'translate-x-5' : 'translate-x-0'}
              `} />
            </button>
          </div>

          {/* Footer */}
          <div className="flex gap-3 pt-1">
            <button
              type="button"
              onClick={onClose}
              disabled={isLoading}
              className="
                flex-1 h-10 rounded-lg border border-[#1e2736]
                text-sm text-[#8b96a8] hover:text-[#e8edf5] hover:border-[#2a3748]
                transition-colors duration-150 disabled:opacity-50
              "
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isLoading}
              className="
                flex-1 h-10 rounded-lg bg-[#3b7dd8] hover:bg-[#4d8fe8]
                text-sm font-medium text-white
                flex items-center justify-center gap-2
                transition-colors duration-150 disabled:opacity-60
                focus:outline-none focus:ring-2 focus:ring-[#3b7dd8] focus:ring-offset-2 focus:ring-offset-[#111620]
              "
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  {mode === 'create' ? 'Adding…' : 'Saving…'}
                </>
              ) : (
                mode === 'create' ? 'Add Camera' : 'Save Changes'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
