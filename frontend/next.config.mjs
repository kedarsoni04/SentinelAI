/** @type {import('next').NextConfig} */
const BACKEND_URL =
  process.env.NEXT_PUBLIC_API_URL ||
  'https://sentinelai-backend-s3cz.onrender.com';

const nextConfig = {
  output: 'standalone',

  /**
   * Proxy all /api/* requests to the FastAPI backend.
   * This eliminates CORS entirely for production deployments on Vercel
   * because the browser talks to the same Next.js origin; Next.js
   * forwards the request server-side.
   *
   * NOTE: WebSocket connections (/api/realtime/ws/*) cannot be proxied
   * by Next.js rewrites — they must hit the backend directly. The
   * RealtimeWebSocketClient in services/realtime.ts uses BACKEND_URL_WS.
   */
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${BACKEND_URL}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
