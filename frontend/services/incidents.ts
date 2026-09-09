import api from './api';
import type {
  CreateIncidentReportRequest,
  IncidentReport,
  IncidentReportListItem,
} from '@/types';

/**
 * Generate a new AI incident report from the given security event IDs.
 * Returns immediately with status=GENERATING. Poll getIncidentReport() until done.
 */
export async function createIncidentReport(
  data: CreateIncidentReportRequest
): Promise<IncidentReport> {
  const response = await api.post<IncidentReport>('/api/incidents', data);
  return response.data;
}

/**
 * List all incident reports for the authenticated user.
 */
export async function getIncidentReports(params?: {
  limit?: number;
  offset?: number;
}): Promise<IncidentReportListItem[]> {
  const response = await api.get<IncidentReportListItem[]>('/api/incidents', { params });
  return response.data;
}

/**
 * Retrieve a single incident report by ID.
 * If status=GENERATING, poll again in 2–3 seconds.
 */
export async function getIncidentReport(id: string): Promise<IncidentReport> {
  const response = await api.get<IncidentReport>(`/api/incidents/${id}`);
  return response.data;
}

/**
 * Permanently delete an incident report.
 */
export async function deleteIncidentReport(id: string): Promise<void> {
  await api.delete(`/api/incidents/${id}`);
}
