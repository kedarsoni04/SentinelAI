import { redirect } from 'next/navigation';

/**
 * Root page — immediately redirects to /dashboard.
 * Middleware will redirect unauthenticated users to /login.
 */
export default function RootPage() {
  redirect('/dashboard');
}
