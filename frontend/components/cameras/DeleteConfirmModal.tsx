'use client';

import { AlertTriangle, Loader2 } from 'lucide-react';
import type { Camera } from '@/types';

interface DeleteConfirmModalProps {
  camera: Camera;
  onConfirm: () => Promise<void>;
  onCancel: () => void;
  isLoading: boolean;
}

/**
 * DeleteConfirmModal — requires explicit user confirmation before deleting a camera.
 * Never deletes immediately on first click.
 */
export default function DeleteConfirmModal({
  camera,
  onConfirm,
  onCancel,
  isLoading,
}: DeleteConfirmModalProps) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={!isLoading ? onCancel : undefined}
      />

      {/* Modal */}
      <div className="relative w-full max-w-sm bg-[#111620] border border-[#1e2736] rounded-xl shadow-2xl shadow-black/60 p-6">
        {/* Icon */}
        <div className="w-12 h-12 rounded-xl bg-[rgba(239,68,68,0.08)] border border-[rgba(239,68,68,0.15)] flex items-center justify-center mb-4">
          <AlertTriangle className="w-5 h-5 text-[#ef4444]" />
        </div>

        <h2 className="text-base font-semibold text-[#e8edf5] mb-1">Delete Camera?</h2>
        <p className="text-sm text-[#8b96a8] leading-relaxed mb-1">
          Are you sure you want to remove{' '}
          <span className="font-medium text-[#e8edf5]">&quot;{camera.name}&quot;</span>?
        </p>
        <p className="text-xs text-[#4e5a6b] mb-6">
          This action cannot be undone. All configuration for this camera will be permanently deleted.
        </p>

        <div className="flex gap-3">
          <button
            onClick={onCancel}
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
            onClick={onConfirm}
            disabled={isLoading}
            className="
              flex-1 h-10 rounded-lg
              bg-[#ef4444] hover:bg-[#dc2626]
              text-sm font-medium text-white
              flex items-center justify-center gap-2
              transition-colors duration-150 disabled:opacity-60
            "
          >
            {isLoading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Deleting…
              </>
            ) : (
              'Delete Camera'
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
