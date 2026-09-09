import { AlertTriangle, Eye, Clock, Users, MapPin, Activity } from 'lucide-react';
import type { IncidentTimelineItem } from '@/types';
import { cn } from '@/lib/utils';

interface IncidentTimelineProps {
  items: IncidentTimelineItem[];
}

const eventTypeConfig: Record<string, { icon: React.ComponentType<{className?: string}>; color: string; bg: string }> = {
  INTRUSION:         { icon: AlertTriangle, color: 'text-red-400',    bg: 'bg-red-500/20' },
  LOITERING:         { icon: Clock,         color: 'text-orange-400', bg: 'bg-orange-500/20' },
  CROWD_DENSITY:     { icon: Users,         color: 'text-yellow-400', bg: 'bg-yellow-500/20' },
  STATIONARY_OBJECT: { icon: MapPin,        color: 'text-blue-400',   bg: 'bg-blue-500/20' },
  UNUSUAL_MOVEMENT:  { icon: Activity,      color: 'text-purple-400', bg: 'bg-purple-500/20' },
};

const DEFAULT_TYPE_CONFIG = { icon: Eye, color: 'text-[#3b7dd8]', bg: 'bg-[#3b7dd8]/20' };

function formatEventType(type: string): string {
  return type
    .toLowerCase()
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

export default function IncidentTimeline({ items }: IncidentTimelineProps) {
  if (!items || items.length === 0) {
    return (
      <p className="text-sm text-[#8b96a8] italic">No timeline events available.</p>
    );
  }

  return (
    <div className="relative">
      {/* Vertical line */}
      <div className="absolute left-5 top-0 bottom-0 w-px bg-[#1e2736]" />

      <div className="space-y-4">
        {items.map((item, index) => {
          const typeKey = item.event_type?.toUpperCase() ?? '';
          const { icon: Icon, color, bg } = eventTypeConfig[typeKey] ?? DEFAULT_TYPE_CONFIG;

          return (
            <div key={index} className="flex gap-4 relative">
              {/* Icon bubble */}
              <div
                className={cn(
                  'relative z-10 flex items-center justify-center w-10 h-10 rounded-full shrink-0',
                  bg
                )}
              >
                <Icon className={cn('w-4 h-4', color)} />
              </div>

              {/* Content */}
              <div className="flex-1 pb-4">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-xs font-mono text-[#4e5a6b] bg-[#0d1117] border border-[#1e2736] rounded px-1.5 py-0.5">
                    {item.timestamp_label}
                  </span>
                  <span className={cn('text-xs font-semibold uppercase tracking-wide', color)}>
                    {formatEventType(item.event_type)}
                  </span>
                </div>
                <p className="text-sm text-[#c8d4e5] leading-relaxed">
                  {item.description}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
