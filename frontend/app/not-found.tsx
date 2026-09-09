import Link from 'next/link';
import { ShieldAlert, ArrowLeft } from 'lucide-react';

export default function NotFound() {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex items-center justify-center p-4">
      <div className="max-w-md w-full bg-slate-900 border border-slate-800 rounded-xl p-8 text-center shadow-2xl">
        <div className="mx-auto w-16 h-16 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400 mb-6">
          <ShieldAlert className="h-8 w-8" />
        </div>

        <h1 className="text-4xl font-extrabold text-white tracking-tight mb-2">404</h1>
        <h2 className="text-lg font-semibold text-slate-200 mb-2">Surveillance Sector Not Found</h2>
        <p className="text-sm text-slate-400 mb-6">
          The requested surveillance feed, route, or SOC resource does not exist or has been decommissioned.
        </p>

        <Link
          href="/dashboard"
          className="inline-flex items-center justify-center gap-2 w-full py-2.5 px-4 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium transition-colors shadow-lg shadow-indigo-600/20"
        >
          <ArrowLeft className="h-4 w-4" />
          Return to SOC Operations
        </Link>
      </div>
    </div>
  );
}
