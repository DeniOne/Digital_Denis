/** @type {import('next').NextConfig} */
const nextConfig = {
    reactStrictMode: true,
    // Next.js 16 works best with Turbopack for dev speed
    transpilePackages: ['lucide-react'],
    experimental: {
        turbo: {
            // Options for Turbopack
        },
    },
};

module.exports = nextConfig;
