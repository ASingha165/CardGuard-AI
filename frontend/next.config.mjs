/** @type {import('next').NextConfig} */
const apiOrigin = process.env.CARDGUARD_API_URL?.replace(/\/$/, "");

const nextConfig = {
  output: "standalone",
  async rewrites() {
    if (!apiOrigin) return [];
    return [
      { source: "/health", destination: `${apiOrigin}/health` },
      { source: "/api/:path*", destination: `${apiOrigin}/api/:path*` },
    ];
  },
};

export default nextConfig;
