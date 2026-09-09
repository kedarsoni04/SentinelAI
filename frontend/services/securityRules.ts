import api from './api';
import type {
  CreateSecurityRuleData,
  SecurityEventType,
  SecurityRule,
  UpdateSecurityRuleData,
} from '@/types';

/**
 * Retrieve all security rules for authenticated user with optional filters.
 */
export async function getSecurityRules(params?: {
  camera_id?: string;
  event_type?: SecurityEventType;
}): Promise<SecurityRule[]> {
  const response = await api.get<SecurityRule[]>('/api/security-rules', {
    params,
  });
  return response.data;
}

/**
 * Retrieve a single security rule by ID.
 */
export async function getSecurityRule(id: string): Promise<SecurityRule> {
  const response = await api.get<SecurityRule>(`/api/security-rules/${id}`);
  return response.data;
}

/**
 * Create a new security rule.
 */
export async function createSecurityRule(data: CreateSecurityRuleData): Promise<SecurityRule> {
  const response = await api.post<SecurityRule>('/api/security-rules', data);
  return response.data;
}

/**
 * Update a security rule.
 */
export async function updateSecurityRule(
  id: string,
  data: UpdateSecurityRuleData
): Promise<SecurityRule> {
  const response = await api.put<SecurityRule>(`/api/security-rules/${id}`, data);
  return response.data;
}

/**
 * Quick toggle security rule active status.
 */
export async function toggleSecurityRuleStatus(
  id: string,
  isEnabled: boolean
): Promise<SecurityRule> {
  const response = await api.patch<SecurityRule>(`/api/security-rules/${id}/status`, null, {
    params: { is_enabled: isEnabled },
  });
  return response.data;
}

/**
 * Delete a security rule.
 */
export async function deleteSecurityRule(id: string): Promise<void> {
  await api.delete(`/api/security-rules/${id}`);
}
