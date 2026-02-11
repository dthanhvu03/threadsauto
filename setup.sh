#!/bin/bash
# Unified setup script for Threads Automation Tool
# Combines all setup and utility scripts into one

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Show menu
show_menu() {
    echo ""
    echo "=========================================="
    echo "THREADS AUTOMATION TOOL - SETUP"
    echo "=========================================="
    echo ""
    echo "1. Full Setup (venv + dependencies + Playwright)"
    echo "2. Install Dependencies Only"
    echo "3. Install aiofiles"
    echo "4. Setup npm Global Directory"
    echo "5. Fix npm Permissions"
    echo "6. Setup UI UX Pro Max"
    echo "7. Check Port 8000"
    echo "8. Kill Port 8000"
    echo ""
    echo "0. Exit"
    echo ""
    read -p "Chọn option (0-8): " choice
    echo ""
}

# 1. Full Setup
full_setup() {
    echo "🚀 Đang thiết lập Threads Automation Tool..."
    echo ""
    
    # Check Python version
    echo "📋 Đang kiểm tra phiên bản Python..."
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
    
    if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 11 ]); then
        echo "❌ Error: Python 3.11+ required, found $PYTHON_VERSION"
        exit 1
    fi
    
    echo "✅ Python $PYTHON_VERSION (OK)"
    echo ""
    
    # Check requirements.txt
    if [ ! -f "requirements.txt" ]; then
        echo "❌ Error: requirements.txt not found"
        exit 1
    fi
    
    # Check venv
    if [ -d "venv" ]; then
        echo "⚠️  Virtual environment đã tồn tại (venv/)"
        read -p "   Bạn có muốn tạo lại? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo "🗑️  Đang xóa venv cũ..."
            rm -rf venv
        else
            echo "📦 Sử dụng venv hiện có..."
            SKIP_VENV_CREATE=true
        fi
    fi
    
    # Create venv
    if [ "$SKIP_VENV_CREATE" != "true" ]; then
        echo "📦 Đang tạo virtual environment..."
        python3 -m venv venv
    fi
    
    # Activate venv
    echo "✅ Đang kích hoạt virtual environment..."
    source venv/bin/activate
    
    # Upgrade pip
    echo "⬆️  Đang nâng cấp pip..."
    pip install --upgrade pip --quiet
    
    # Install dependencies
    echo "📥 Đang cài đặt dependencies..."
    pip install -r requirements.txt
    
    # Install Playwright browsers (Python)
    echo "🌐 Đang cài đặt Playwright browsers (Python)..."
    playwright install chromium
    
    # Install Node.js dependencies (for feed extraction)
    echo "📦 Đang kiểm tra Node.js..."
    if command -v node &> /dev/null; then
        NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
        if [ "$NODE_VERSION" -ge 18 ]; then
            echo "✅ Node.js $(node -v) detected"
            echo "📥 Đang cài đặt Node.js dependencies..."
            cd scripts
            if [ -f "package.json" ]; then
                npm install
                echo "🌐 Đang cài đặt Playwright browsers (Node.js)..."
                npx playwright install chromium
                cd ..
                echo "✅ Node.js dependencies installed"
            else
                echo "⚠️  package.json not found in scripts/, skipping Node.js setup"
                cd ..
            fi
        else
            echo "⚠️  Node.js version must be 18+, found $(node -v), skipping Node.js setup"
        fi
    else
        echo "⚠️  Node.js not found, skipping Node.js dependencies (feed extraction will not work)"
    fi
    
    # Create directories
    echo "📁 Đang tạo các thư mục..."
    mkdir -p profiles
    mkdir -p logs
    mkdir -p jobs
    
    echo ""
    echo "✅ Hoàn tất thiết lập!"
    echo ""
    echo "📝 Các bước tiếp theo:"
    echo "   source venv/bin/activate"
    echo "   python main.py --account account_01 --content 'Xin chào Threads!'"
    echo ""
}

# 2. Install Dependencies Only
install_dependencies() {
    echo "📥 Đang cài đặt dependencies..."
    
    if [ ! -f "requirements.txt" ]; then
        echo "❌ Error: requirements.txt not found"
        exit 1
    fi
    
    if [ ! -d "venv" ]; then
        echo "❌ Error: venv not found. Run 'Full Setup' first."
        exit 1
    fi
    
    source venv/bin/activate
    pip install -r requirements.txt
    
    echo "✅ Dependencies installed!"
    echo ""
}

# 3. Install aiofiles
install_aiofiles() {
    echo "📥 Đang cài đặt aiofiles..."
    
    if [ -d "venv" ]; then
        source venv/bin/activate
    fi
    
    pip install aiofiles>=23.2.1
    
    echo "Verifying installation..."
    python -c "import aiofiles; print('✓ aiofiles installed successfully')" || echo "✗ Installation failed"
    echo ""
}

# 4. Setup npm Global Directory
setup_npm_global() {
    echo "🔧 Setting up npm global directory..."
    
    mkdir -p ~/.npm-global
    npm config set prefix "$HOME/.npm-global"
    
    echo "✅ npm prefix set to: $(npm config get prefix)"
    
    if ! grep -q "npm-global/bin" ~/.bashrc; then
        echo '' >> ~/.bashrc
        echo '# npm global packages' >> ~/.bashrc
        echo 'export PATH=$HOME/.npm-global/bin:$PATH' >> ~/.bashrc
        echo "✅ Added PATH to ~/.bashrc"
    else
        echo "✅ PATH already in ~/.bashrc"
    fi
    
    export PATH=$HOME/.npm-global/bin:$PATH
    
    echo "✅ PATH updated for current session"
    echo ""
    echo "📦 Now you can install global packages:"
    echo "   npm install -g uipro-cli"
    echo ""
}

# 5. Fix npm Permissions
fix_npm_permissions() {
    echo "🔧 Đang fix npm permissions..."
    echo ""
    
    mkdir -p ~/.npm-global
    npm config set prefix "$HOME/.npm-global"
    
    CURRENT_PREFIX=$(npm config get prefix)
    echo "✅ npm prefix: $CURRENT_PREFIX"
    echo ""
    
    export PATH=$HOME/.npm-global/bin:$PATH
    
    if ! grep -q "npm-global/bin" ~/.bashrc 2>/dev/null; then
        echo '' >> ~/.bashrc
        echo '# npm global packages' >> ~/.bashrc
        echo 'export PATH=$HOME/.npm-global/bin:$PATH' >> ~/.bashrc
        echo "✅ Đã thêm PATH vào ~/.bashrc"
    fi
    
    echo ""
    echo "✅ Đã fix npm permissions!"
    echo ""
}

# 6. Setup UI UX Pro Max
setup_ui_ux_pro_max() {
    echo "🎨 Đang thiết lập UI UX Pro Max cho Cursor..."
    echo ""
    
    # Check Node.js
    if ! command -v node &> /dev/null; then
        echo "❌ Error: Node.js chưa được cài đặt"
        exit 1
    fi
    
    NODE_VERSION=$(node --version)
    echo "✅ Node.js $NODE_VERSION (OK)"
    echo ""
    
    # Check npm
    if ! command -v npm &> /dev/null; then
        echo "❌ Error: npm chưa được cài đặt"
        exit 1
    fi
    
    # Setup npm global
    mkdir -p ~/.npm-global
    npm config set prefix "$HOME/.npm-global"
    export PATH=$HOME/.npm-global/bin:$PATH
    
    if ! grep -q "npm-global/bin" ~/.bashrc 2>/dev/null; then
        echo '' >> ~/.bashrc
        echo '# npm global packages' >> ~/.bashrc
        echo 'export PATH=$HOME/.npm-global/bin:$PATH' >> ~/.bashrc
    fi
    
    # Install uipro-cli
    echo "📥 Đang cài đặt uipro-cli..."
    npm install -g uipro-cli
    
    # Initialize
    echo ""
    echo "🚀 Đang khởi tạo UI UX Pro Max cho Cursor..."
    export PATH=$HOME/.npm-global/bin:$PATH
    uipro init --ai cursor
    
    echo ""
    echo "✅ Hoàn tất thiết lập UI UX Pro Max!"
    echo ""
}

# 7. Check Port 8000
check_port() {
    PORT=8000
    
    echo "Checking for processes using port $PORT..."
    echo ""
    
    PID=$(lsof -ti:$PORT 2>/dev/null || fuser $PORT/tcp 2>/dev/null | awk '{print $1}')
    
    if [ -z "$PID" ]; then
        echo "✓ Port $PORT is free"
        echo ""
        echo "You can start the server with:"
        echo "  python backend/main.py"
        return
    fi
    
    echo "⚠ Port $PORT is in use by process(es):"
    ps aux | grep -E "PID|$PID" | head -2
    echo ""
    
    for pid in $PID; do
        echo "Process $pid:"
        ps -p $pid -o pid,cmd --no-headers 2>/dev/null || echo "  (Process may have ended)"
        echo ""
    done
    
    echo "Options:"
    echo "1. Kill process(es) using port $PORT"
    echo "2. Use a different port"
    echo ""
    read -p "Kill process(es)? (y/N): " answer
    
    if [[ "$answer" =~ ^[Yy]$ ]]; then
        echo "Killing process(es)..."
        for pid in $PID; do
            kill -9 $pid 2>/dev/null && echo "✓ Killed process $pid" || echo "✗ Failed to kill process $pid"
        done
        sleep 1
        echo ""
        echo "✓ Port $PORT should now be free"
    else
        echo ""
        echo "To use a different port, modify backend/main.py"
    fi
    echo ""
}

# 8. Kill Port 8000
kill_port() {
    PORT=8000
    
    echo "Finding processes using port $PORT..."
    
    PIDS=$(lsof -ti:$PORT 2>/dev/null)
    
    if [ -z "$PIDS" ]; then
        echo "✓ Port $PORT is already free"
        return
    fi
    
    echo "Found processes: $PIDS"
    echo ""
    
    for pid in $PIDS; do
        echo "Process $pid:"
        ps -p $pid -o pid,cmd --no-headers 2>/dev/null || echo "  (Process may have ended)"
    done
    
    echo ""
    echo "Killing processes..."
    
    for pid in $PIDS; do
        if kill -9 $pid 2>/dev/null; then
            echo "✓ Killed process $pid"
        else
            echo "✗ Failed to kill process $pid (may have already ended)"
        fi
    done
    
    sleep 1
    
    if lsof -ti:$PORT 2>/dev/null > /dev/null; then
        echo ""
        echo "⚠ Warning: Port $PORT may still be in use"
    else
        echo ""
        echo "✓ Port $PORT is now free"
        echo ""
        echo "You can now start the server with:"
        echo "  python backend/main.py"
    fi
    echo ""
}

# Main loop
while true; do
    show_menu
    
    case $choice in
        1)
            full_setup
            ;;
        2)
            install_dependencies
            ;;
        3)
            install_aiofiles
            ;;
        4)
            setup_npm_global
            ;;
        5)
            fix_npm_permissions
            ;;
        6)
            setup_ui_ux_pro_max
            ;;
        7)
            check_port
            ;;
        8)
            kill_port
            ;;
        0)
            echo "👋 Goodbye!"
            exit 0
            ;;
        *)
            echo "❌ Invalid option. Please choose 0-8."
            ;;
    esac
    
    read -p "Press Enter to continue..."
done
