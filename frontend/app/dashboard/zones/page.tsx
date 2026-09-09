'use client';

import React, { useEffect, useState, useCallback } from 'react';
import {
  Maximize2,
  Plus,
  Trash2,
} from 'lucide-react';
import type { Camera as CameraType, CreateSecurityZoneData, SecurityZone } from '@/types';
import {
  getSecurityZones,
  createSecurityZone,
  deleteSecurityZone,
  toggleSecurityZoneStatus,
} from '@/services/securityZones';
import { getCameras } from '@/services/cameras';
import SecurityZoneEditor from '@/components/security/SecurityZoneEditor';
import { Toast, useToast } from '@/components/ui/Toast';

export default function SecurityZonesPage() {
  const [zones, setZones] = useState<SecurityZone[]>([]);
  const [cameras, setCameras] = useState<CameraType[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isEditorOpen, setIsEditorOpen] = useState(false);

  const { toasts, showToast, dismissToast } = useToast();

  const loadData = useCallback(async () => {
    setIsLoading(true);
    try {
      const [zonesData, camerasData] = await Promise.all([
        getSecurityZones(),
        getCameras(),
      ]);
      setZones(zonesData);
      setCameras(camerasData);
    } catch {
      setZones([]);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleCreateZone = async (data: CreateSecurityZoneData) => {
    await createSecurityZone(data);
    showToast('success', 'Security zone created successfully');
    setIsEditorOpen(false);
    loadData();
  };

  const handleToggle = async (zoneId: string, currentStatus: boolean) => {
    try {
      await toggleSecurityZoneStatus(zoneId, !currentStatus);
      setZones((prev) =>
        prev.map((z) => (z.id === zoneId ? { ...z, is_enabled: !currentStatus } : z))
      );
      showToast('success', `Zone ${!currentStatus ? 'enabled' : 'disabled'}`);
    } catch {
      showToast('error', 'Failed to update zone status');
    }
  };

  const handleDelete = async (zoneId: string) => {
    if (!confirm('Are you sure you want to delete this security zone?')) return;
    try {
      await deleteSecurityZone(zoneId);
      setZones((prev) => prev.filter((z) => z.id !== zoneId));
      showToast('success', 'Zone deleted successfully');
    } catch {
      showToast('error', 'Failed to delete zone');
    }
  };

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Toast notifications */}
      <Toast toasts={toasts} onDismiss={dismissToast} />

      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-xl font-semibold text-[#e8edf5]">Security Zones Configuration</h1>
          <p className="text-sm text-[#8b96a8] mt-1">
            Draw and define resolution-independent geometric zones (Restricted, Crowd, Monitoring).
          </p>
        </div>

        {!isEditorOpen && (
          <button
            type="button"
            onClick={() => setIsEditorOpen(true)}
            className="px-3.5 py-1.5 rounded-lg bg-[#3b7dd8] hover:bg-[#2b6dc8] text-xs font-semibold text-white flex items-center gap-1.5 transition-colors shadow-sm"
          >
            <Plus className="w-4 h-4" />
            Draw New Zone
          </button>
        )}
      </div>

      {/* Zone Editor if active */}
      {isEditorOpen && (
        <SecurityZoneEditor
          cameras={cameras}
          onSave={handleCreateZone}
          onCancel={() => setIsEditorOpen(false)}
        />
      )}

      {/* Existing Zones Grid */}
      {isLoading ? (
        <div className="bg-[#111620] border border-[#1e2736] rounded-xl p-12 text-center text-xs text-[#8b96a8]">
          Loading zones...
        </div>
      ) : zones.length === 0 && !isEditorOpen ? (
        <div className="bg-[#111620] border border-[#1e2736] rounded-xl p-12 text-center space-y-3">
          <div className="w-12 h-12 rounded-full bg-[#3b7dd8]/10 border border-[#3b7dd8]/20 flex items-center justify-center text-[#3b7dd8] mx-auto">
            <Maximize2 className="w-6 h-6" />
          </div>
          <h3 className="text-sm font-semibold text-[#e8edf5]">No Security Zones Configured</h3>
          <p className="text-xs text-[#8b96a8] max-w-sm mx-auto">
            Click &ldquo;Draw New Zone&rdquo; above to place polygon points and define monitored spatial areas.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {zones.map((zone) => (
            <div
              key={zone.id}
              className="bg-[#111620] border border-[#1e2736] rounded-xl p-4 flex flex-col justify-between space-y-3"
            >
              <div>
                <div className="flex items-center justify-between gap-2 mb-2">
                  <span
                    className={`px-2 py-0.5 rounded text-[10px] font-mono font-semibold uppercase ${
                      zone.zone_type === 'RESTRICTED'
                        ? 'bg-red-500/15 text-red-400 border border-red-500/30'
                        : 'bg-purple-500/15 text-purple-400 border border-purple-500/30'
                    }`}
                  >
                    {zone.zone_type}
                  </span>
                  <button
                    type="button"
                    onClick={() => handleToggle(zone.id, zone.is_enabled)}
                    className={`w-7 h-4 rounded-full transition-colors relative ${
                      zone.is_enabled ? 'bg-emerald-500' : 'bg-[#1e2736]'
                    }`}
                  >
                    <span
                      className={`w-3 h-3 rounded-full bg-white absolute top-0.5 transition-transform ${
                        zone.is_enabled ? 'right-0.5' : 'left-0.5'
                      }`}
                    />
                  </button>
                </div>

                <h4 className="text-sm font-semibold text-[#e8edf5]">{zone.name}</h4>
                {zone.description && (
                  <p className="text-xs text-[#8b96a8] mt-1 line-clamp-2">{zone.description}</p>
                )}
              </div>

              {/* Polygon preview thumbnail */}
              <div className="aspect-video w-full bg-[#0a0d13] border border-[#1e2736] rounded-lg overflow-hidden relative">
                <svg className="w-full h-full">
                  <polygon
                    points={zone.coordinates.map((p) => `${p.x * 100}%,${p.y * 100}%`).join(' ')}
                    className={
                      zone.zone_type === 'RESTRICTED'
                        ? 'fill-red-500/20 stroke-red-400 stroke-1'
                        : 'fill-purple-500/20 stroke-purple-400 stroke-1'
                    }
                  />
                  {zone.coordinates.map((p, idx) => (
                    <circle
                      key={idx}
                      cx={`${p.x * 100}%`}
                      cy={`${p.y * 100}%`}
                      r="2"
                      className="fill-cyan-400"
                    />
                  ))}
                </svg>
              </div>

              <div className="flex items-center justify-between text-xs text-[#8b96a8] border-t border-[#1e2736]/60 pt-2.5">
                <span className="font-mono">{zone.coordinates.length} vertices</span>
                <button
                  type="button"
                  onClick={() => handleDelete(zone.id)}
                  className="text-[#8b96a8] hover:text-red-400 transition-colors p-1"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
