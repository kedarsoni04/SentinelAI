import api from './api';
import type {
  EventMetrics,
  SecurityEvent,
  SecurityEventSeverity,
  SecurityEventStatus,
  SecurityEventType,
} from '@/types';

/**
 * Retrieve security events with optional filtering and pagination.
 */
export async function getSecurityEvents(params?: {
  event_type?: SecurityEventType;
  severity?: SecurityEventSeverity;
  status?: SecurityEventStatus;
  camera_id?: string;
  analysis_job_id?: string;
  limit?: number;
  offset?: number;
}): Promise<SecurityEvent[]> {
  const response = await api.get<SecurityEvent[]>('/api/security-events', {
    params,
  });
  return response.data;
}

/**
 * Retrieve SOC dashboard aggregated security event metrics.
 */
export async function getEventMetrics(): Promise<EventMetrics> {
  const response = await api.get<EventMetrics>('/api/security-events/metrics');
  return response.data;
}

/**
 * Retrieve a single security event by ID.
 */
export async function getSecurityEvent(id: string): Promise<SecurityEvent> {
  const response = await api.get<SecurityEvent>(`/api/security-events/${id}`);
  return response.data;
}

/**
 * Update event workflow status (OPEN, ACKNOWLEDGED, RESOLVED, DISMISSED).
 */
export async function updateSecurityEventStatus(
  id: string,
  status: SecurityEventStatus
): Promise<SecurityEvent> {
  const response = await api.patch<SecurityEvent>(`/api/security-events/${id}/status`, {
    status,
  });
  return response.data;
}

/**
 * Retrieve all events associated with a specific video analysis job.
 */
export async function getJobSecurityEvents(jobId: string): Promise<SecurityEvent[]> {
  const response = await api.get<SecurityEvent[]>(`/api/video-analysis/${jobId}/events`);
  return response.data;
}
