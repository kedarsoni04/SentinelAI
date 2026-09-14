// ─── User Types ──────────────────────────────────────────────────────────────

export type UserRole = 'ADMIN' | 'SECURITY_OPERATOR' | 'VIEWER';

export interface User {
  id: string;
  name: string;
  email: string;
  role: UserRole;
  created_at: string;
}

// ─── Auth Types ───────────────────────────────────────────────────────────────

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  name: string;
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: User;
}

// ─── API Error Types ──────────────────────────────────────────────────────────

export interface ApiError {
  detail: string | ValidationError[];
}

export interface ValidationError {
  loc: (string | number)[];
  msg: string;
  type: string;
}

// ─── Auth State ───────────────────────────────────────────────────────────────

export interface AuthState {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
}

// ─── Camera Types ─────────────────────────────────────────────────────────────

export type CameraSourceType = 'WEBCAM' | 'RTSP' | 'HTTP_STREAM' | 'VIDEO_FILE';

export type CameraStatus = 'ONLINE' | 'OFFLINE' | 'UNKNOWN';

export interface Camera {
  id: string;
  name: string;
  location: string;
  stream_url: string | null;
  source_type: CameraSourceType;
  status: CameraStatus;
  is_enabled: boolean;
  created_at: string;
  updated_at: string;
  last_active: string | null;
}

export interface CreateCameraData {
  name: string;
  location: string;
  stream_url?: string | null;
  source_type: CameraSourceType;
  is_enabled: boolean;
}

export interface UpdateCameraData {
  name?: string;
  location?: string;
  stream_url?: string | null;
  source_type?: CameraSourceType;
  status?: CameraStatus;
  is_enabled?: boolean;
}

export interface CameraStatusUpdate {
  is_enabled: boolean;
}

export interface CameraStats {
  total: number;
  enabled: number;
  disabled: number;
  online: number;
}

// ─── Video Analysis Types (Phase 3) ──────────────────────────────────────────

export type JobStatus = 'QUEUED' | 'PROCESSING' | 'COMPLETED' | 'FAILED' | 'CANCELLED';

export interface AnalysisJob {
  id: string;
  user_id: string;
  camera_id: string | null;
  source_type: string;
  original_filename: string;
  status: JobStatus;
  progress: number;
  duration_seconds: number | null;
  fps: number | null;
  frame_count: number | null;
  width: number | null;
  height: number | null;
  sampled_frames: number;
  processed_frames: number;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
  error_message: string | null;
  camera?: Camera | null;
}

export interface AnalysisResult {
  id: string;
  analysis_job_id: string;
  frame_index: number;
  timestamp_seconds: number;
  frame_url: string;
  thumbnail_url: string | null;
  annotated_frame_url?: string | null;
  detection_count?: number;
  width: number;
  height: number;
  processing_time_ms: number | null;
  created_at: string;
}

export interface UploadResponse {
  id: string;
  status: JobStatus;
  original_filename: string;
  progress: number;
  message: string;
}

export interface ActiveJobsCount {
  active_jobs: number;
  queued: number;
  processing: number;
}

// ─── Phase 4 Detection Types ────────────────────────────────────────────────

export interface BoundingBox {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
  width: number;
  height: number;
}

export interface Detection {
  id: string;
  class_id: number;
  class_name: string;
  confidence: number;
  bbox: BoundingBox;
  track_id?: number | null;
}

export interface DetectionSummary {
  total_detections: number;
  frames_with_detections: number;
  unique_classes: number;
  average_confidence: number;
  class_counts: Record<string, number>;
}

// ─── Phase 5 Object Tracking & Temporal Intelligence Types ───────────────────

export interface TrackPoint {
  frame_index: number;
  timestamp_seconds: number;
  center_x: number;
  center_y: number;
  x1: number;
  y1: number;
  x2: number;
  y2: number;
  confidence: number;
}

export interface TrackedObject {
  id: string;
  track_id: number;
  class_id: number;
  class_name: string;
  first_seen_timestamp: number;
  last_seen_timestamp: number;
  duration_seconds: number;
  first_seen_frame: number;
  last_seen_frame: number;
  total_frames: number;
  average_confidence: number;
  max_confidence: number;
}

export interface TrackDetail extends TrackedObject {
  displacement_pixels: number;
  trajectory_distance_pixels: number;
  trajectory: TrackPoint[];
}

export interface TrackingSummary {
  total_tracked_objects: number;
  tracked_persons: number;
  tracked_vehicles: number;
  longest_track_duration_seconds: number;
  average_track_duration_seconds: number;
  average_observations_per_track: number;
  most_frequently_tracked_class: string | null;
}

// ─── Phase 6 Security Event Detection & Incident Intelligence ───────────────

export type ZoneType = 'RESTRICTED' | 'CROWD' | 'MONITORING';

export interface CoordinatePoint {
  x: number;
  y: number;
}

export interface SecurityZone {
  id: string;
  user_id: string;
  camera_id: string | null;
  camera_name?: string | null;
  name: string;
  description: string | null;
  zone_type: ZoneType;
  coordinates: CoordinatePoint[];
  is_enabled: boolean;
  created_at: string;
  updated_at: string;
}

export interface CreateSecurityZoneData {
  name: string;
  description?: string | null;
  camera_id?: string | null;
  zone_type: ZoneType;
  coordinates: CoordinatePoint[];
  is_enabled: boolean;
}

export interface UpdateSecurityZoneData {
  name?: string;
  description?: string | null;
  camera_id?: string | null;
  zone_type?: ZoneType;
  coordinates?: CoordinatePoint[];
  is_enabled?: boolean;
}

export type SecurityEventType =
  | 'INTRUSION'
  | 'LOITERING'
  | 'STATIONARY_OBJECT'
  | 'CROWD_DENSITY'
  | 'UNUSUAL_MOVEMENT';

export type SecurityEventSeverity = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';

export type SecurityEventStatus = 'OPEN' | 'ACKNOWLEDGED' | 'RESOLVED' | 'DISMISSED';

export interface SecurityRule {
  id: string;
  user_id: string;
  camera_id: string | null;
  camera_name?: string | null;
  zone_id: string | null;
  zone_name?: string | null;
  name: string;
  description: string | null;
  event_type: SecurityEventType;
  severity: SecurityEventSeverity;
  is_enabled: boolean;
  threshold_value: number | null;
  threshold_seconds: number | null;
  minimum_confidence: number | null;
  class_filters: string[] | null;
  created_at: string;
  updated_at: string;
}

export interface CreateSecurityRuleData {
  name: string;
  description?: string | null;
  event_type: SecurityEventType;
  severity: SecurityEventSeverity;
  camera_id?: string | null;
  zone_id?: string | null;
  threshold_value?: number | null;
  threshold_seconds?: number | null;
  minimum_confidence?: number | null;
  class_filters?: string[] | null;
  is_enabled: boolean;
}

export interface UpdateSecurityRuleData {
  name?: string;
  description?: string | null;
  severity?: SecurityEventSeverity;
  camera_id?: string | null;
  zone_id?: string | null;
  threshold_value?: number | null;
  threshold_seconds?: number | null;
  minimum_confidence?: number | null;
  class_filters?: string[] | null;
  is_enabled?: boolean;
}

export interface SecurityEvent {
  id: string;
  analysis_job_id: string;
  camera_id: string | null;
  camera_name?: string | null;
  rule_id: string | null;
  rule_name?: string | null;
  tracked_object_id: string | null;
  track_id: number | null;
  class_name: string | null;
  event_type: SecurityEventType;
  severity: SecurityEventSeverity;
  status: SecurityEventStatus;
  title: string;
  description: string;
  start_timestamp: number;
  end_timestamp: number | null;
  duration_seconds: number | null;
  confidence: number | null;
  evidence_frame_id: string | null;
  evidence_frame_url: string | null;
  annotated_frame_url: string | null;
  metadata_json: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

export interface EventMetrics {
  total_events: number;
  open_events: number;
  high_severity_events: number;
  medium_severity_events: number;
  low_severity_events: number;
  events_today: number;
  by_type: Record<string, number>;
}

// ─── Real-Time Monitoring & SOC Operations Types (Phase 7) ───────────────────

export type RealtimeStatus =
  | 'CREATED'
  | 'STARTING'
  | 'RUNNING'
  | 'PAUSED'
  | 'STOPPING'
  | 'COMPLETED'
  | 'FAILED'
  | 'STOPPED';

export type ConnectionStatus = 'LIVE' | 'RECONNECTING' | 'OFFLINE';

export interface ActiveTrackInfo {
  track_id: number;
  class_name: string;
  confidence: number;
  duration_seconds: number;
}

export interface RealtimeSessionMetrics {
  job_id: string;
  user_id: string;
  camera_id?: string | null;
  camera_name?: string | null;
  status: RealtimeStatus;
  start_time?: string | null;
  end_time?: string | null;
  current_timestamp: number;
  frames_processed: number;
  processing_fps: number;
  active_tracks: number;
  active_tracks_list: ActiveTrackInfo[];
  events_detected: number;
  last_heartbeat: string;
  latest_frame_index?: number | null;
  error_message?: string | null;
}

export type RealtimeMessageType =
  | 'security_event'
  | 'event_updated'
  | 'status_update'
  | 'heartbeat'
  | 'error';

export interface RealtimeMessage {
  type: RealtimeMessageType;
  data: Record<string, unknown>;
  job_id?: string;
  timestamp: string;
}

export interface NotificationPreferences {
  desktop_notifications: boolean;
  alert_sound: boolean;
  min_severity: SecurityEventSeverity;
}

// ─── Phase 8: AI Incident Intelligence Types ──────────────────────────────────

export type IncidentReportStatus = 'GENERATING' | 'COMPLETED' | 'FAILED';

export type IncidentRiskLevel = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';

export interface IncidentTimelineItem {
  timestamp_label: string;
  event_type: string;
  description: string;
}

export interface IncidentReport {
  id: string;
  user_id: string;
  analysis_job_id: string | null;
  camera_id: string | null;
  camera_name?: string | null;
  event_ids: string[];
  event_count: number;
  ai_provider: string;
  ai_model: string | null;
  prompt_tokens: number | null;
  summary: string | null;
  timeline: IncidentTimelineItem[] | null;
  risk_level: IncidentRiskLevel | null;
  risk_explanation: string | null;
  recommendations: string[] | null;
  disclaimer: string | null;
  status: IncidentReportStatus;
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

export interface IncidentReportListItem {
  id: string;
  user_id: string;
  camera_id: string | null;
  camera_name?: string | null;
  event_count: number;
  ai_provider: string;
  risk_level: IncidentRiskLevel | null;
  summary_preview: string | null;
  status: IncidentReportStatus;
  created_at: string;
}

export interface CreateIncidentReportRequest {
  event_ids: string[];
  analysis_job_id?: string | null;
}

// ─── Phase 9: Advanced Analytics & Anomaly Intelligence ───────────────────────
export * from './analytics';
