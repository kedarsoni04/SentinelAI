'use client';

import { useEffect, useState, useCallback } from 'react';
import {
  AlertTriangle,
  BarChart2,
  Camera,
  Flame,
  RefreshCw,
  Zap,
} from 'lucide-react';
import DateRangeSelector from '@/components/analytics/DateRangeSelector';
import AnalyticsMetricCard from '@/components/analytics/AnalyticsMetricCard';
import EventTrendChart from '@/components/analytics/EventTrendChart';
import DistributionCharts from '@/components/analytics/DistributionCharts';
import ActivityHeatmap from '@/components/analytics/ActivityHeatmap';
import CameraAnalyticsTable from '@/components/analytics/CameraAnalyticsTable';
import AnomaliesPanel from '@/components/analytics/AnomaliesPanel';
import InsightsPanel from '@/components/analytics/InsightsPanel';
import IncidentAnalyticsSection from '@/components/analytics/IncidentAnalyticsSection';

import {
  getActivityHeatmap,
  getAnalyticsOverview,
  getAnomalies,
  getCameraAnalytics,
  getEventDistribution,
  getEventTrends,
  getIncidentAnalytics,
  getSecurityInsights,
  getSeverityDistribution,
} from '@/services/analytics';

import type {
  ActivityHeatmapData,
  AnalyticsFilterParams,
  AnalyticsOverview,
  AnomalyDetectionData,
  CameraAnalyticsData,
  DateRangePreset,
  EventDistributionData,
  EventTrendsData,
  IncidentAnalyticsData,
  SecurityInsightsData,
  SeverityDistributionData,
} from '@/types';

export default function AnalyticsDashboardPage() {
  const [preset, setPreset] = useState<DateRangePreset>('7d');
  const [customStart, setCustomStart] = useState<string | undefined>();
  const [customEnd, setCustomEnd] = useState<string | undefined>();
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Data states
  const [overview, setOverview] = useState<AnalyticsOverview | null>(null);
  const [trends, setTrends] = useState<EventTrendsData | null>(null);
  const [eventDist, setEventDist] = useState<EventDistributionData | null>(null);
  const [sevDist, setSevDist] = useState<SeverityDistributionData | null>(null);
  const [cameraData, setCameraData] = useState<CameraAnalyticsData | null>(null);
  const [heatmap, setHeatmap] = useState<ActivityHeatmapData | null>(null);
  const [incidents, setIncidents] = useState<IncidentAnalyticsData | null>(null);
  const [anomalies, setAnomalies] = useState<AnomalyDetectionData | null>(null);
  const [insights, setInsights] = useState<SecurityInsightsData | null>(null);

  // Loading flags
  const [loadingOverview, setLoadingOverview] = useState(true);
  const [loadingTrends, setLoadingTrends] = useState(true);
  const [loadingDist, setLoadingDist] = useState(true);
  const [loadingCameras, setLoadingCameras] = useState(true);
  const [loadingHeatmap, setLoadingHeatmap] = useState(true);
  const [loadingIncidents, setLoadingIncidents] = useState(true);
  const [loadingAnomalies, setLoadingAnomalies] = useState(true);
  const [loadingInsights, setLoadingInsights] = useState(true);

  const loadAllAnalytics = useCallback(async (params: AnalyticsFilterParams) => {
    setIsRefreshing(true);

    // Overview
    setLoadingOverview(true);
    getAnalyticsOverview(params)
      .then(setOverview)
      .catch(() => {})
      .finally(() => setLoadingOverview(false));

    // Trends
    setLoadingTrends(true);
    getEventTrends(params)
      .then(setTrends)
      .catch(() => {})
      .finally(() => setLoadingTrends(false));

    // Distributions
    setLoadingDist(true);
    Promise.all([
      getEventDistribution(params),
      getSeverityDistribution(params),
    ])
      .then(([eDist, sDist]) => {
        setEventDist(eDist);
        setSevDist(sDist);
      })
      .catch(() => {})
      .finally(() => setLoadingDist(false));

    // Camera Analytics
    setLoadingCameras(true);
    getCameraAnalytics(params)
      .then(setCameraData)
      .catch(() => {})
      .finally(() => setLoadingCameras(false));

    // Heatmap
    setLoadingHeatmap(true);
    getActivityHeatmap(params)
      .then(setHeatmap)
      .catch(() => {})
      .finally(() => setLoadingHeatmap(false));

    // Incidents
    setLoadingIncidents(true);
    getIncidentAnalytics(params)
      .then(setIncidents)
      .catch(() => {})
      .finally(() => setLoadingIncidents(false));

    // Anomalies
    setLoadingAnomalies(true);
    getAnomalies(params)
      .then(setAnomalies)
      .catch(() => {})
      .finally(() => setLoadingAnomalies(false));

    // Insights
    setLoadingInsights(true);
    getSecurityInsights(params)
      .then(setInsights)
      .catch(() => {})
      .finally(() => {
        setLoadingInsights(false);
        setIsRefreshing(false);
      });
  }, []);

  useEffect(() => {
    const params: AnalyticsFilterParams = {
      preset,
      start_date: preset === 'custom' ? customStart : undefined,
      end_date: preset === 'custom' ? customEnd : undefined,
    };
    loadAllAnalytics(params);
  }, [preset, customStart, customEnd, loadAllAnalytics]);

  const handlePresetChange = (newPreset: DateRangePreset) => {
    setPreset(newPreset);
  };

  const handleCustomRangeChange = (start: string, end: string) => {
    setCustomStart(start);
    setCustomEnd(end);
  };

  const handleRefresh = () => {
    loadAllAnalytics({
      preset,
      start_date: preset === 'custom' ? customStart : undefined,
      end_date: preset === 'custom' ? customEnd : undefined,
    });
  };

  return (
    <div className="space-y-6 pb-12">
      {/* Top Header & Range Controls */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4 pb-2 border-b border-[#1e2736]">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-lg bg-[rgba(59,125,216,0.12)] text-[#3b7dd8]">
              <BarChart2 className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-[#e8edf5] tracking-tight">
                Security Analytics & Anomaly Intelligence
              </h1>
              <p className="text-xs text-[#8b96a8] mt-0.5">
                Real-time metrics, historical trends, baseline calculations, and deterministic SOC anomaly intelligence
              </p>
            </div>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <DateRangeSelector
            preset={preset}
            startDate={customStart}
            endDate={customEnd}
            onPresetChange={handlePresetChange}
            onCustomRangeChange={handleCustomRangeChange}
            disabled={isRefreshing}
          />

          <button
            type="button"
            onClick={handleRefresh}
            disabled={isRefreshing}
            className="p-2 bg-[#161c28] hover:bg-[#1e2736] border border-[#232f42] rounded-lg text-[#8b96a8] hover:text-[#e8edf5] transition-colors disabled:opacity-50"
            title="Refresh analytics data"
          >
            <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin text-[#3b7dd8]' : ''}`} />
          </button>
        </div>
      </div>

      {/* KPI Overview Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <AnalyticsMetricCard
          title="Total Security Events"
          value={overview?.total_events ?? 0}
          changePercentage={overview?.event_change_percentage}
          icon={AlertTriangle}
          accentColor="blue"
          isLoading={loadingOverview}
        />

        <AnalyticsMetricCard
          title="Incidents Generated"
          value={overview?.total_incidents ?? 0}
          changePercentage={overview?.incident_change_percentage}
          icon={Zap}
          accentColor="purple"
          isLoading={loadingOverview}
        />

        <AnalyticsMetricCard
          title="High & Critical Alerts"
          value={(overview?.high_severity_events ?? 0) + (overview?.critical_events ?? 0)}
          changeLabel="elevated severity tier"
          icon={Flame}
          accentColor="red"
          isLoading={loadingOverview}
        />

        <AnalyticsMetricCard
          title="Monitored Cameras"
          value={overview?.active_cameras ?? 0}
          changeLabel="surveillance fleet online"
          icon={Camera}
          accentColor="green"
          isLoading={loadingOverview}
        />
      </div>

      {/* Operational Security Insights Banner */}
      {insights && insights.insights.length > 0 && (
        <InsightsPanel data={insights} isLoading={loadingInsights} />
      )}

      {/* Event Velocity & Multi-Severity Trends */}
      <EventTrendChart
        data={trends?.data ?? []}
        interval={trends?.interval ?? 'daily'}
        totalEvents={trends?.total_events ?? 0}
        isLoading={loadingTrends}
      />

      {/* Severity & Event Category Distributions */}
      <DistributionCharts
        eventTypes={eventDist?.items ?? []}
        severities={sevDist?.items ?? []}
        totalEvents={overview?.total_events ?? 0}
        isLoading={loadingDist}
      />

      {/* 7x24 Security Activity Heatmap & Time Patterns */}
      <ActivityHeatmap
        data={
          heatmap ?? {
            cells: [],
            peak_hour: null,
            peak_day: null,
            quiet_hours: [],
            total_events: 0,
          }
        }
        isLoading={loadingHeatmap}
      />

      {/* Fleet Camera Analytics & Deterministic Risk Scoring */}
      <CameraAnalyticsTable
        data={
          cameraData ?? {
            total_cameras: 0,
            most_active_camera: null,
            highest_risk_camera: null,
            cameras: [],
          }
        }
        isLoading={loadingCameras}
      />

      {/* Anomaly Detection & Incident Analytics Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <AnomaliesPanel
          data={
            anomalies ?? {
              has_sufficient_data: false,
              status: 'INSUFFICIENT_DATA',
              message: 'Loading anomaly intelligence...',
              anomalies: [],
              total_anomalies: 0,
            }
          }
          isLoading={loadingAnomalies}
        />

        <IncidentAnalyticsSection
          data={
            incidents ?? {
              total_incidents: 0,
              by_status: {},
              by_risk_level: {},
              resolved_count: 0,
              resolution_rate: 0,
              average_resolution_time_minutes: null,
            }
          }
          isLoading={loadingIncidents}
        />
      </div>
    </div>
  );
}
