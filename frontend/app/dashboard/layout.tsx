'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/hooks/useAuth';
import Sidebar from '@/components/layout/Sidebar';
import Topbar from '@/components/layout/Topbar';
import { Loader2 } from 'lucide-react';

/**
 * Dashboard layout — wraps all /dashboard/* pages with the sidebar and topbar.
 * Provides client-side auth validation as a secondary guard after middleware.
 */
export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const { isAuthenticated, isLoading } = useAuth();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.replace('/login');
    }
  }, [isAuthenticated, isLoading, router]);

  // Show a full-screen loader while validating auth
  if (isLoading) {
    return (
      <div className="min-h-screen bg-[#0a0d12] flex items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <Loader2 className="w-8 h-8 text-[#3b7dd8] animate-spin" />
          <p className="text-sm text-[#8b96a8]">Initializing SentinelAI…</p>
        </div>
      </div>
    );
  }

  // Don't render protected content before redirect fires
  if (!isAuthenticated) {
    return null;
  }

  return (
    <div className="flex h-screen bg-[#0a0d12] overflow-hidden">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        <Topbar />
        <main className="flex-1 overflow-y-auto p-6">
          {children}
        </main>
      </div>
    </div>
  );
}
