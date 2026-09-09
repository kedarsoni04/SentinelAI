'use client';

import React, { useEffect, useState, useCallback } from 'react';
import {
  Sliders,
  Plus,
  Trash2,
} from 'lucide-react';
import type { Camera, CreateSecurityRuleData, SecurityRule, SecurityZone } from '@/types';
import {
  getSecurityRules,
  createSecurityRule,
  toggleSecurityRuleStatus,
  deleteSecurityRule,
} from '@/services/securityRules';
import { getSecurityZones } from '@/services/securityZones';
import { getCameras } from '@/services/cameras';
import SecurityRuleModal from '@/components/security/SecurityRuleModal';
import EventSeverityBadge from '@/components/security/EventSeverityBadge';
import { Toast, useToast } from '@/components/ui/Toast';

export default function SecurityRulesPage() {
  const [rules, setRules] = useState<SecurityRule[]>([]);
  const [zones, setZones] = useState<SecurityZone[]>([]);
  const [cameras, setCameras] = useState<Camera[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const { toasts, showToast, dismissToast } = useToast();

  const loadData = useCallback(async () => {
    setIsLoading(true);
    try {
      const [rulesData, zonesData, camerasData] = await Promise.all([
        getSecurityRules(),
        getSecurityZones(),
        getCameras(),
      ]);
      setRules(rulesData);
      setZones(zonesData);
      setCameras(camerasData);
    } catch {
      setRules([]);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleCreateRule = async (data: CreateSecurityRuleData) => {
    await createSecurityRule(data);
    showToast('success', 'Security rule created successfully');
    loadData();
  };

  const handleToggle = async (ruleId: string, currentStatus: boolean) => {
    try {
      await toggleSecurityRuleStatus(ruleId, !currentStatus);
      setRules((prev) =>
        prev.map((r) => (r.id === ruleId ? { ...r, is_enabled: !currentStatus } : r))
      );
      showToast('success', `Rule ${!currentStatus ? 'enabled' : 'disabled'}`);
    } catch {
      showToast('error', 'Failed to update rule status');
    }
  };

  const handleDelete = async (ruleId: string) => {
    if (!confirm('Are you sure you want to delete this security rule?')) return;
    try {
      await deleteSecurityRule(ruleId);
      setRules((prev) => prev.filter((r) => r.id !== ruleId));
      showToast('success', 'Rule deleted successfully');
    } catch {
      showToast('error', 'Failed to delete rule');
    }
  };

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Toast notifications */}
      <Toast toasts={toasts} onDismiss={dismissToast} />

      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-xl font-semibold text-[#e8edf5]">Security Rules Configuration</h1>
          <p className="text-sm text-[#8b96a8] mt-1">
            Configure observable security conditions (zone intrusions, loitering limits, crowd counts, speed limits).
          </p>
        </div>

        <button
          type="button"
          onClick={() => setIsModalOpen(true)}
          className="px-3.5 py-1.5 rounded-lg bg-[#3b7dd8] hover:bg-[#2b6dc8] text-xs font-semibold text-white flex items-center gap-1.5 transition-colors shadow-sm"
        >
          <Plus className="w-4 h-4" />
          Create Rule
        </button>
      </div>

      {/* Rules Table / List */}
      {isLoading ? (
        <div className="bg-[#111620] border border-[#1e2736] rounded-xl p-12 text-center text-xs text-[#8b96a8]">
          Loading rules...
        </div>
      ) : rules.length === 0 ? (
        <div className="bg-[#111620] border border-[#1e2736] rounded-xl p-12 text-center space-y-3">
          <div className="w-12 h-12 rounded-full bg-[#3b7dd8]/10 border border-[#3b7dd8]/20 flex items-center justify-center text-[#3b7dd8] mx-auto">
            <Sliders className="w-6 h-6" />
          </div>
          <h3 className="text-sm font-semibold text-[#e8edf5]">No Security Rules Configured</h3>
          <p className="text-xs text-[#8b96a8] max-w-sm mx-auto">
            Create your first rule to begin monitoring zones for intrusions, loitering, and crowd densities.
          </p>
        </div>
      ) : (
        <div className="border border-[#1e2736] rounded-xl overflow-hidden bg-[#111620]">
          <table className="w-full text-left text-xs">
            <thead className="bg-[#0e131d] border-b border-[#1e2736] text-[#8b96a8] font-mono">
              <tr>
                <th className="py-3 px-4">Severity</th>
                <th className="py-3 px-4">Rule Name</th>
                <th className="py-3 px-4">Event Type</th>
                <th className="py-3 px-4">Target Zone</th>
                <th className="py-3 px-4">Thresholds</th>
                <th className="py-3 px-4">Scope</th>
                <th className="py-3 px-4">Active</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#1e2736]/60">
              {rules.map((rule) => (
                <tr key={rule.id} className="hover:bg-[#161c28] transition-colors">
                  <td className="py-3 px-4">
                    <EventSeverityBadge severity={rule.severity} />
                  </td>
                  <td className="py-3 px-4 font-semibold text-[#e8edf5]">
                    {rule.name}
                  </td>
                  <td className="py-3 px-4 font-mono text-cyan-400">
                    {rule.event_type}
                  </td>
                  <td className="py-3 px-4 text-[#8b96a8]">
                    {rule.zone_name ? (
                      <span className="text-[#e8edf5]">{rule.zone_name}</span>
                    ) : (
                      <span className="font-mono text-[11px] text-[#4e5a6b]">Global / Frame</span>
                    )}
                  </td>
                  <td className="py-3 px-4 font-mono text-[#8b96a8]">
                    {rule.threshold_seconds !== null && `${rule.threshold_seconds}s `}
                    {rule.threshold_value !== null && `${rule.threshold_value} units`}
                    {rule.threshold_seconds === null && rule.threshold_value === null && 'Boundary Entry'}
                  </td>
                  <td className="py-3 px-4 text-[#8b96a8]">
                    {rule.camera_name || 'All Cameras'}
                  </td>
                  <td className="py-3 px-4">
                    <button
                      type="button"
                      onClick={() => handleToggle(rule.id, rule.is_enabled)}
                      className={`w-7 h-4 rounded-full transition-colors relative ${
                        rule.is_enabled ? 'bg-emerald-500' : 'bg-[#1e2736]'
                      }`}
                    >
                      <span
                        className={`w-3 h-3 rounded-full bg-white absolute top-0.5 transition-transform ${
                          rule.is_enabled ? 'right-0.5' : 'left-0.5'
                        }`}
                      />
                    </button>
                  </td>
                  <td className="py-3 px-4 text-right">
                    <button
                      type="button"
                      onClick={() => handleDelete(rule.id)}
                      className="text-[#8b96a8] hover:text-red-400 transition-colors p-1"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Create Rule Modal */}
      {isModalOpen && (
        <SecurityRuleModal
          zones={zones}
          cameras={cameras}
          onSave={handleCreateRule}
          onClose={() => setIsModalOpen(false)}
        />
      )}
    </div>
  );
}
