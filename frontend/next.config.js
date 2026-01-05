/** @type {import('next').NextConfig} */
const nextConfig = {
    output: 'export',
    distDir: 'out',
    images: {
        unoptimized: true,
    },
    reactStrictMode: true,
    // Next.js 16 works best with Turbopack for dev speed
    transpilePackages: ['lucide-react'],
    experimental: {
        // Experimental options
    },
};

module.exports = nextConfig;
