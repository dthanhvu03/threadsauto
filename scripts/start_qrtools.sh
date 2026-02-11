#!/bin/bash

# Startup script for Qrtools service

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
QRTOOLS_DIR="$PROJECT_ROOT/qrtools"

echo "🚀 Starting Qrtools API Server..."

# Check if qrtools directory exists
if [ ! -d "$QRTOOLS_DIR" ]; then
    echo "❌ Error: Qrtools directory not found at $QRTOOLS_DIR"
    echo "Please ensure Qrtools is set up in the qrtools/ directory"
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Error: Node.js is not installed"
    echo "Please install Node.js 18+ to run Qrtools"
    exit 1
fi

# Check Node.js version
NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 18 ]; then
    echo "❌ Error: Node.js version 18+ is required (current: $(node -v))"
    exit 1
fi

# Navigate to qrtools directory
cd "$QRTOOLS_DIR"

# Install dependencies if node_modules doesn't exist
if [ ! -d "node_modules" ]; then
    echo "📦 Installing Qrtools dependencies..."
    npm install
fi

# Install Playwright browsers if needed
if [ ! -d "$HOME/.cache/ms-playwright" ]; then
    echo "🌐 Installing Playwright browsers..."
    npx playwright install chromium
fi

# Start API server
echo "✅ Starting Qrtools API Server on port 3000..."
npm run api
