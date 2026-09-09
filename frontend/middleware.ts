import { NextRequest, NextResponse } from 'next/server';

/**
 * Next.js Edge Middleware — server-side route protection.
 *
 * Checks for the `sentinel_token` cookie (set by the frontend on login).
 * - Unauthenticated users accessing /dashboard/* are redirected to /login.
 * - Authenticated users accessing /login or /register are redirected to /dashboard.
 *
 * NOTE: This provides a server-side UX guard only.
 * The actual token validation happens on the backend (GET /api/auth/me).
 * The useAuth hook re-validates the token on every dashboard mount.
 */
export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const token = request.cookies.get('sentinel_token')?.value;

  const isProtectedRoute = pathname.startsWith('/dashboard');
  const isAuthRoute = pathname === '/login' || pathname === '/register';

  // Redirect unauthenticated users away from protected routes
  if (isProtectedRoute && !token) {
    const loginUrl = new URL('/login', request.url);
    loginUrl.searchParams.set('from', pathname);
    return NextResponse.redirect(loginUrl);
  }

  // Redirect authenticated users away from auth pages
  if (isAuthRoute && token) {
    return NextResponse.redirect(new URL('/dashboard', request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ['/dashboard/:path*', '/login', '/register'],
};
