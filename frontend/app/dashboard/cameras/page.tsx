'use client';

import { useCallback, useEffect, useState } from 'react';
import { Camera, Plus, AlertTriangle, Loader2, RefreshCw } from 'lucide-react';
import type { Camera as CameraType, CameraStats, CreateCameraData, UpdateCameraData } from '@/types';
import {
  getCameras,
  createCamera,
  updateCamera,
  deleteCamera,
  updateCameraStatus,
} from '@/services/cameras';
import { extractErrorMessage } from '@/services/auth';
import CameraCard from '@/components/cameras/CameraCard';
import CameraFormModal from '@/components/cameras/CameraFormModal';
import DeleteConfirmModal from '@/components/cameras/DeleteConfirmModal';
import { Toast, useToast } from '@/components/ui/Toast';

type ModalState =
  | { type: 'none' }
  | { type: 'create' }
  | { type: 'edit'; camera: CameraType }
  | { type: 'delete'; camera: CameraType };

export default function CamerasPage() {
  const [cameras, setCameras] = useState<CameraType[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [modal, setModal] = useState<ModalState>({ type: 'none' });
  const [isDeleting, setIsDeleting] = useState(false);
  const { toasts, showToast, dismissToast } = useToast();

  // ─── Load Cameras ──────────────────────────────────────────────────────────

  const loadCameras = useCallback(async () => {
    setLoadError(null);
    try {
      const data = await getCameras();
      setCameras(data);
    } catch (err) {
      setLoadError(extractErrorMessage(err));
    }
  }, []);

  useEffect(() => {
    const init = async () => {
      setIsLoading(true);
      await loadCameras();
      setIsLoading(false);
    };
    init();
  }, [loadCameras]);

  // ─── Stats ─────────────────────────────────────────────────────────────────

  const stats: CameraStats = {
    total: cameras.length,
    enabled: cameras.filter((c) => c.is_enabled).length,
    disabled: cameras.filter((c) => !c.is_enabled).length,
    online: cameras.filter((c) => c.status === 'ONLINE').length,
  };

  // ─── Handlers ──────────────────────────────────────────────────────────────

  const handleCreate = async (data: CreateCameraData | UpdateCameraData) => {
    const created = await createCamera(data as CreateCameraData);
    setCameras((prev) => [created, ...prev]);
    setModal({ type: 'none' });
    showToast('success', `Camera "${created.name}" added successfully.`);
  };

  const handleEdit = async (data: CreateCameraData | UpdateCameraData) => {
    if (modal.type !== 'edit') return;
    const updated = await updateCamera(modal.camera.id, data as UpdateCameraData);
    setCameras((prev) => prev.map((c) => (c.id === updated.id ? updated : c)));
    setModal({ type: 'none' });
    showToast('success', `Camera "${updated.name}" updated successfully.`);
  };

  const handleDelete = async () => {
    if (modal.type !== 'delete') return;
    setIsDeleting(true);
    try {
      await deleteCamera(modal.camera.id);
      setCameras((prev) => prev.filter((c) => c.id !== modal.camera.id));
      showToast('success', `Camera "${modal.camera.name}" removed successfully.`);
      setModal({ type: 'none' });
    } catch (err) {
      showToast('error', extractErrorMessage(err));
    } finally {
      setIsDeleting(false);
    }
  };

  const handleToggle = async (camera: CameraType, enabled: boolean) => {
    try {
      const updated = await updateCameraStatus(camera.id, enabled);
      setCameras((prev) => prev.map((c) => (c.id === updated.id ? updated : c)));
      showToast('success', enabled ? `Camera "${camera.name}" enabled.` : `Camera "${camera.name}" disabled.`);
    } catch (err) {
      showToast('error', extractErrorMessage(err));
      throw err; // Let CameraCard revert its loading state
    }
  };

  // ─── Render ────────────────────────────────────────────────────────────────

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-xl font-semibold text-[#e8edf5]">Camera Management</h1>
          <p className="text-sm text-[#8b96a8] mt-1">
            Manage and configure your surveillance camera sources.
          </p>
        </div>
        <button
          onClick={() => setModal({ type: 'create' })}
          className="
            flex items-center gap-2 px-4 py-2 rounded-lg
            bg-[#3b7dd8] hover:bg-[#4d8fe8]
            text-sm font-medium text-white
            transition-colors duration-150 shrink-0
          "
        >
          <Plus className="w-4 h-4" />
          Add Camera
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {[
          { label: 'Total Cameras', value: stats.total, color: '#3b7dd8' },
          { label: 'Enabled',       value: stats.enabled,  color: '#22c55e' },
          { label: 'Disabled',      value: stats.disabled, color: '#f59e0b' },
          { label: 'Online',        value: stats.online,   color: '#22c55e' },
        ].map((stat) => (
          <div
            key={stat.label}
            className="bg-[#111620] border border-[#1e2736] rounded-xl px-4 py-3"
          >
            <p className="text-[10px] font-medium text-[#8b96a8] uppercase tracking-widest mb-1">
              {stat.label}
            </p>
            <p className="text-2xl font-semibold tabular-nums" style={{ color: stat.color }}>
              {stat.value}
            </p>
          </div>
        ))}
      </div>

      {/* Status note */}
      <div className="flex items-start gap-2.5 bg-[rgba(59,125,216,0.04)] border border-[rgba(59,125,216,0.12)] rounded-xl px-4 py-3">
        <Camera className="w-4 h-4 text-[#3b7dd8] mt-0.5 shrink-0" />
        <p className="text-xs text-[#8b96a8] leading-relaxed">
          <span className="text-[#3b7dd8] font-medium">Phase 2 — Camera Configuration.</span>{' '}
          Connection status monitoring and live feed processing will be available in Phase 3.
          All cameras added here are configuration records only — no stream connections are established.
        </p>
      </div>

      {/* Loading state */}
      {isLoading && (
        <div className="flex items-center justify-center py-20">
          <div className="flex flex-col items-center gap-3">
            <Loader2 className="w-7 h-7 text-[#3b7dd8] animate-spin" />
            <p className="text-sm text-[#8b96a8]">Loading cameras…</p>
          </div>
        </div>
      )}

      {/* Error state */}
      {!isLoading && loadError && (
        <div className="bg-[#111620] border border-[rgba(239,68,68,0.2)] rounded-xl p-6 text-center">
          <AlertTriangle className="w-8 h-8 text-[#ef4444] mx-auto mb-3" />
          <p className="text-sm font-medium text-[#e8edf5] mb-1">Unable to Load Cameras</p>
          <p className="text-xs text-[#8b96a8] mb-4">{loadError}</p>
          <button
            onClick={loadCameras}
            className="flex items-center gap-2 px-4 py-2 rounded-lg border border-[#1e2736] text-sm text-[#8b96a8] hover:text-[#e8edf5] hover:border-[#2a3748] transition-colors mx-auto"
          >
            <RefreshCw className="w-4 h-4" />
            Try Again
          </button>
        </div>
      )}

      {/* Empty state */}
      {!isLoading && !loadError && cameras.length === 0 && (
        <div className="bg-[#111620] border border-[#1e2736] border-dashed rounded-xl p-12 text-center">
          <div className="w-14 h-14 rounded-2xl bg-[rgba(59,125,216,0.08)] border border-[rgba(59,125,216,0.15)] flex items-center justify-center mx-auto mb-4">
            <Camera className="w-7 h-7 text-[#3b7dd8]" />
          </div>
          <p className="text-base font-semibold text-[#e8edf5] mb-1">No Cameras Configured</p>
          <p className="text-sm text-[#8b96a8] mb-6 max-w-xs mx-auto leading-relaxed">
            Start building your surveillance network by adding your first camera source.
          </p>
          <button
            onClick={() => setModal({ type: 'create' })}
            className="
              flex items-center gap-2 px-5 py-2.5 rounded-lg mx-auto
              bg-[#3b7dd8] hover:bg-[#4d8fe8]
              text-sm font-medium text-white
              transition-colors duration-150
            "
          >
            <Plus className="w-4 h-4" />
            Add Camera
          </button>
        </div>
      )}

      {/* Camera Grid */}
      {!isLoading && !loadError && cameras.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {cameras.map((camera) => (
            <CameraCard
              key={camera.id}
              camera={camera}
              onEdit={(cam) => setModal({ type: 'edit', camera: cam })}
              onDelete={(cam) => setModal({ type: 'delete', camera: cam })}
              onToggle={handleToggle}
            />
          ))}
        </div>
      )}

      {/* Modals */}
      {modal.type === 'create' && (
        <CameraFormModal
          mode="create"
          onSubmit={handleCreate}
          onClose={() => setModal({ type: 'none' })}
        />
      )}

      {modal.type === 'edit' && (
        <CameraFormModal
          mode="edit"
          camera={modal.camera}
          onSubmit={handleEdit}
          onClose={() => setModal({ type: 'none' })}
        />
      )}

      {modal.type === 'delete' && (
        <DeleteConfirmModal
          camera={modal.camera}
          onConfirm={handleDelete}
          onCancel={() => setModal({ type: 'none' })}
          isLoading={isDeleting}
        />
      )}

      {/* Toast Notifications */}
      <Toast toasts={toasts} onDismiss={dismissToast} />
    </div>
  );
}
