import api from './api';
import { getBackendBaseUrl } from './realtime';
import { getStoredToken } from './auth';
import type {
  ActiveJobsCount,
  AnalysisJob,
  AnalysisResult,
  Detection,
  DetectionSummary,
  TrackDetail,
  TrackedObject,
  TrackingSummary,
  UploadResponse,
} from '@/types';
import { AxiosProgressEvent } from 'axios';

/**
 * Upload a surveillance video file with optional progress callback.
 */
export async function uploadVideo(
  file: File,
  onUploadProgress?: (progressEvent: AxiosProgressEvent) => void,
  cameraId?: string
): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append('file', file);
  if (cameraId) {
    formData.append('camera_id', cameraId);
  }

  const response = await api.post<UploadResponse>('/api/video-analysis/upload', formData, {
    headers: {
      'Content-Type': undefined, // Let Axios/browser automatically inject multipart boundary
    },
    timeout: 600000, // 10 minutes for large surveillance video uploads (up to 250MB)
    onUploadProgress,
  });
  return response.data;
}

/**
 * Retrieve all video analysis jobs belonging to the authenticated user.
 */
export async function getAnalysisJobs(): Promise<AnalysisJob[]> {
  const response = await api.get<AnalysisJob[]>('/api/video-analysis');
  return response.data;
}

/**
 * Retrieve a single analysis job by its ID.
 */
export async function getAnalysisJob(id: string): Promise<AnalysisJob> {
  const response = await api.get<AnalysisJob>(`/api/video-analysis/${id}`);
  return response.data;
}

/**
 * Retrieve extracted frame results for a completed or processing job.
 */
export async function getAnalysisResults(id: string): Promise<AnalysisResult[]> {
  const response = await api.get<AnalysisResult[]>(`/api/video-analysis/${id}/results`);
  return response.data;
}

/**
 * Cancel an active or queued analysis job.
 */
export async function cancelAnalysis(id: string): Promise<AnalysisJob> {
  const response = await api.patch<AnalysisJob>(`/api/video-analysis/${id}/cancel`);
  return response.data;
}

/**
 * Get active (queued + processing) analysis jobs count for the SOC dashboard.
 */
export async function getActiveJobsCount(): Promise<ActiveJobsCount> {
  const response = await api.get<ActiveJobsCount>('/api/video-analysis/active-count');
  return response.data;
}

/**
 * Get aggregated object detection summary statistics for an analysis job.
 */
export async function getDetectionSummary(jobId: string): Promise<DetectionSummary> {
  const response = await api.get<DetectionSummary>(`/api/video-analysis/${jobId}/detections/summary`);
  return response.data;
}

/**
 * Get detailed object detections and bounding boxes for a specific sampled frame.
 */
export async function getFrameDetections(jobId: string, resultId: string): Promise<Detection[]> {
  const response = await api.get<Detection[]>(`/api/video-analysis/${jobId}/results/${resultId}/detections`);
  return response.data;
}

/**
 * Constructs an authenticated absolute media URL for an extracted frame, thumbnail, or annotated frame.
 * Uses the direct backend URL (bypassing the Next.js proxy) because these URLs carry
 * the JWT as a query parameter and are used in <img> src attributes.
 */
export function getAuthenticatedFrameUrl(relativeUrl: string): string {
  const baseUrl = getBackendBaseUrl();
  const token = getStoredToken();
  const separator = relativeUrl.includes('?') ? '&' : '?';
  const tokenQuery = token ? `${separator}token=${encodeURIComponent(token)}` : '';
  return `${baseUrl}${relativeUrl}${tokenQuery}`;
}

// ─── Phase 5: Tracking & Temporal Intelligence ───────────────────────────────

/**
 * Retrieve object tracking summary statistics for a completed job.
 */
export async function getTrackingSummary(jobId: string): Promise<TrackingSummary> {
  const response = await api.get<TrackingSummary>(`/api/video-analysis/${jobId}/tracking/summary`);
  return response.data;
}

/**
 * List unique tracked objects for a job with optional class and duration filters.
 */
export async function getTrackedObjects(
  jobId: string,
  params?: { class_name?: string; min_duration?: number }
): Promise<TrackedObject[]> {
  const response = await api.get<TrackedObject[]>(`/api/video-analysis/${jobId}/tracks`, {
    params,
  });
  return response.data;
}

/**
 * Retrieve detailed temporal metadata, metrics, and trajectory points for a tracked object.
 */
export async function getTrackDetail(jobId: string, trackId: number): Promise<TrackDetail> {
  const response = await api.get<TrackDetail>(`/api/video-analysis/${jobId}/tracks/${trackId}`);
  return response.data;
}

