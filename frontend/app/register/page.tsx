'use client';

import { useState, FormEvent } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Eye, EyeOff, Shield, AlertCircle, CheckCircle, Loader2 } from 'lucide-react';
import { useAuth } from '@/hooks/useAuth';
import { extractErrorMessage } from '@/services/auth';

export default function RegisterPage() {
  const router = useRouter();
  const { register } = useAuth();

  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const validateForm = (): string | null => {
    if (!name.trim() || name.trim().length < 2) {
      return 'Full name must be at least 2 characters.';
    }
    if (!email.trim()) {
      return 'Email address is required.';
    }
    const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailPattern.test(email.trim())) {
      return 'Please enter a valid email address.';
    }
    if (password.length < 8) {
      return 'Password must be at least 8 characters.';
    }
    if (password !== confirmPassword) {
      return 'Passwords do not match.';
    }
    return null;
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);

    const validationError = validateForm();
    if (validationError) {
      setError(validationError);
      return;
    }

    setIsLoading(true);
    try {
      await register({
        name: name.trim(),
        email: email.trim(),
        password,
      });
      setSuccess(true);
      setTimeout(() => router.push('/dashboard'), 1200);
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setIsLoading(false);
    }
  };

  const passwordStrength = (() => {
    if (!password) return null;
    if (password.length < 8) return { level: 'weak', label: 'Too short', color: '#ef4444' };
    if (password.length < 12) return { level: 'medium', label: 'Moderate', color: '#f59e0b' };
    return { level: 'strong', label: 'Strong', color: '#22c55e' };
  })();

  return (
    <main className="min-h-screen flex flex-col items-center justify-center bg-[#0a0d12] px-4 py-8">
      {/* Background grid */}
      <div
        className="absolute inset-0 opacity-[0.03] pointer-events-none"
        style={{
          backgroundImage:
            'linear-gradient(#3b7dd8 1px, transparent 1px), linear-gradient(90deg, #3b7dd8 1px, transparent 1px)',
          backgroundSize: '40px 40px',
        }}
      />

      <div className="relative w-full max-w-sm">
        {/* Logo */}
        <div className="flex items-center justify-center gap-2.5 mb-8">
          <div className="w-9 h-9 bg-[#3b7dd8] rounded-lg flex items-center justify-center">
            <Shield className="w-5 h-5 text-white" />
          </div>
          <span className="text-xl font-semibold tracking-tight text-[#e8edf5]">
            SentinelAI
          </span>
        </div>

        <div className="bg-[#111620] border border-[#1e2736] rounded-xl p-8">
          <div className="mb-6">
            <h1 className="text-xl font-semibold text-[#e8edf5]">Create Account</h1>
            <p className="text-sm text-[#8b96a8] mt-1">
              Join the SentinelAI platform
            </p>
          </div>

          {/* Success State */}
          {success && (
            <div className="flex items-start gap-2.5 bg-[rgba(34,197,94,0.08)] border border-[rgba(34,197,94,0.2)] rounded-lg px-4 py-3 mb-5">
              <CheckCircle className="w-4 h-4 text-[#22c55e] mt-0.5 shrink-0" />
              <p className="text-sm text-[#22c55e]">
                Account created successfully. Redirecting to SOC Dashboard…
              </p>
            </div>
          )}

          {/* Error */}
          {error && (
            <div className="flex items-start gap-2.5 bg-[rgba(239,68,68,0.08)] border border-[rgba(239,68,68,0.2)] rounded-lg px-4 py-3 mb-5">
              <AlertCircle className="w-4 h-4 text-[#ef4444] mt-0.5 shrink-0" />
              <p className="text-sm text-[#ef4444]">{error}</p>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4" noValidate>
            {/* Full Name */}
            <div>
              <label
                htmlFor="name"
                className="block text-xs font-medium text-[#8b96a8] mb-1.5 uppercase tracking-wider"
              >
                Full Name
              </label>
              <input
                id="name"
                type="text"
                autoComplete="name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                disabled={isLoading || success}
                placeholder="Kedar Sharma"
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
                disabled={isLoading || success}
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
                  autoComplete="new-password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  disabled={isLoading || success}
                  placeholder="Min. 8 characters"
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
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
              {/* Password strength indicator */}
              {passwordStrength && (
                <div className="mt-2 flex items-center gap-2">
                  <div className="flex-1 h-1 bg-[#1e2736] rounded-full overflow-hidden">
                    <div
                      className="h-full rounded-full transition-all duration-300"
                      style={{
                        width:
                          passwordStrength.level === 'weak'
                            ? '33%'
                            : passwordStrength.level === 'medium'
                            ? '66%'
                            : '100%',
                        backgroundColor: passwordStrength.color,
                      }}
                    />
                  </div>
                  <span className="text-xs" style={{ color: passwordStrength.color }}>
                    {passwordStrength.label}
                  </span>
                </div>
              )}
            </div>

            {/* Confirm Password */}
            <div>
              <label
                htmlFor="confirmPassword"
                className="block text-xs font-medium text-[#8b96a8] mb-1.5 uppercase tracking-wider"
              >
                Confirm Password
              </label>
              <div className="relative">
                <input
                  id="confirmPassword"
                  type={showConfirmPassword ? 'text' : 'password'}
                  autoComplete="new-password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  disabled={isLoading || success}
                  placeholder="Repeat password"
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
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-[#4e5a6b] hover:text-[#8b96a8] transition-colors"
                  tabIndex={-1}
                >
                  {showConfirmPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            {/* Submit */}
            <button
              type="submit"
              disabled={isLoading || success}
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
                  Creating account…
                </>
              ) : (
                'Create Account'
              )}
            </button>
          </form>
        </div>

        <p className="text-center text-sm text-[#8b96a8] mt-5">
          Already have an account?{' '}
          <Link
            href="/login"
            className="text-[#3b7dd8] hover:text-[#4d8fe8] font-medium transition-colors"
          >
            Sign In
          </Link>
        </p>
      </div>
    </main>
  );
}
