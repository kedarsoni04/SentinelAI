import api, { getApiBaseUrl } from './api';
import { getStoredToken } from './auth';
import type {
  ConnectionStatus,
  RealtimeMessage,
  RealtimeSessionMetrics,
} from '@/types';

export function getWebSocketBaseUrl(): string {
  const apiUrl = getApiBaseUrl();
  if (apiUrl.startsWith('https://')) return apiUrl.replace('https://', 'wss://');
  if (apiUrl.startsWith('http://')) return apiUrl.replace('http://', 'ws://');
  return `wss://${apiUrl}`;
}

/**
 * Start real-time monitoring session for a video analysis job.
 */
export async function startRealtimeMonitoring(jobId: string): Promise<RealtimeSessionMetrics> {
  const res = await api.post<RealtimeSessionMetrics>(`/api/video-analysis/${jobId}/realtime/start`);
  return res.data;
}

/**
 * Stop an active real-time monitoring session.
 */
export async function stopRealtimeMonitoring(jobId: string): Promise<RealtimeSessionMetrics> {
  const res = await api.post<RealtimeSessionMetrics>(`/api/video-analysis/${jobId}/realtime/stop`);
  return res.data;
}

/**
 * Get current execution status and metrics for a real-time monitoring session.
 */
export async function getRealtimeStatus(jobId: string): Promise<RealtimeSessionMetrics> {
  const res = await api.get<RealtimeSessionMetrics>(`/api/video-analysis/${jobId}/realtime/status`);
  return res.data;
}

/**
 * List all active monitoring sessions for the authenticated operator.
 */
export async function getActiveMonitoringSessions(): Promise<RealtimeSessionMetrics[]> {
  const res = await api.get<RealtimeSessionMetrics[]>('/api/video-analysis/realtime/active');
  return res.data;
}

/**
 * Construct authenticated preview frame URL for real-time monitoring.
 */
export function getRealtimeFrameUrl(jobId: string, timestamp?: number): string {
  const baseUrl = getApiBaseUrl();
  const token = getStoredToken();
  const tsParam = timestamp ? `&ts=${timestamp}` : `&_t=${Date.now()}`;
  return `${baseUrl}/api/video-analysis/${jobId}/realtime/frame?token=${encodeURIComponent(token || '')}${tsParam}`;
}

export interface WebSocketClientOptions {
  onMessage: (message: RealtimeMessage) => void;
  onStatusChange: (status: ConnectionStatus) => void;
  onError?: (error: Event) => void;
}

/**
 * Resilient WebSocket Client for real-time video analysis & SOC alert streams.
 * Includes automatic exponential backoff reconnection, token authentication,
 * and clean lifecycle teardown.
 */
export class RealtimeWebSocketClient {
  private jobId: string;
  private options: WebSocketClientOptions;
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectDelay = 30000;
  private reconnectTimer: NodeJS.Timeout | null = null;
  private pingTimer: NodeJS.Timeout | null = null;
  private isManuallyClosed = false;

  constructor(jobId: string, options: WebSocketClientOptions) {
    this.jobId = jobId;
    this.options = options;
  }

  public connect(): void {
    if (typeof window === 'undefined') return;

    this.isManuallyClosed = false;
    this.clearTimers();

    const token = getStoredToken();
    if (!token) {
      this.options.onStatusChange('OFFLINE');
      return;
    }

    const wsUrl = `${getWebSocketBaseUrl()}/api/ws/analysis/${this.jobId}?token=${encodeURIComponent(token)}`;

    try {
      this.options.onStatusChange(this.reconnectAttempts > 0 ? 'RECONNECTING' : 'OFFLINE');
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        this.reconnectAttempts = 0;
        this.options.onStatusChange('LIVE');
        this.startHeartbeat();
      };

      this.ws.onmessage = (event) => {
        try {
          if (event.data === 'pong') return;
          const parsed = JSON.parse(event.data) as RealtimeMessage;
          this.options.onMessage(parsed);
        } catch {
          // Ignore unstructured or ping messages
        }
      };

      this.ws.onclose = () => {
        this.stopHeartbeat();
        if (!this.isManuallyClosed) {
          this.options.onStatusChange('RECONNECTING');
          this.scheduleReconnect();
        } else {
          this.options.onStatusChange('OFFLINE');
        }
      };

      this.ws.onerror = (err) => {
        if (this.options.onError) {
          this.options.onError(err);
        }
      };
    } catch {
      this.scheduleReconnect();
    }
  }

  public disconnect(): void {
    this.isManuallyClosed = true;
    this.clearTimers();
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.options.onStatusChange('OFFLINE');
  }

  private scheduleReconnect(): void {
    if (this.isManuallyClosed) return;

    const delay = Math.min(
      this.maxReconnectDelay,
      1000 * Math.pow(2, this.reconnectAttempts)
    );
    this.reconnectAttempts++;

    this.reconnectTimer = setTimeout(() => {
      this.connect();
    }, delay);
  }

  private startHeartbeat(): void {
    this.stopHeartbeat();
    this.pingTimer = setInterval(() => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.ws.send('ping');
      }
    }, 15000);
  }

  private stopHeartbeat(): void {
    if (this.pingTimer) {
      clearInterval(this.pingTimer);
      this.pingTimer = null;
    }
  }

  private clearTimers(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    this.stopHeartbeat();
  }
}
