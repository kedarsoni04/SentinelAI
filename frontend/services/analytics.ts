import api from './api';
import type {
  ActivityHeatmapData,
  AnalyticsFilterParams,
  AnalyticsOverview,
  AnomalyDetectionData,
  CameraAnalyticsData,
  EventDistributionData,
  EventTrendsData,
  IncidentAnalyticsData,
  SecurityInsightsData,
  SeverityDistributionData,
} from '@/types';

/**
 * Builds query parameters string for analytics requests.
 */
function buildQueryParams(params?: AnalyticsFilterParams): Record<string, string> {
  const query: Record<string, string> = {};
  if (params?.preset) {
    query.preset = params.preset;
  }
  if (params?.start_date) {
    query.start_date = params.start_date;
  }
  if (params?.end_date) {
    query.end_date = params.end_date;
  }
  return query;
}

export async function getAnalyticsOverview(
  params?: AnalyticsFilterParams
): Promise<AnalyticsOverview> {
  const response = await api.get<AnalyticsOverview>('/api/analytics/overview', {
    params: buildQueryParams(params),
  });
  return response.data;
}

export async function getEventTrends(
  params?: AnalyticsFilterParams
): Promise<EventTrendsData> {
  const response = await api.get<EventTrendsData>('/api/analytics/events/trends', {
    params: buildQueryParams(params),
  });
  return response.data;
}

export async function getEventDistribution(
  params?: AnalyticsFilterParams
): Promise<EventDistributionData> {
  const response = await api.get<EventDistributionData>('/api/analytics/events/distribution', {
    params: buildQueryParams(params),
  });
  return response.data;
}

export async function getSeverityDistribution(
  params?: AnalyticsFilterParams
): Promise<SeverityDistributionData> {
  const response = await api.get<SeverityDistributionData>('/api/analytics/events/severity', {
    params: buildQueryParams(params),
  });
  return response.data;
}

export async function getCameraAnalytics(
  params?: AnalyticsFilterParams
): Promise<CameraAnalyticsData> {
  const response = await api.get<CameraAnalyticsData>('/api/analytics/cameras', {
    params: buildQueryParams(params),
  });
  return response.data;
}

export async function getActivityHeatmap(
  params?: AnalyticsFilterParams
): Promise<ActivityHeatmapData> {
  const response = await api.get<ActivityHeatmapData>('/api/analytics/activity', {
    params: buildQueryParams(params),
  });
  return response.data;
}

export async function getIncidentAnalytics(
  params?: AnalyticsFilterParams
): Promise<IncidentAnalyticsData> {
  const response = await api.get<IncidentAnalyticsData>('/api/analytics/incidents', {
    params: buildQueryParams(params),
  });
  return response.data;
}

export async function getAnomalies(
  params?: AnalyticsFilterParams
): Promise<AnomalyDetectionData> {
  const response = await api.get<AnomalyDetectionData>('/api/analytics/anomalies', {
    params: buildQueryParams(params),
  });
  return response.data;
}

export async function getSecurityInsights(
  params?: AnalyticsFilterParams
): Promise<SecurityInsightsData> {
  const response = await api.get<SecurityInsightsData>('/api/analytics/insights', {
    params: buildQueryParams(params),
  });
  return response.data;
}
