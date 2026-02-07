import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  turbopack: {
    root: __dirname,
  },
  allowedDevOrigins: ["http://192.168.0.71:3000", "http://localhost:3000"],
  async redirects() {
    return [
      { source: "/app/imoveis", destination: "/app/setores", permanent: false },
      { source: "/ativos", destination: "/app/dashboard", permanent: false },
      { source: "/setores", destination: "/app/setores", permanent: false },
      { source: "/benchmark", destination: "/app/dashboard", permanent: false },
      { source: "/simulador", destination: "/app/dashboard", permanent: false },
      { source: "/forecast-check", destination: "/app/dashboard", permanent: false },
      { source: "/api-docs", destination: "/app/dashboard", permanent: false },
      { source: "/sobre", destination: "/app/sobre", permanent: false },
      { source: "/dashboard", destination: "/app/dashboard", permanent: false },
    ];
  },
};

export default nextConfig;
