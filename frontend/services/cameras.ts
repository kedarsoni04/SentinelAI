import api from './api';
import { extractErrorMessage } from './auth';
import type { Camera, CreateCameraData, UpdateCameraData, CameraStatusUpdate } from '@/types';

// ─── Camera API Calls ─────────────────────────────────────────────────────────

/**
 * Fetch all configured cameras.
 * Returns newest first (as ordered by the backend).
 */
export async function getCameras(): Promise<Camera[]> {
  const response = await api.get<Camera[]>('/api/cameras');
  return response.data;
}

/**
 * Fetch a single camera by ID.
 */
export async function getCamera(id: string): Promise<Camera> {
  const response = await api.get<Camera>(`/api/cameras/${id}`);
  return response.data;
}

/**
 * Create a new camera configuration.
 */
export async function createCamera(data: CreateCameraData): Promise<Camera> {
  const response = await api.post<Camera>('/api/cameras', data);
  return response.data;
}

/**
 * Update an existing camera's configuration.
 * Only provided fields are updated (partial update).
 */
export async function updateCamera(id: string, data: UpdateCameraData): Promise<Camera> {
  const response = await api.put<Camera>(`/api/cameras/${id}`, data);
  return response.data;
}

/**
 * Permanently delete a camera.
 */
export async function deleteCamera(id: string): Promise<void> {
  await api.delete(`/api/cameras/${id}`);
}

/**
 * Enable or disable a camera without deleting it.
 */
export async function updateCameraStatus(id: string, is_enabled: boolean): Promise<Camera> {
  const response = await api.patch<Camera>(`/api/cameras/${id}/status`, { is_enabled });
  return response.data;
}

// Re-export for convenience
export { extractErrorMessage };
