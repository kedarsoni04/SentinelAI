import { NextRequest, NextResponse } from 'next/server';

/**
 * Validates basic JWT structure and verifies whether the token is unexpired.
 * Uses Edge-compatible atob for lightweight, dependency-free decoding.
 */
function isTokenValid(token?: string | null): boolean {
  if (!token || token === 'undefined' || token === 'null' || !token.trim()) {
    return false;
  }
  try {
    const parts = token.split('.');
    if (parts.length !== 3) return false;
    // Edge-safe base64url decoding
    const base64 = parts[1].replace(/-/g, '+').replace(/_/g, '/');
    const jsonStr = atob(base64);
    const payload = JSON.parse(jsonStr);
    if (typeof payload.exp === 'number') {
      return payload.exp * 1000 > Date.now();
    }
    return true;
  } catch {
    return false;
  }
}

/**
 * Next.js Edge Middleware — server-side route protection.
 *
 * Checks for the `sentinel_token` cookie.
 * - Unauthenticated / expired users accessing /dashboard/* are redirected to /login.
 * - Invalid or expired cookies are automatically pruned to prevent infinite redirect loops.
 */
export function middleware(request: NextRequest) {
  const { pathname, searchParams } = request.nextUrl;
  const rawToken = request.cookies.get('sentinel_token')?.value;
  const tokenValid = isTokenValid(rawToken);

  const isProtectedRoute = pathname.startsWith('/dashboard');
  const isAuthRoute = pathname === '/login' || pathname === '/register';

  // 1. Unauthenticated or expired access to protected routes -> redirect to /login & clear bad cookie
  if (isProtectedRoute && !tokenValid) {
    const loginUrl = new URL('/login', request.url);
    loginUrl.searchParams.set('from', pathname);
    const response = NextResponse.redirect(loginUrl);
    if (rawToken) {
      response.cookies.delete('sentinel_token');
    }
    return response;
  }

  // 2. Auth routes (/login, /register)
  if (isAuthRoute) {
    // If the cookie is invalid or expired, purge it immediately
    if (rawToken && !tokenValid) {
      const response = NextResponse.next();
      response.cookies.delete('sentinel_token');
      return response;
    }

    // Only redirect to /dashboard if the token is demonstrably valid and not explicitly switching accounts
    if (tokenValid && !searchParams.has('from') && !searchParams.has('logout')) {
      return NextResponse.redirect(new URL('/dashboard', request.url));
    }
  }

  return NextResponse.next();
}

export const config = {
  matcher: ['/dashboard/:path*', '/login', '/register'],
};
