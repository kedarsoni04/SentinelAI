'use client';

import { useEffect, useState } from 'react';
import { CheckCircle, AlertCircle, X } from 'lucide-react';

export type ToastType = 'success' | 'error';

export interface ToastMessage {
  id: string;
  type: ToastType;
  message: string;
}

interface ToastProps {
  toasts: ToastMessage[];
  onDismiss: (id: string) => void;
}

/**
 * Minimal toast notification system — no external libraries.
 * Renders a stack of dismissible notifications in the bottom-right corner.
 * Auto-dismisses after 4 seconds.
 */
export function Toast({ toasts, onDismiss }: ToastProps) {
  return (
    <div className="fixed bottom-5 right-5 z-50 flex flex-col gap-2 pointer-events-none">
      {toasts.map((toast) => (
        <ToastItem key={toast.id} toast={toast} onDismiss={onDismiss} />
      ))}
    </div>
  );
}

function ToastItem({ toast, onDismiss }: { toast: ToastMessage; onDismiss: (id: string) => void }) {
  useEffect(() => {
    const timer = setTimeout(() => onDismiss(toast.id), 4000);
    return () => clearTimeout(timer);
  }, [toast.id, onDismiss]);

  const isSuccess = toast.type === 'success';

  return (
    <div
      className={`
        pointer-events-auto flex items-start gap-3 min-w-[280px] max-w-sm
        px-4 py-3 rounded-xl border shadow-xl shadow-black/40
        animate-in slide-in-from-bottom-2 duration-200
        ${isSuccess
          ? 'bg-[#111620] border-[rgba(34,197,94,0.25)]'
          : 'bg-[#111620] border-[rgba(239,68,68,0.25)]'
        }
      `}
    >
      {isSuccess
        ? <CheckCircle className="w-4 h-4 text-[#22c55e] mt-0.5 shrink-0" />
        : <AlertCircle className="w-4 h-4 text-[#ef4444] mt-0.5 shrink-0" />
      }
      <p className="text-sm text-[#e8edf5] flex-1 leading-relaxed">{toast.message}</p>
      <button
        onClick={() => onDismiss(toast.id)}
        className="text-[#4e5a6b] hover:text-[#8b96a8] transition-colors shrink-0"
        aria-label="Dismiss"
      >
        <X className="w-3.5 h-3.5" />
      </button>
    </div>
  );
}

// ─── Toast Hook ───────────────────────────────────────────────────────────────

/**
 * useToast — manages a stack of toast messages.
 * Usage:
 *   const { toasts, showToast, dismissToast } = useToast();
 *   showToast('success', 'Camera added successfully.');
 */
export function useToast() {
  const [toasts, setToasts] = useState<ToastMessage[]>([]);

  const showToast = (type: ToastType, message: string) => {
    const id = Math.random().toString(36).slice(2);
    setToasts((prev) => [...prev, { id, type, message }]);
  };

  const dismissToast = (id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  return { toasts, showToast, dismissToast };
}
