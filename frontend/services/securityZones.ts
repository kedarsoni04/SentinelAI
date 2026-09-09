import api from './api';
import type {
  CreateSecurityZoneData,
  SecurityZone,
  UpdateSecurityZoneData,
} from '@/types';

/**
 * Retrieve all security zones for authenticated user with optional camera filter.
 */
export async function getSecurityZones(cameraId?: string): Promise<SecurityZone[]> {
  const response = await api.get<SecurityZone[]>('/api/security-zones', {
    params: cameraId ? { camera_id: cameraId } : undefined,
  });
  return response.data;
}

/**
 * Retrieve a single security zone by ID.
 */
export async function getSecurityZone(id: string): Promise<SecurityZone> {
  const response = await api.get<SecurityZone>(`/api/security-zones/${id}`);
  return response.data;
}

/**
 * Create a new geometric security zone.
 */
export async function createSecurityZone(data: CreateSecurityZoneData): Promise<SecurityZone> {
  const response = await api.post<SecurityZone>('/api/security-zones', data);
  return response.data;
}

/**
 * Update a security zone.
 */
export async function updateSecurityZone(
  id: string,
  data: UpdateSecurityZoneData
): Promise<SecurityZone> {
  const response = await api.put<SecurityZone>(`/api/security-zones/${id}`, data);
  return response.data;
}

/**
 * Quick toggle security zone active status.
 */
export async function toggleSecurityZoneStatus(
  id: string,
  isEnabled: boolean
): Promise<SecurityZone> {
  const response = await api.patch<SecurityZone>(`/api/security-zones/${id}/status`, null, {
    params: { is_enabled: isEnabled },
  });
  return response.data;
}

/**
 * Delete a security zone.
 */
export async function deleteSecurityZone(id: string): Promise<void> {
  await api.delete(`/api/security-zones/${id}`);
}
