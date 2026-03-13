import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
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
