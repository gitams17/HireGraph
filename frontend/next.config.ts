import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  cacheComponents: true,
  partialPrefetching: true,
  trailingSlash: true,
  skipTrailingSlashRedirect: true,

  turbopack: {
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },

  /**
   * Rewrite all /api/* requests to the Django backend running at port 8000.
   * This gives the browser a single same-origin endpoint, which means:
   *  - Session cookies work with SameSite=Lax (no special cookie flags needed)
   *  - No CORS pre-flight overhead on API calls
   *  - Production behaviour is identical (nginx / Cloud Run reverse-proxy)
   */
  async rewrites() {
    const apiBase =
      process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
    return [
      {
        source: "/api/:path*",
        destination: `${apiBase}/api/:path*/`,
      },
    ];
  },
};

export default nextConfig;
