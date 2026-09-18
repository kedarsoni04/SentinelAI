'use client';

import { useState, FormEvent } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Eye, EyeOff, AlertCircle, Loader2 } from 'lucide-react';
import { useAuth } from '@/hooks/useAuth';
import { extractErrorMessage } from '@/services/auth';

export default function LoginPage() {
  const router = useRouter();
  const { login } = useAuth();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);

    // Client-side validation
    if (!email.trim()) {
      setError('Email address is required.');
      return;
    }
    const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailPattern.test(email.trim())) {
      setError('Please enter a valid email address (e.g. operator@sentinelai.io).');
      return;
    }
    if (!password) {
      setError('Password is required.');
      return;
    }

    setIsLoading(true);
    try {
      await login({ email: email.trim(), password });
      router.push('/dashboard');
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <main className="min-h-screen flex flex-col items-center justify-center bg-[#0a0d12] px-4">
      {/* Background grid pattern */}
      <div
        className="absolute inset-0 opacity-[0.03] pointer-events-none"
        style={{
          backgroundImage:
            'linear-gradient(#3b7dd8 1px, transparent 1px), linear-gradient(90deg, #3b7dd8 1px, transparent 1px)',
          backgroundSize: '40px 40px',
        }}
      />

      <div className="relative w-full max-w-sm">
        {/* Text Logo / Brand */}
        <div className="flex items-center justify-center gap-2.5 mb-8">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[#3b7dd8] to-[#1a4fa0] flex items-center justify-center shrink-0">
            <span className="text-white font-bold text-base">S</span>
          </div>
          <span className="text-[#e8edf5] font-bold text-xl tracking-tight">
            Sentinel<span className="text-[#3b7dd8]">AI</span>
          </span>
        </div>

        {/* Card */}
        <div className="bg-[#111620] border border-[#1e2736] rounded-xl p-8">
          <div className="mb-6">
            <h1 className="text-xl font-semibold text-[#e8edf5]">Sign in</h1>
            <p className="text-sm text-[#8b96a8] mt-1">
              Access your Security Operations Center
            </p>
          </div>

          {/* Error Banner */}
          {error && (
            <div className="flex items-start gap-2.5 bg-[rgba(239,68,68,0.08)] border border-[rgba(239,68,68,0.2)] rounded-lg px-4 py-3 mb-5">
              <AlertCircle className="w-4 h-4 text-[#ef4444] mt-0.5 shrink-0" />
              <p className="text-sm text-[#ef4444]">{error}</p>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4" noValidate>
            {/* Email */}
            <div>
              <label
                htmlFor="email"
                className="block text-xs font-medium text-[#8b96a8] mb-1.5 uppercase tracking-wider"
              >
                Email
              </label>
              <input
                id="email"
                type="email"
                autoComplete="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                disabled={isLoading}
                placeholder="you@example.com"
                className="
                  w-full h-10 px-3 rounded-lg
                  bg-[#161c28] border border-[#1e2736]
                  text-sm text-[#e8edf5] placeholder:text-[#4e5a6b]
                  focus:outline-none focus:border-[#3b7dd8] focus:ring-1 focus:ring-[#3b7dd8]
                  transition-colors duration-150
                  disabled:opacity-50 disabled:cursor-not-allowed
                "
              />
            </div>

            {/* Password */}
            <div>
              <label
                htmlFor="password"
                className="block text-xs font-medium text-[#8b96a8] mb-1.5 uppercase tracking-wider"
              >
                Password
              </label>
              <div className="relative">
                <input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  autoComplete="current-password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  disabled={isLoading}
                  placeholder="••••••••"
                  className="
                    w-full h-10 px-3 pr-10 rounded-lg
                    bg-[#161c28] border border-[#1e2736]
                    text-sm text-[#e8edf5] placeholder:text-[#4e5a6b]
                    focus:outline-none focus:border-[#3b7dd8] focus:ring-1 focus:ring-[#3b7dd8]
                    transition-colors duration-150
                    disabled:opacity-50 disabled:cursor-not-allowed
                  "
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-[#4e5a6b] hover:text-[#8b96a8] transition-colors"
                  tabIndex={-1}
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                >
                  {showPassword ? (
                    <EyeOff className="w-4 h-4" />
                  ) : (
                    <Eye className="w-4 h-4" />
                  )}
                </button>
              </div>
            </div>

            {/* Submit */}
            <button
              type="submit"
              disabled={isLoading}
              className="
                w-full h-10 mt-2 rounded-lg
                bg-[#3b7dd8] hover:bg-[#4d8fe8]
                text-sm font-medium text-white
                flex items-center justify-center gap-2
                transition-colors duration-150
                disabled:opacity-60 disabled:cursor-not-allowed
                focus:outline-none focus:ring-2 focus:ring-[#3b7dd8] focus:ring-offset-2 focus:ring-offset-[#111620]
              "
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Signing in…
                </>
              ) : (
                'Sign In'
              )}
            </button>
          </form>
        </div>

        {/* Register link */}
        <p className="text-center text-sm text-[#8b96a8] mt-5">
          Don&apos;t have an account?{' '}
          <Link
            href="/register"
            className="text-[#3b7dd8] hover:text-[#4d8fe8] font-medium transition-colors"
          >
            Create Account
          </Link>
        </p>
      </div>
    </main>
  );
}
