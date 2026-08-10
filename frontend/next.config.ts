import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  eslint: {
    dirs: [
      "app",
      "components",
      "features",
      "hooks",
      "services",
      "lib",
      "providers",
      "store",
      "types",
      "constants",
    ],
  },
};

export default nextConfig;
