'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Bell, ChevronDown, LogOut, User, Shield } from 'lucide-react';
import { useAuth } from '@/hooks/useAuth';

export default function Topbar() {
  const router = useRouter();
  const { user, logout } = useAuth();
  const [dropdownOpen, setDropdownOpen] = useState(false);

  const handleLogout = async () => {
    await logout();
    router.push('/login');
  };

  const roleLabel: Record<string, string> = {
    ADMIN: 'Administrator',
    SECURITY_OPERATOR: 'Security Operator',
    VIEWER: 'Viewer',
  };

  return (
    <header className="
      h-14 px-6
      bg-[#0d1117] border-b border-[#1e2736]
      flex items-center justify-between
      sticky top-0 z-10
    ">
      {/* Left — page context */}
      <div className="flex items-center gap-2">
        <span className="text-xs text-[#4e5a6b] uppercase tracking-widest font-medium">
          Security Operations Center
        </span>
      </div>

      {/* Right — actions */}
      <div className="flex items-center gap-3">
        {/* Notifications — placeholder */}
        <button
          className="
            w-8 h-8 rounded-lg flex items-center justify-center
            text-[#4e5a6b] hover:text-[#8b96a8] hover:bg-[#161c28]
            transition-colors duration-150
            relative
          "
          title="Notifications (no active alerts)"
          aria-label="Notifications"
        >
          <Bell className="w-4 h-4" />
          {/* No active notifications in Phase 1 */}
        </button>

        {/* User menu */}
        <div className="relative">
          <button
            onClick={() => setDropdownOpen(!dropdownOpen)}
            className="
              flex items-center gap-2.5 px-3 py-1.5 rounded-lg
              bg-[#161c28] border border-[#1e2736]
              hover:border-[#2a3748] transition-colors duration-150
              text-sm
            "
            aria-expanded={dropdownOpen}
            aria-haspopup="true"
          >
            {/* Avatar */}
            <div className="w-6 h-6 rounded-full bg-[#3b7dd8] flex items-center justify-center">
              <span className="text-[10px] font-semibold text-white uppercase">
                {user?.name?.charAt(0) || '?'}
              </span>
            </div>
            <span className="text-[#e8edf5] font-medium max-w-[120px] truncate">
              {user?.name || 'Loading…'}
            </span>
            <ChevronDown className={`w-3.5 h-3.5 text-[#4e5a6b] transition-transform duration-150 ${dropdownOpen ? 'rotate-180' : ''}`} />
          </button>

          {/* Dropdown */}
          {dropdownOpen && (
            <>
              {/* Backdrop */}
              <div
                className="fixed inset-0 z-10"
                onClick={() => setDropdownOpen(false)}
              />
              <div className="
                absolute right-0 top-full mt-1.5 z-20
                w-52 bg-[#111620] border border-[#1e2736] rounded-xl
                shadow-xl shadow-black/40
                overflow-hidden
              ">
                {/* User info */}
                <div className="px-4 py-3 border-b border-[#1e2736]">
                  <p className="text-sm font-medium text-[#e8edf5] truncate">{user?.name}</p>
                  <p className="text-xs text-[#8b96a8] truncate mt-0.5">{user?.email}</p>
                  <div className="flex items-center gap-1.5 mt-2">
                    <Shield className="w-3 h-3 text-[#3b7dd8]" />
                    <span className="text-[10px] text-[#3b7dd8] font-medium">
                      {user?.role ? roleLabel[user.role] || user.role : '—'}
                    </span>
                  </div>
                </div>

                {/* Actions */}
                <div className="p-1">
                  <button
                    className="
                      w-full flex items-center gap-2.5 px-3 py-2 rounded-lg
                      text-sm text-[#8b96a8] hover:text-[#e8edf5] hover:bg-[#161c28]
                      transition-colors duration-150
                    "
                    onClick={() => setDropdownOpen(false)}
                    disabled
                  >
                    <User className="w-3.5 h-3.5" />
                    Profile
                    <span className="ml-auto text-[9px] text-[#4e5a6b] border border-[#1e2736] rounded px-1">Soon</span>
                  </button>
                  <button
                    onClick={handleLogout}
                    className="
                      w-full flex items-center gap-2.5 px-3 py-2 rounded-lg
                      text-sm text-[#ef4444] hover:bg-[rgba(239,68,68,0.08)]
                      transition-colors duration-150
                    "
                  >
                    <LogOut className="w-3.5 h-3.5" />
                    Sign Out
                  </button>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </header>
  );
}
