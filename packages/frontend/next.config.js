// next.config.js
/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'export',
  webpack: (config) => {
    // Add transpilePackages to ensure undici gets processed by Babel
    config.resolve.alias = {
      ...config.resolve.alias,
      undici: false, // Disable direct imports of undici
    };

    // Make sure we're transpiling the problematic module
    const transpileModules = ['undici'];
    const regexEqual = (x, y) => 
      x instanceof RegExp &&
      y instanceof RegExp &&
      x.source === y.source &&
      x.flags === y.flags;

    // Modify the oneOf rules
    config.module.rules.forEach((rule) => {
      if (rule.oneOf) {
        rule.oneOf.forEach((r) => {
          if (
            r.test &&
            r.test.toString().includes('tsx|ts|jsx|js|mjs') &&
            r.include === undefined
          ) {
            r.include = [
              r.include,
              /node_modules\/undici/,
            ].filter(Boolean);
          }
        });
      }
    });
    
    return config;
  },
  images: {
    unoptimized: true,
  },
};

module.exports = nextConfig;