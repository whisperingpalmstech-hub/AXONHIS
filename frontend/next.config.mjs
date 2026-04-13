/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: "standalone",
  async rewrites() {
    return [
      {
        source: '/api/v1/:path*',
        destination: 'http://localhost:9500/api/v1/:path*',
      },
    ];
  },
};

export default nextConfig;
