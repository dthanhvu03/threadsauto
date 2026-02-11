#!/bin/bash
# Install Node.js dependencies for scripts directory

set -e

echo "=========================================="
echo "Installing Node.js Dependencies"
echo "=========================================="
echo ""

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed!"
    echo "   Please install Node.js 18+ first"
    exit 1
fi

# Check Node.js version
NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 18 ]; then
    echo "❌ Node.js version must be 18 or higher"
    echo "   Current version: $(node -v)"
    exit 1
fi

echo "✅ Node.js version: $(node -v)"
echo ""

# Navigate to scripts directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "Installing dependencies from package.json..."
echo ""

# Install dependencies
if npm install; then
    echo ""
    echo "✅ Dependencies installed successfully!"
    echo ""
    echo "Installing Playwright browsers..."
    echo ""
    
    # Install Playwright browsers
    if npx playwright install chromium; then
        echo ""
        echo "=========================================="
        echo "✅ Setup complete!"
        echo "=========================================="
        echo ""
        echo "You can now use the feed extractor script."
    else
        echo ""
        echo "⚠️  Dependencies installed, but Playwright browser installation failed"
        echo "   You can install it manually with: npx playwright install chromium"
    fi
else
    echo ""
    echo "❌ Failed to install dependencies"
    exit 1
fi
