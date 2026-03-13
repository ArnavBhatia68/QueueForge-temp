/**
 * Legacy compatibility config mirror.
 * Keep this file aligned with `next.config.ts` for environments that prefer `.mjs`.
 */
const nextConfig = {
  skipTrailingSlashRedirect: true,
  allowedDevOrigins: ['127.0.0.1', 'localhost'],
  async rewrites() {
    const apiBase = process.env.NEXT_PUBLIC_API_URL
      ? process.env.NEXT_PUBLIC_API_URL
      : 'http://127.0.0.1:8001/api/v1';

    return [
      {
        source: '/api/v1/:path*/',
        destination: `${apiBase}/:path*/`,
      },
      {
        source: '/api/v1/:path*',
        destination: `${apiBase}/:path*`,
      },
    ];
  },
};

export default nextConfig;
