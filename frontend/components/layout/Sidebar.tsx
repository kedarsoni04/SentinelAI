'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  LayoutDashboard,
  Radio,
  Camera,
  Film,
  AlertTriangle,
  Sliders,
  Maximize2,
  BarChart2,
  Settings,
  ChevronRight,
  Brain,
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface NavItem {
  label: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  implemented: boolean;
}

const navItems: NavItem[] = [
  { label: 'Dashboard',       href: '/dashboard',                icon: LayoutDashboard, implemented: true },
  { label: 'Live Monitoring', href: '/dashboard/monitoring',       icon: Radio,           implemented: true },
  { label: 'Security Events', href: '/dashboard/events',           icon: AlertTriangle,   implemented: true },
  { label: 'Cameras',         href: '/dashboard/cameras',        icon: Camera,          implemented: true },
  { label: 'Analysis',        href: '/dashboard/analysis',       icon: Film,            implemented: true },
  { label: 'Security Rules',  href: '/dashboard/rules',          icon: Sliders,         implemented: true },
  { label: 'Security Zones',  href: '/dashboard/zones',          icon: Maximize2,       implemented: true },
  { label: 'Incident Intel',  href: '/dashboard/incidents',      icon: Brain,           implemented: true },
  { label: 'Analytics',       href: '/dashboard/analytics',      icon: BarChart2,       implemented: true },
  { label: 'Settings',        href: '/dashboard/settings',       icon: Settings,        implemented: false },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="
      hidden md:flex flex-col
      w-[240px] shrink-0
      bg-[#0d1117] border-r border-[#1e2736]
      h-screen sticky top-0
    ">
      {/* Brand */}
      <div className="flex items-center justify-center px-5 h-14 border-b border-[#1e2736]">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-[#3b7dd8] to-[#1a4fa0] flex items-center justify-center shrink-0">
            <span className="text-white font-bold text-sm">S</span>
          </div>
          <span className="text-[#e8edf5] font-bold text-base tracking-tight">
            Sentinel<span className="text-[#3b7dd8]">AI</span>
          </span>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-0.5 overflow-y-auto">
        <p className="px-2 pb-2 text-[10px] font-semibold text-[#4e5a6b] uppercase tracking-widest">
          Navigation
        </p>

        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = pathname === item.href;

          if (!item.implemented) {
            return (
              <div
                key={item.href}
                className="
                  flex items-center gap-3 px-2 py-2 rounded-lg
                  text-[#4e5a6b] cursor-not-allowed select-none
                "
                title="Coming in a future phase"
              >
                <Icon className="w-4 h-4 shrink-0" />
                <span className="text-sm">{item.label}</span>
                <span className="ml-auto text-[9px] font-medium text-[#4e5a6b] border border-[#1e2736] rounded px-1 py-0.5 uppercase tracking-wider">
                  Soon
                </span>
              </div>
            );
          }

          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                'flex items-center gap-3 px-2 py-2 rounded-lg transition-colors duration-150',
                isActive
                  ? 'bg-[rgba(59,125,216,0.12)] text-[#3b7dd8]'
                  : 'text-[#8b96a8] hover:bg-[#161c28] hover:text-[#e8edf5]'
              )}
            >
              <Icon className="w-4 h-4 shrink-0" />
              <span className="text-sm font-medium">{item.label}</span>
              {isActive && <ChevronRight className="w-3 h-3 ml-auto" />}
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="px-5 py-4 border-t border-[#1e2736]">
        <p className="text-[10px] text-[#4e5a6b]">Phase 9 · Advanced Analytics</p>
        <p className="text-[10px] text-[#4e5a6b] mt-0.5">v0.9.0</p>
      </div>
    </aside>
  );
}
