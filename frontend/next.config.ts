import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Fix Turbopack workspace warning
  turbopack: {
    root: "/Users/shyamolkonwar/Documents/Yantra AI/mvp/frontend"
  }
};

export default nextConfig;
