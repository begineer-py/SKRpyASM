#!/bin/bash
# Clean Vite and TypeScript caches
rm -rf node_modules/.vite
rm -rf node_modules/.ts-cache
rm -rf .vite
rm -rf dist

# Clear tsc build info
find . -name "tsconfig.*.tsbuildinfo" -delete
find . -name ".tsbuildinfo" -delete

echo "✅ Caches cleared. Run 'npm run dev' to rebuild."
