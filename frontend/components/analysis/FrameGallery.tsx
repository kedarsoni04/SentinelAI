'use client';

import { useState, useEffect, useCallback } from 'react';
import {
  Maximize2,
  Clock,
  Cpu,
  Layers,
  ChevronLeft,
  ChevronRight,
  X,
  ExternalLink,
  Target,
  Sparkles,
  Eye,
} from 'lucide-react';
import type { AnalysisResult, Detection } from '@/types';
import { getAuthenticatedFrameUrl, getFrameDetections } from '@/services/videoAnalysis';

interface FrameGalleryProps {
  results: AnalysisResult[];
}

export default function FrameGallery({ results }: FrameGalleryProps) {
  const [activeModalIndex, setActiveModalIndex] = useState<number | null>(null);
  const [filterMode, setFilterMode] = useState<'all' | 'detected'>('all');
  const [viewMode, setViewMode] = useState<'annotated' | 'original'>('annotated');

  // Modal detections state
  const [modalDetections, setModalDetections] = useState<Detection[]>([]);
  const [isLoadingDetections, setIsLoadingDetections] = useState<boolean>(false);

  // Filtered results
  const filteredResults = results.filter((r) => {
    const hasDetections = (r.detection_count || 0) > 0;
    if (filterMode === 'detected' && !hasDetections) {
      return false;
    }
    return true;
  });

  const framesWithDetectionsCount = results.filter((r) => (r.detection_count || 0) > 0).length;

  const activeResult =
    activeModalIndex !== null && activeModalIndex < filteredResults.length
      ? filteredResults[activeModalIndex]
      : null;

  // Load detections when modal opens or active result changes
  useEffect(() => {
    if (!activeResult) {
      setModalDetections([]);
      return;
    }

    // Default to annotated view if available
    setViewMode(activeResult.annotated_frame_url ? 'annotated' : 'original');

    let isMounted = true;
    setIsLoadingDetections(true);

    getFrameDetections(activeResult.analysis_job_id, activeResult.id)
      .then((data) => {
        if (isMounted) {
          setModalDetections(data);
        }
      })
      .catch(() => {
        if (isMounted) {
          setModalDetections([]);
        }
      })
      .finally(() => {
        if (isMounted) {
          setIsLoadingDetections(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, [activeResult]);

  const handleNext = useCallback(() => {
    if (activeModalIndex !== null && activeModalIndex < filteredResults.length - 1) {
      setActiveModalIndex((prev) => (prev !== null ? prev + 1 : null));
    }
  }, [activeModalIndex, filteredResults.length]);

  const handlePrev = useCallback(() => {
    if (activeModalIndex !== null && activeModalIndex > 0) {
      setActiveModalIndex((prev) => (prev !== null ? prev - 1 : null));
    }
  }, [activeModalIndex]);

  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (activeModalIndex === null) return;
      if (e.key === 'ArrowRight') {
        handleNext();
      } else if (e.key === 'ArrowLeft') {
        handlePrev();
      } else if (e.key === 'Escape') {
        setActiveModalIndex(null);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [activeModalIndex, handleNext, handlePrev]);

  if (results.length === 0) {
    return (
      <div className="bg-[#111620] border border-[#1e2736] rounded-xl p-12 text-center">
        <p className="text-sm text-[#8b96a8]">No frames extracted for this video.</p>
      </div>
    );
  }

  const formatTimestamp = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    const ms = Math.floor((seconds % 1) * 100);
    return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}.${String(ms).padStart(2, '0')}`;
  };

  return (
    <div className="space-y-4">
      {/* Gallery Controls & Filtering Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-[#111620] border border-[#1e2736] rounded-xl p-4">
        <div className="flex items-center gap-2 flex-wrap">
          <div className="flex items-center gap-2">
            <Layers className="w-4 h-4 text-[#3b7dd8]" />
            <h3 className="text-sm font-semibold text-[#e8edf5]">
              Extracted Representative Frames
            </h3>
          </div>
          <span className="text-xs text-[#8b96a8] font-mono bg-[#161c28] px-2 py-0.5 rounded border border-[#1e2736]">
            {filteredResults.length} of {results.length} shown
          </span>
        </div>

        {/* Filter buttons */}
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => setFilterMode('all')}
            className={`px-3 py-1.5 text-xs font-medium rounded-lg transition-colors flex items-center gap-1.5 ${
              filterMode === 'all'
                ? 'bg-[#3b7dd8] text-white'
                : 'text-[#8b96a8] hover:text-[#e8edf5] bg-[#161c28] border border-[#1e2736]'
            }`}
          >
            All Frames ({results.length})
          </button>

          <button
            type="button"
            onClick={() => setFilterMode('detected')}
            className={`px-3 py-1.5 text-xs font-medium rounded-lg transition-colors flex items-center gap-1.5 ${
              filterMode === 'detected'
                ? 'bg-[#3b7dd8] text-white'
                : 'text-[#8b96a8] hover:text-[#e8edf5] bg-[#161c28] border border-[#1e2736]'
            }`}
          >
            <Target className="w-3.5 h-3.5 text-cyan-400" />
            With Objects ({framesWithDetectionsCount})
          </button>
        </div>
      </div>

      {/* Frame Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {filteredResults.map((result, idx) => {
          const displayUrl = getAuthenticatedFrameUrl(
            result.annotated_frame_url || result.thumbnail_url || result.frame_url
          );
          const detectionCount = result.detection_count || 0;

          return (
            <div
              key={result.id}
              onClick={() => setActiveModalIndex(idx)}
              className="group bg-[#111620] border border-[#1e2736] hover:border-[#3b7dd8]/60 rounded-xl overflow-hidden cursor-pointer transition-all duration-200 hover:shadow-lg hover:shadow-[#3b7dd8]/5 flex flex-col"
            >
              {/* Image Preview Container */}
              <div className="relative aspect-video bg-[#0a0d12] overflow-hidden">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={displayUrl}
                  alt={`Frame ${result.frame_index}`}
                  loading="lazy"
                  className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"
                />

                {/* Overlay hover icon */}
                <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                  <div className="w-9 h-9 rounded-full bg-white/20 backdrop-blur-sm flex items-center justify-center text-white">
                    <Maximize2 className="w-4 h-4" />
                  </div>
                </div>

                {/* Timestamp Pill */}
                <div className="absolute top-2 left-2 px-2 py-0.5 rounded bg-black/75 backdrop-blur-sm border border-white/10 text-[11px] font-mono text-[#e8edf5] flex items-center gap-1">
                  <Clock className="w-3 h-3 text-[#3b7dd8]" />
                  {formatTimestamp(result.timestamp_seconds)}
                </div>

                {/* Frame Index Pill */}
                <div className="absolute top-2 right-2 px-2 py-0.5 rounded bg-black/75 backdrop-blur-sm border border-white/10 text-[11px] font-mono text-[#8b96a8]">
                  #{result.frame_index}
                </div>

                {/* Detection Badge overlay at bottom */}
                <div className="absolute bottom-2 left-2">
                  {detectionCount > 0 ? (
                    <span className="px-2 py-0.5 rounded bg-[#0a192f]/90 border border-cyan-500/40 text-[11px] font-medium text-cyan-300 backdrop-blur-sm flex items-center gap-1">
                      <Target className="w-3 h-3 text-cyan-400" />
                      {detectionCount} {detectionCount === 1 ? 'Object' : 'Objects'} Detected
                    </span>
                  ) : (
                    <span className="px-2 py-0.5 rounded bg-black/60 border border-white/10 text-[10px] text-[#8b96a8] backdrop-blur-sm">
                      No Objects
                    </span>
                  )}
                </div>
              </div>

              {/* Card Meta */}
              <div className="p-3 bg-[#111620] border-t border-[#1e2736]/60 flex items-center justify-between text-xs text-[#8b96a8]">
                <span className="font-mono">
                  {result.width} × {result.height}
                </span>

                {result.processing_time_ms !== null && (
                  <span className="flex items-center gap-1 text-[11px] text-[#4e5a6b] font-mono">
                    <Cpu className="w-3 h-3" />
                    {result.processing_time_ms.toFixed(1)}ms
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Lightbox / Full Resolution Modal with Original vs AI Toggle */}
      {activeResult && activeModalIndex !== null && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/85 backdrop-blur-sm p-3 sm:p-4">
          <div className="relative w-full max-w-6xl bg-[#111620] border border-[#1e2736] rounded-xl overflow-hidden shadow-2xl flex flex-col max-h-[94vh]">
            {/* Modal Header */}
            <div className="flex items-center justify-between px-5 py-3.5 border-b border-[#1e2736] bg-[#0d1117]">
              <div className="flex items-center gap-3 flex-wrap">
                <span className="text-sm font-semibold text-[#e8edf5]">
                  Frame #{activeResult.frame_index}
                </span>
                <span className="text-xs font-mono text-[#3b7dd8] bg-[#3b7dd8]/10 px-2 py-0.5 rounded border border-[#3b7dd8]/20">
                  {formatTimestamp(activeResult.timestamp_seconds)}
                </span>
                <span className="text-xs text-[#8b96a8]">
                  {activeModalIndex + 1} of {filteredResults.length}
                </span>

                {/* View Mode Toggle: Original vs AI Detection View */}
                <div className="flex items-center bg-[#161c28] border border-[#1e2736] rounded-lg p-0.5 ml-2">
                  <button
                    type="button"
                    onClick={() => setViewMode('original')}
                    className={`px-2.5 py-1 text-xs font-medium rounded-md flex items-center gap-1.5 transition-colors ${
                      viewMode === 'original'
                        ? 'bg-[#111620] text-[#e8edf5] shadow-sm'
                        : 'text-[#8b96a8] hover:text-[#e8edf5]'
                    }`}
                  >
                    <Eye className="w-3 h-3" />
                    Original Frame
                  </button>

                  <button
                    type="button"
                    onClick={() => setViewMode('annotated')}
                    className={`px-2.5 py-1 text-xs font-medium rounded-md flex items-center gap-1.5 transition-colors ${
                      viewMode === 'annotated'
                        ? 'bg-[#3b7dd8] text-white shadow-sm'
                        : 'text-[#8b96a8] hover:text-[#e8edf5]'
                    }`}
                  >
                    <Sparkles className="w-3 h-3 text-cyan-300" />
                    AI Detection View
                  </button>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <a
                  href={getAuthenticatedFrameUrl(
                    viewMode === 'annotated' && activeResult.annotated_frame_url
                      ? activeResult.annotated_frame_url
                      : activeResult.frame_url
                  )}
                  target="_blank"
                  rel="noreferrer"
                  className="text-xs text-[#8b96a8] hover:text-[#e8edf5] p-1.5 rounded-lg border border-[#1e2736] hover:bg-[#161c28] transition-colors flex items-center gap-1"
                  title="Open full image in new tab"
                >
                  <ExternalLink className="w-3.5 h-3.5" />
                  <span className="hidden sm:inline">Raw File</span>
                </a>
                <button
                  type="button"
                  onClick={() => setActiveModalIndex(null)}
                  className="text-[#8b96a8] hover:text-[#e8edf5] p-1.5 rounded-lg hover:bg-[#161c28] transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>

            {/* Modal Body: Image display + Detections side/bottom inspector */}
            <div className="flex-1 flex flex-col lg:flex-row overflow-hidden min-h-[360px]">
              {/* Image Canvas Container */}
              <div className="relative flex-1 bg-[#0a0d12] flex items-center justify-center p-3 sm:p-4 overflow-hidden">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={getAuthenticatedFrameUrl(
                    viewMode === 'annotated' && activeResult.annotated_frame_url
                      ? activeResult.annotated_frame_url
                      : activeResult.frame_url
                  )}
                  alt={`Frame ${activeResult.frame_index}`}
                  className="max-h-[60vh] lg:max-h-[68vh] max-w-full object-contain rounded-lg shadow-md"
                />

                {/* View indicator badge */}
                <div className="absolute top-4 left-4 px-2.5 py-1 rounded bg-black/80 backdrop-blur-sm border border-white/10 text-xs font-mono text-[#e8edf5]">
                  {viewMode === 'annotated' ? (
                    <span className="flex items-center gap-1.5 text-cyan-300">
                      <Sparkles className="w-3 h-3" />
                      YOLO Detection Overlay
                    </span>
                  ) : (
                    <span className="flex items-center gap-1.5 text-[#8b96a8]">
                      <Eye className="w-3 h-3" />
                      Original Video Frame
                    </span>
                  )}
                </div>

                {/* Prev / Next controls */}
                {activeModalIndex > 0 && (
                  <button
                    type="button"
                    onClick={handlePrev}
                    className="absolute left-4 top-1/2 -translate-y-1/2 w-10 h-10 rounded-full bg-black/60 hover:bg-black/90 border border-white/10 text-white flex items-center justify-center backdrop-blur-sm transition-colors"
                  >
                    <ChevronLeft className="w-5 h-5" />
                  </button>
                )}

                {activeModalIndex < filteredResults.length - 1 && (
                  <button
                    type="button"
                    onClick={handleNext}
                    className="absolute right-4 top-1/2 -translate-y-1/2 w-10 h-10 rounded-full bg-black/60 hover:bg-black/90 border border-white/10 text-white flex items-center justify-center backdrop-blur-sm transition-colors"
                  >
                    <ChevronRight className="w-5 h-5" />
                  </button>
                )}
              </div>

              {/* Detections Inspector Sidebar */}
              <div className="w-full lg:w-80 bg-[#0d1117] border-t lg:border-t-0 lg:border-l border-[#1e2736] flex flex-col max-h-[30vh] lg:max-h-none overflow-hidden">
                <div className="p-3.5 border-b border-[#1e2736] flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Target className="w-4 h-4 text-cyan-400" />
                    <span className="text-xs font-semibold text-[#e8edf5] uppercase tracking-wider">
                      Frame Detections
                    </span>
                  </div>
                  <span className="text-xs font-mono px-2 py-0.5 rounded bg-[#161c28] border border-[#1e2736] text-[#e8edf5]">
                    {modalDetections.length} objects
                  </span>
                </div>

                {/* Detections list */}
                <div className="flex-1 overflow-y-auto p-3.5 space-y-2.5">
                  {isLoadingDetections ? (
                    <div className="py-8 text-center text-xs text-[#8b96a8]">
                      Loading detections...
                    </div>
                  ) : modalDetections.length === 0 ? (
                    <div className="py-8 text-center space-y-1">
                      <p className="text-xs font-medium text-[#e8edf5]">No objects detected</p>
                      <p className="text-[11px] text-[#4e5a6b]">
                        No objects in this frame met the confidence threshold.
                      </p>
                    </div>
                  ) : (
                    modalDetections.map((det, detIdx) => {
                      const confPct = Math.round(det.confidence * 100);
                      return (
                        <div
                          key={det.id || detIdx}
                          className="bg-[#111620] border border-[#1e2736] rounded-lg p-2.5 text-xs space-y-1.5"
                        >
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-1.5">
                              <span className="font-semibold text-[#e8edf5] uppercase tracking-wide">
                                {det.class_name}
                              </span>
                              {det.track_id !== undefined && det.track_id !== null && (
                                <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-cyan-500/20 text-cyan-300 border border-cyan-500/40">
                                  #{det.track_id}
                                </span>
                              )}
                            </div>
                            <span className="font-mono text-cyan-400 font-medium">
                              {confPct}%
                            </span>
                          </div>

                          <div className="text-[11px] text-[#8b96a8] font-mono grid grid-cols-2 gap-1 bg-[#0a0d12] p-1.5 rounded border border-[#1e2736]/40">
                            <span>
                              X: <strong className="text-[#e8edf5]">{det.bbox.x1}</strong>
                            </span>
                            <span>
                              Y: <strong className="text-[#e8edf5]">{det.bbox.y1}</strong>
                            </span>
                            <span>
                              W: <strong className="text-[#e8edf5]">{det.bbox.width}</strong>
                            </span>
                            <span>
                              H: <strong className="text-[#e8edf5]">{det.bbox.height}</strong>
                            </span>
                          </div>
                        </div>
                      );
                    })
                  )}
                </div>
              </div>
            </div>

            {/* Modal Footer Specs */}
            <div className="px-5 py-2.5 bg-[#0d1117] border-t border-[#1e2736] flex flex-wrap items-center justify-between text-xs text-[#8b96a8] gap-4">
              <div className="flex items-center gap-4">
                <span>
                  Resolution:{' '}
                  <strong className="text-[#e8edf5] font-mono">
                    {activeResult.width} × {activeResult.height}
                  </strong>
                </span>
                <span>
                  Extraction Latency:{' '}
                  <strong className="text-[#e8edf5] font-mono">
                    {activeResult.processing_time_ms?.toFixed(1) || '—'} ms
                  </strong>
                </span>
              </div>
              <p className="text-[11px] text-[#4e5a6b]">
                Use Left / Right arrow keys to navigate frames • Toggle Original / AI Detection View
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
