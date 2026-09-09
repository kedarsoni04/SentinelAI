'use client';

import React from 'react';
import {
  Target,
  Layers,
  Percent,
  User,
  Car,
  Tag,
  CheckCircle2,
} from 'lucide-react';
import type { DetectionSummary } from '@/types';

interface DetectionSummaryCardProps {
  summary: DetectionSummary;
  totalSampledFrames: number;
}

const VEHICLE_CLASSES = new Set(['car', 'motorcycle', 'bus', 'truck', 'bicycle']);

export default function DetectionSummaryCard({
  summary,
  totalSampledFrames,
}: DetectionSummaryCardProps) {
  // If no detections were made in the video
  if (summary.total_detections === 0) {
    return (
      <div className="bg-[#111620] border border-[#1e2736] rounded-xl p-6 flex items-start gap-4">
        <div className="w-10 h-10 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400 shrink-0">
          <CheckCircle2 className="w-5 h-5" />
        </div>
        <div>
          <h3 className="text-sm font-semibold text-[#e8edf5]">
            No Objects Detected
          </h3>
          <p className="text-xs text-[#8b96a8] mt-1 leading-relaxed">
            The AI analysis completed successfully across {totalSampledFrames} sampled frames, but
            no configured object classes (e.g. persons, vehicles) met the confidence threshold.
          </p>
        </div>
      </div>
    );
  }

  // Calculate grouped categories dynamically
  let personCount = 0;
  let vehicleCount = 0;
  let otherCount = 0;

  Object.entries(summary.class_counts).forEach(([cls, count]) => {
    const c = cls.toLowerCase();
    if (c === 'person') {
      personCount += count;
    } else if (VEHICLE_CLASSES.has(c)) {
      vehicleCount += count;
    } else {
      otherCount += count;
    }
  });

  const framePct =
    totalSampledFrames > 0
      ? Math.round((summary.frames_with_detections / totalSampledFrames) * 100)
      : 0;

  return (
    <div className="bg-[#111620] border border-[#1e2736] rounded-xl overflow-hidden space-y-6 p-5">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-[#1e2736] pb-4">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-[#3b7dd8]/10 border border-[#3b7dd8]/20 flex items-center justify-center text-[#3b7dd8]">
            <Target className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-[#e8edf5]">
              YOLO Object Detection Intelligence
            </h3>
            <p className="text-xs text-[#8b96a8]">
              Automated computer vision inferences across sampled video frames
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-[11px] font-mono px-2.5 py-1 rounded bg-[#161c28] border border-[#1e2736] text-[#8b96a8]">
            Model: <strong className="text-[#e8edf5]">YOLOv11</strong>
          </span>
        </div>
      </div>

      {/* 4 Metrics Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <div className="bg-[#0e131d] border border-[#1e2736] rounded-lg p-3.5">
          <div className="flex items-center justify-between text-xs text-[#8b96a8] mb-1">
            <span>Total Detections</span>
            <Target className="w-3.5 h-3.5 text-[#3b7dd8]" />
          </div>
          <p className="text-xl font-bold font-mono text-[#e8edf5]">
            {summary.total_detections.toLocaleString()}
          </p>
          <span className="text-[11px] text-[#4e5a6b]">Across all sampled frames</span>
        </div>

        <div className="bg-[#0e131d] border border-[#1e2736] rounded-lg p-3.5">
          <div className="flex items-center justify-between text-xs text-[#8b96a8] mb-1">
            <span>Frames with Objects</span>
            <Layers className="w-3.5 h-3.5 text-emerald-400" />
          </div>
          <p className="text-xl font-bold font-mono text-[#e8edf5]">
            {summary.frames_with_detections}{' '}
            <span className="text-xs text-[#8b96a8] font-normal">/ {totalSampledFrames}</span>
          </p>
          <span className="text-[11px] text-emerald-400 font-mono">{framePct}% frame coverage</span>
        </div>

        <div className="bg-[#0e131d] border border-[#1e2736] rounded-lg p-3.5">
          <div className="flex items-center justify-between text-xs text-[#8b96a8] mb-1">
            <span>Unique Classes</span>
            <Tag className="w-3.5 h-3.5 text-amber-400" />
          </div>
          <p className="text-xl font-bold font-mono text-[#e8edf5]">
            {summary.unique_classes}
          </p>
          <span className="text-[11px] text-[#4e5a6b]">Distinct categories</span>
        </div>

        <div className="bg-[#0e131d] border border-[#1e2736] rounded-lg p-3.5">
          <div className="flex items-center justify-between text-xs text-[#8b96a8] mb-1">
            <span>Avg Confidence</span>
            <Percent className="w-3.5 h-3.5 text-[#3b7dd8]" />
          </div>
          <p className="text-xl font-bold font-mono text-[#e8edf5]">
            {Math.round(summary.average_confidence * 100)}%
          </p>
          <span className="text-[11px] text-[#4e5a6b]">Mean prediction score</span>
        </div>
      </div>

      {/* Category Grouping Badges */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <div className="bg-[#161c28] border border-[#1e2736] rounded-lg p-3 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded bg-[#3b7dd8]/10 text-[#3b7dd8] flex items-center justify-center">
              <User className="w-4 h-4" />
            </div>
            <div>
              <p className="text-xs font-medium text-[#e8edf5]">Persons</p>
              <p className="text-[10px] text-[#8b96a8]">Human entities</p>
            </div>
          </div>
          <span className="text-sm font-bold font-mono text-[#e8edf5] bg-[#111620] px-2.5 py-1 rounded border border-[#1e2736]">
            {personCount}
          </span>
        </div>

        <div className="bg-[#161c28] border border-[#1e2736] rounded-lg p-3 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded bg-amber-500/10 text-amber-400 flex items-center justify-center">
              <Car className="w-4 h-4" />
            </div>
            <div>
              <p className="text-xs font-medium text-[#e8edf5]">Vehicles</p>
              <p className="text-[10px] text-[#8b96a8]">Cars, trucks, bikes</p>
            </div>
          </div>
          <span className="text-sm font-bold font-mono text-[#e8edf5] bg-[#111620] px-2.5 py-1 rounded border border-[#1e2736]">
            {vehicleCount}
          </span>
        </div>

        <div className="bg-[#161c28] border border-[#1e2736] rounded-lg p-3 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded bg-emerald-500/10 text-emerald-400 flex items-center justify-center">
              <Tag className="w-4 h-4" />
            </div>
            <div>
              <p className="text-xs font-medium text-[#e8edf5]">Other Objects</p>
              <p className="text-[10px] text-[#8b96a8]">Configured classes</p>
            </div>
          </div>
          <span className="text-sm font-bold font-mono text-[#e8edf5] bg-[#111620] px-2.5 py-1 rounded border border-[#1e2736]">
            {otherCount}
          </span>
        </div>
      </div>

      {/* Dynamic Class Breakdown List */}
      <div className="space-y-2.5 pt-2">
        <h4 className="text-xs font-semibold text-[#4e5a6b] uppercase tracking-wider">
          Class Breakdown
        </h4>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2.5">
          {Object.entries(summary.class_counts).map(([cls, count]) => {
            const pct = Math.round((count / summary.total_detections) * 100);
            return (
              <div
                key={cls}
                className="bg-[#0e131d] border border-[#1e2736] rounded-lg p-2.5 flex flex-col justify-between gap-1.5"
              >
                <div className="flex items-center justify-between text-xs">
                  <span className="font-medium text-[#e8edf5] capitalize">{cls}</span>
                  <span className="font-mono text-[#8b96a8]">
                    <strong className="text-[#e8edf5]">{count}</strong> ({pct}%)
                  </span>
                </div>
                <div className="w-full bg-[#161c28] rounded-full h-1.5 overflow-hidden">
                  <div
                    className="bg-[#3b7dd8] h-full rounded-full transition-all duration-300"
                    style={{ width: `${pct}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
