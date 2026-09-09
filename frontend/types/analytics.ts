export type DateRangePreset = '24h' | '7d' | '30d' | '90d' | 'custom';

export type AnomalyType =
  | 'EVENT_VOLUME_SPIKE'
  | 'SEVERITY_SPIKE'
  | 'CAMERA_ACTIVITY_SPIKE'
  | 'UNUSUAL_TIME_ACTIVITY';

export type AnomalySeverity = 'INFO' | 'LOW' | 'MEDIUM' | 'HIGH';

export type InsightType =
  | 'TOP_CAMERA'
  | 'TOP_EVENT_TYPE'
  | 'PEAK_ACTIVITY_TIME'
  | 'SEVERITY_TREND'
  | 'CAMERA_RISK'
  | 'ANOMALY';

export type InsightPriority = 'INFO' | 'LOW' | 'MEDIUM' | 'HIGH';

export interface AnalyticsFilterParams {
  preset?: DateRangePreset;
  start_date?: string;
  end_date?: string;
}

export interface AnalyticsOverview {
  total_events: number;
  total_incidents: number;
  high_severity_events: number;
  critical_events: number;
  resolved_incidents: number;
  active_cameras: number;
  event_change_percentage: number | null;
  incident_change_percentage: number | null;
  period_start: string;
  period_end: string;
  comparison_period_start: string | null;
  comparison_period_end: string | null;
}

export interface EventTrendItem {
  timestamp: string;
  label: string;
  total: number;
  low: number;
  medium: number;
  high: number;
  critical: number;
}

export interface EventTrendsData {
  interval: 'hourly' | 'daily' | 'weekly';
  total_events: number;
  data: EventTrendItem[];
}

export interface DistributionItem {
  name: string;
  count: number;
  percentage: number;
}

export interface EventDistributionData {
  total: number;
  items: DistributionItem[];
}

export interface SeverityDistributionItem {
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  count: number;
  percentage: number;
}

export interface SeverityDistributionData {
  total: number;
  items: SeverityDistributionItem[];
}

export interface CameraAnalyticsItem {
  camera_id: string;
  camera_name: string;
  location: string;
  status: string;
  is_enabled: boolean;
  total_events: number;
  high_severity_events: number;
  critical_events: number;
  incidents: number;
  avg_events_per_day: number;
  most_common_event_type: string | null;
  last_activity: string | null;
  risk_score: number;
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  risk_factors: string[];
}

export interface CameraAnalyticsData {
  total_cameras: number;
  most_active_camera: string | null;
  highest_risk_camera: string | null;
  cameras: CameraAnalyticsItem[];
}

export interface HeatmapCell {
  day: number; // 0=Monday, 6=Sunday
  day_name: string;
  hour: number; // 0-23
  count: number;
}

export interface ActivityHeatmapData {
  cells: HeatmapCell[];
  peak_hour: number | null;
  peak_day: string | null;
  quiet_hours: number[];
  total_events: number;
}

export interface IncidentAnalyticsData {
  total_incidents: number;
  by_status: Record<string, number>;
  by_risk_level: Record<string, number>;
  resolved_count: number;
  resolution_rate: number;
  average_resolution_time_minutes: number | null;
}

export interface AnomalyItem {
  id: string;
  type: AnomalyType;
  severity: AnomalySeverity;
  title: string;
  description: string;
  observed_value: number;
  baseline_value: number;
  deviation_percentage: number;
  detected_at: string;
  why_flagged: string;
  camera_id?: string | null;
  camera_name?: string | null;
}

export interface AnomalyDetectionData {
  has_sufficient_data: boolean;
  status: 'INSUFFICIENT_DATA' | 'NORMAL' | 'ANOMALIES_DETECTED';
  message: string;
  anomalies: AnomalyItem[];
  total_anomalies: number;
}

export interface SecurityInsightItem {
  id: string;
  type: InsightType;
  priority: InsightPriority;
  title: string;
  description: string;
  related_entity?: string | null;
}

export interface SecurityInsightsData {
  insights: SecurityInsightItem[];
  total_insights: number;
}
