'use client';

import React, { useState } from 'react';
import { X, Save, AlertCircle } from 'lucide-react';
import type {
  Camera,
  CreateSecurityRuleData,
  SecurityEventSeverity,
  SecurityEventType,
  SecurityZone,
} from '@/types';

interface SecurityRuleModalProps {
  zones: SecurityZone[];
  cameras: Camera[];
  onSave: (data: CreateSecurityRuleData) => Promise<void>;
  onClose: () => void;
}

export default function SecurityRuleModal({
  zones,
  cameras,
  onSave,
  onClose,
}: SecurityRuleModalProps) {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [eventType, setEventType] = useState<SecurityEventType>('INTRUSION');
  const [severity, setSeverity] = useState<SecurityEventSeverity>('HIGH');
  const [zoneId, setZoneId] = useState<string>(zones[0]?.id || '');
  const [cameraId, setCameraId] = useState<string>('');
  const [thresholdSeconds, setThresholdSeconds] = useState<number>(15);
  const [thresholdValue, setThresholdValue] = useState<number>(25);
  const [crowdCount, setCrowdCount] = useState<number>(5);
  const [speedThreshold, setSpeedThreshold] = useState<number>(250);
  const [classFilter, setClassFilter] = useState<string>('person');
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleEventTypeChange = (newType: SecurityEventType) => {
    setEventType(newType);
    // Suggest appropriate default severities
    switch (newType) {
      case 'INTRUSION':
        setSeverity('HIGH');
        break;
      case 'LOITERING':
      case 'STATIONARY_OBJECT':
      case 'CROWD_DENSITY':
        setSeverity('MEDIUM');
        break;
      case 'UNUSUAL_MOVEMENT':
        setSeverity('LOW');
        break;
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) {
      setError('Please provide a rule name.');
      return;
    }

    // Zone requirement validation
    if (['INTRUSION', 'LOITERING', 'CROWD_DENSITY'].includes(eventType) && !zoneId) {
      setError(`Event type '${eventType}' requires an associated security zone.`);
      return;
    }

    let finalThreshVal: number | null = null;
    let finalThreshSec: number | null = null;

    if (eventType === 'LOITERING') {
      finalThreshSec = thresholdSeconds;
    } else if (eventType === 'STATIONARY_OBJECT') {
      finalThreshVal = thresholdValue;
      finalThreshSec = thresholdSeconds;
    } else if (eventType === 'CROWD_DENSITY') {
      finalThreshVal = crowdCount;
    } else if (eventType === 'UNUSUAL_MOVEMENT') {
      finalThreshVal = speedThreshold;
    }

    const classFiltersList = classFilter.trim()
      ? classFilter.split(',').map((s) => s.trim().toLowerCase()).filter(Boolean)
      : null;

    setIsSubmitting(true);
    try {
      await onSave({
        name: name.trim(),
        description: description.trim() || null,
        event_type: eventType,
        severity: severity,
        camera_id: cameraId || null,
        zone_id: zoneId || null,
        threshold_value: finalThreshVal,
        threshold_seconds: finalThreshSec,
        minimum_confidence: 0.5,
        class_filters: classFiltersList,
        is_enabled: true,
      });
      onClose();
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } };
      setError(e?.response?.data?.detail || 'Failed to save security rule.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
      <div className="bg-[#111620] border border-[#1e2736] rounded-xl max-w-lg w-full overflow-hidden shadow-2xl animate-in fade-in zoom-in-95 duration-150">
        <div className="p-4 border-b border-[#1e2736] flex items-center justify-between bg-[#0e131d]">
          <h3 className="text-sm font-semibold text-[#e8edf5]">Configure Security Rule</h3>
          <button
            type="button"
            onClick={onClose}
            className="text-[#8b96a8] hover:text-[#e8edf5] transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-4 space-y-4 text-xs">
          {error && (
            <div className="p-2.5 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <div>
            <label className="block text-[#8b96a8] mb-1">Rule Name *</label>
            <input
              type="text"
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Loading Bay Loitering"
              className="w-full px-3 py-1.5 rounded-lg bg-[#0e131d] border border-[#1e2736] text-[#e8edf5] focus:outline-none focus:border-[#3b7dd8]"
            />
          </div>

          <div>
            <label className="block text-[#8b96a8] mb-1">Description (Optional)</label>
            <input
              type="text"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Optional description of this security rule"
              className="w-full px-3 py-1.5 rounded-lg bg-[#0e131d] border border-[#1e2736] text-[#e8edf5] focus:outline-none focus:border-[#3b7dd8]"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-[#8b96a8] mb-1">Event Type *</label>
              <select
                value={eventType}
                onChange={(e) => handleEventTypeChange(e.target.value as SecurityEventType)}
                className="w-full px-3 py-1.5 rounded-lg bg-[#0e131d] border border-[#1e2736] text-[#e8edf5] focus:outline-none focus:border-[#3b7dd8]"
              >
                <option value="INTRUSION">Restricted Zone Intrusion</option>
                <option value="LOITERING">Loitering</option>
                <option value="STATIONARY_OBJECT">Stationary Object</option>
                <option value="CROWD_DENSITY">Crowd Density</option>
                <option value="UNUSUAL_MOVEMENT">Unusual Movement</option>
              </select>
            </div>

            <div>
              <label className="block text-[#8b96a8] mb-1">Operational Severity</label>
              <select
                value={severity}
                onChange={(e) => setSeverity(e.target.value as SecurityEventSeverity)}
                className="w-full px-3 py-1.5 rounded-lg bg-[#0e131d] border border-[#1e2736] text-[#e8edf5] focus:outline-none focus:border-[#3b7dd8]"
              >
                <option value="LOW">LOW</option>
                <option value="MEDIUM">MEDIUM</option>
                <option value="HIGH">HIGH</option>
                <option value="CRITICAL">CRITICAL</option>
              </select>
            </div>
          </div>

          {/* Conditional Zone Selector */}
          {['INTRUSION', 'LOITERING', 'CROWD_DENSITY'].includes(eventType) && (
            <div>
              <label className="block text-[#8b96a8] mb-1">Target Security Zone *</label>
              {zones.length === 0 ? (
                <p className="text-[11px] text-amber-400">
                  No security zones configured. Please create a zone first.
                </p>
              ) : (
                <select
                  value={zoneId}
                  onChange={(e) => setZoneId(e.target.value)}
                  required
                  className="w-full px-3 py-1.5 rounded-lg bg-[#0e131d] border border-[#1e2736] text-[#e8edf5] focus:outline-none focus:border-[#3b7dd8]"
                >
                  <option value="">Select a zone...</option>
                  {zones.map((z) => (
                    <option key={z.id} value={z.id}>
                      {z.name} ({z.zone_type})
                    </option>
                  ))}
                </select>
              )}
            </div>
          )}

          {/* Conditional Rule Thresholds */}
          {eventType === 'LOITERING' && (
            <div>
              <label className="block text-[#8b96a8] mb-1">Loitering Duration Threshold (Seconds)</label>
              <input
                type="number"
                min="1"
                value={thresholdSeconds}
                onChange={(e) => setThresholdSeconds(Number(e.target.value))}
                className="w-full px-3 py-1.5 rounded-lg bg-[#0e131d] border border-[#1e2736] text-[#e8edf5] focus:outline-none focus:border-[#3b7dd8]"
              />
            </div>
          )}

          {eventType === 'STATIONARY_OBJECT' && (
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-[#8b96a8] mb-1">Max Movement (Pixels)</label>
                <input
                  type="number"
                  min="1"
                  value={thresholdValue}
                  onChange={(e) => setThresholdValue(Number(e.target.value))}
                  className="w-full px-3 py-1.5 rounded-lg bg-[#0e131d] border border-[#1e2736] text-[#e8edf5] focus:outline-none focus:border-[#3b7dd8]"
                />
              </div>
              <div>
                <label className="block text-[#8b96a8] mb-1">Min Duration (Seconds)</label>
                <input
                  type="number"
                  min="1"
                  value={thresholdSeconds}
                  onChange={(e) => setThresholdSeconds(Number(e.target.value))}
                  className="w-full px-3 py-1.5 rounded-lg bg-[#0e131d] border border-[#1e2736] text-[#e8edf5] focus:outline-none focus:border-[#3b7dd8]"
                />
              </div>
            </div>
          )}

          {eventType === 'CROWD_DENSITY' && (
            <div>
              <label className="block text-[#8b96a8] mb-1">Crowd Person Count Threshold</label>
              <input
                type="number"
                min="2"
                value={crowdCount}
                onChange={(e) => setCrowdCount(Number(e.target.value))}
                className="w-full px-3 py-1.5 rounded-lg bg-[#0e131d] border border-[#1e2736] text-[#e8edf5] focus:outline-none focus:border-[#3b7dd8]"
              />
            </div>
          )}

          {eventType === 'UNUSUAL_MOVEMENT' && (
            <div>
              <label className="block text-[#8b96a8] mb-1">Image-Space Speed Threshold (Pixels / Sec)</label>
              <input
                type="number"
                min="10"
                value={speedThreshold}
                onChange={(e) => setSpeedThreshold(Number(e.target.value))}
                className="w-full px-3 py-1.5 rounded-lg bg-[#0e131d] border border-[#1e2736] text-[#e8edf5] focus:outline-none focus:border-[#3b7dd8]"
              />
            </div>
          )}

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-[#8b96a8] mb-1">Class Filter (Comma separated)</label>
              <input
                type="text"
                value={classFilter}
                onChange={(e) => setClassFilter(e.target.value)}
                placeholder="e.g. person, car"
                className="w-full px-3 py-1.5 rounded-lg bg-[#0e131d] border border-[#1e2736] text-[#e8edf5] focus:outline-none focus:border-[#3b7dd8]"
              />
            </div>
            <div>
              <label className="block text-[#8b96a8] mb-1">Scope to Camera (Optional)</label>
              <select
                value={cameraId}
                onChange={(e) => setCameraId(e.target.value)}
                className="w-full px-3 py-1.5 rounded-lg bg-[#0e131d] border border-[#1e2736] text-[#e8edf5] focus:outline-none focus:border-[#3b7dd8]"
              >
                <option value="">All Cameras &amp; Uploads</option>
                {cameras.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="flex items-center justify-end gap-2 pt-3 border-t border-[#1e2736]">
            <button
              type="button"
              onClick={onClose}
              className="px-3 py-1.5 rounded-lg bg-[#161c28] hover:bg-[#1e2736] text-[#8b96a8] transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-4 py-1.5 rounded-lg bg-[#3b7dd8] hover:bg-[#2b6dc8] font-semibold text-white transition-colors disabled:opacity-50 flex items-center gap-1.5"
            >
              <Save className="w-3.5 h-3.5" />
              {isSubmitting ? 'Saving...' : 'Save Rule'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
