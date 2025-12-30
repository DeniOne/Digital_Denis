const withPWA = require('next-pwa')({
    dest: 'public',
    register: true,
    skipWaiting: true,
    disable: process.env.NODE_ENV === 'development',
    runtimeCaching: [
        {
            urlPattern: /^https?.*$/,
            handler: 'NetworkFirst',
            options: {
                cacheName: 'offlineCache',
                expiration: {
                    maxEntries: 200,
                    maxAgeSeconds: 24 * 60 * 60, // 24 hours
                },
            },
        },
        {
            urlPattern: /\/_next\/static\/.*/i,
            handler: 'CacheFirst',
            options: {
                cacheName: 'static-resources',
                expiration: {
                    maxEntries: 100,
                    maxAgeSeconds: 7 * 24 * 60 * 60, // 7 days
                },
            },
        },
        {
            urlPattern: /\/api\/.*/i,
            handler: 'StaleWhileRevalidate',
            options: {
                cacheName: 'api-cache',
                expiration: {
                    maxEntries: 50,
                    maxAgeSeconds: 5 * 60, // 5 minutes
                },
            },
        },
    ],
});

const path = require('path');

/** @type {import('next').NextConfig} */
const nextConfig = {
    reactStrictMode: true,
    turbopack: {
        root: path.join(__dirname),
    },
    outputFileTracingRoot: path.join(__dirname),
};

module.exports = withPWA(nextConfig);
