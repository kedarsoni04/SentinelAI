'use client';

import { useState, useRef, DragEvent, ChangeEvent } from 'react';
import { UploadCloud, Film, CheckCircle2, AlertCircle, X, Loader2 } from 'lucide-react';
import { uploadVideo } from '@/services/videoAnalysis';
import { extractErrorMessage } from '@/services/auth';

const ALLOWED_EXTS = ['.mp4', '.avi', '.mov', '.mkv', '.webm'];
const MAX_SIZE_MB = 250;

interface VideoUploadZoneProps {
  onUploadSuccess: (jobId: string, filename: string) => void;
  isProcessing?: boolean;
}

export default function VideoUploadZone({
  onUploadSuccess,
  isProcessing = false,
}: VideoUploadZoneProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadProgress, setUploadProgress] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);

  const validateAndSetFile = (file: File) => {
    setError(null);
    const ext = '.' + file.name.split('.').pop()?.toLowerCase();

    if (!ALLOWED_EXTS.includes(ext)) {
      setError(
        `Unsupported video format '${ext}'. Supported formats: ${ALLOWED_EXTS.join(', ')}`
      );
      return;
    }

    const fileSizeMB = file.size / (1024 * 1024);
    if (fileSizeMB > MAX_SIZE_MB) {
      setError(
        `File size (${fileSizeMB.toFixed(1)} MB) exceeds the maximum limit of ${MAX_SIZE_MB} MB.`
      );
      return;
    }

    setSelectedFile(file);
  };

  const handleDragOver = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      validateAndSetFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      validateAndSetFile(e.target.files[0]);
    }
  };

  const handleClear = () => {
    setSelectedFile(null);
    setUploadProgress(null);
    setError(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleStartAnalysis = async () => {
    if (!selectedFile) return;

    setIsUploading(true);
    setError(null);
    setUploadProgress(0);

    try {
      const res = await uploadVideo(selectedFile, (progressEvent) => {
        if (progressEvent.total) {
          const pct = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          setUploadProgress(pct);
        }
      });

      onUploadSuccess(res.id, res.original_filename);
      handleClear();
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="bg-[#111620] border border-[#1e2736] rounded-xl p-6">
      <input
        ref={fileInputRef}
        type="file"
        accept=".mp4,.avi,.mov,.mkv,.webm"
        className="hidden"
        onChange={handleFileChange}
        disabled={isUploading || isProcessing}
      />

      {!selectedFile ? (
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          className={`
            border-2 border-dashed rounded-xl p-8 sm:p-12
            flex flex-col items-center justify-center text-center cursor-pointer
            transition-all duration-200
            ${
              isDragging
                ? 'border-[#3b7dd8] bg-[#3b7dd8]/5 scale-[1.005]'
                : 'border-[#1e2736] hover:border-[#3b7dd8]/50 hover:bg-[#161c28]/50'
            }
          `}
        >
          <div className="w-14 h-14 rounded-full bg-[#161c28] border border-[#1e2736] flex items-center justify-center mb-4 text-[#3b7dd8]">
            <UploadCloud className="w-7 h-7" />
          </div>
          <h3 className="text-base font-semibold text-[#e8edf5] mb-1">
            Upload Surveillance Video
          </h3>
          <p className="text-sm text-[#8b96a8] max-w-sm mb-4">
            Drag and drop your video file here, or click to browse from your device
          </p>

          <div className="flex items-center gap-2 text-xs font-mono text-[#4e5a6b] bg-[#0a0d12] px-3 py-1.5 rounded-md border border-[#1e2736]">
            <span>MP4 • AVI • MOV • MKV • WEBM</span>
            <span>·</span>
            <span>Max {MAX_SIZE_MB} MB</span>
          </div>
        </div>
      ) : (
        <div className="border border-[#1e2736] bg-[#0d1117] rounded-xl p-5 space-y-4">
          <div className="flex items-start justify-between gap-4">
            <div className="flex items-center gap-3 min-w-0">
              <div className="w-10 h-10 rounded-lg bg-[#3b7dd8]/10 border border-[#3b7dd8]/20 flex items-center justify-center text-[#3b7dd8] shrink-0">
                <Film className="w-5 h-5" />
              </div>
              <div className="min-w-0">
                <h4 className="text-sm font-medium text-[#e8edf5] truncate">
                  {selectedFile.name}
                </h4>
                <p className="text-xs text-[#8b96a8] mt-0.5">
                  {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB · ready for analysis
                </p>
              </div>
            </div>

            {!isUploading && (
              <button
                type="button"
                onClick={handleClear}
                className="text-[#4e5a6b] hover:text-[#e8edf5] p-1 rounded-md transition-colors"
                title="Remove selection"
              >
                <X className="w-4 h-4" />
              </button>
            )}
          </div>

          {/* Upload Progress Bar */}
          {isUploading && uploadProgress !== null && (
            <div className="space-y-1.5">
              <div className="flex justify-between text-xs text-[#8b96a8]">
                <span>Uploading video to server…</span>
                <span>{uploadProgress}%</span>
              </div>
              <div className="w-full h-2 bg-[#161c28] rounded-full overflow-hidden">
                <div
                  className="h-full bg-[#3b7dd8] transition-all duration-150 rounded-full"
                  style={{ width: `${uploadProgress}%` }}
                />
              </div>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex items-center justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={handleClear}
              disabled={isUploading}
              className="px-4 py-2 text-xs font-medium text-[#8b96a8] hover:text-[#e8edf5] hover:bg-[#161c28] rounded-lg border border-[#1e2736] transition-colors disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={handleStartAnalysis}
              disabled={isUploading}
              className="px-5 py-2 text-xs font-medium text-white bg-[#3b7dd8] hover:bg-[#4d8fe8] rounded-lg flex items-center gap-2 transition-colors disabled:opacity-50 shadow-sm"
            >
              {isUploading ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  Uploading & Queuing…
                </>
              ) : (
                <>
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  Analyze Video
                </>
              )}
            </button>
          </div>
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="mt-4 flex items-start gap-2.5 p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-xs">
          <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
          <span>{error}</span>
        </div>
      )}
    </div>
  );
}
