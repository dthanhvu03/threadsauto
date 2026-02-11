#!/bin/bash
# UI/UX Pro Max Helper Script
# Quick access to design system generation and searches

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
UI_UX_SCRIPT="$PROJECT_ROOT/.shared/ui-ux-pro-max/scripts/search.py"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check Python
check_python() {
    if ! command -v python3 &> /dev/null; then
        echo "❌ Python 3 is not installed. Please install it first."
        exit 1
    fi
}

# Check if UI/UX Pro Max script exists
check_script() {
    if [ ! -f "$UI_UX_SCRIPT" ]; then
        echo "❌ UI/UX Pro Max script not found at: $UI_UX_SCRIPT"
        exit 1
    fi
}

# Show menu
show_menu() {
    echo ""
    echo "=========================================="
    echo "  UI/UX PRO MAX HELPER"
    echo "=========================================="
    echo ""
    echo "1. Generate Design System (with persist)"
    echo "2. Generate Design System (console only)"
    echo "3. Search UX Guidelines"
    echo "4. Search Style Options"
    echo "5. Search Color Palettes"
    echo "6. Search Typography"
    echo "7. Search Stack Guidelines (Vue)"
    echo "8. Search Stack Guidelines (html-tailwind)"
    echo ""
    echo "0. Exit"
    echo ""
    read -p "Chọn option (0-8): " choice
    echo ""
}

# Generate Design System with persist
generate_design_system_persist() {
    read -p "Enter query (e.g., 'SaaS dashboard automation'): " query
    read -p "Enter project name (default: Threads Automation): " project_name
    project_name=${project_name:-"Threads Automation"}
    read -p "Enter page name (optional, e.g., 'dashboard'): " page_name
    
    echo ""
    echo "${BLUE}Generating design system...${NC}"
    echo ""
    
    if [ -z "$page_name" ]; then
        python3 "$UI_UX_SCRIPT" "$query" --design-system --persist -p "$project_name" -f markdown
    else
        python3 "$UI_UX_SCRIPT" "$query" --design-system --persist -p "$project_name" --page "$page_name" -f markdown
    fi
    
    echo ""
    echo "${GREEN}✅ Design system saved to design-system/${project_name// /-}/MASTER.md${NC}"
    if [ -n "$page_name" ]; then
        echo "${GREEN}✅ Page override saved to design-system/${project_name// /-}/pages/${page_name}.md${NC}"
    fi
}

# Generate Design System (console only)
generate_design_system_console() {
    read -p "Enter query (e.g., 'SaaS dashboard automation'): " query
    read -p "Enter project name (optional): " project_name
    
    echo ""
    echo "${BLUE}Generating design system...${NC}"
    echo ""
    
    if [ -z "$project_name" ]; then
        python3 "$UI_UX_SCRIPT" "$query" --design-system -f markdown
    else
        python3 "$UI_UX_SCRIPT" "$query" --design-system -p "$project_name" -f markdown
    fi
}

# Search UX Guidelines
search_ux() {
    read -p "Enter search keywords (e.g., 'animation accessibility'): " keywords
    read -p "Max results (default: 5): " max_results
    max_results=${max_results:-5}
    
    echo ""
    echo "${BLUE}Searching UX guidelines...${NC}"
    echo ""
    
    python3 "$UI_UX_SCRIPT" "$keywords" --domain ux -n "$max_results"
}

# Search Style Options
search_style() {
    read -p "Enter search keywords (e.g., 'glassmorphism minimalism'): " keywords
    read -p "Max results (default: 3): " max_results
    max_results=${max_results:-3}
    
    echo ""
    echo "${BLUE}Searching style options...${NC}"
    echo ""
    
    python3 "$UI_UX_SCRIPT" "$keywords" --domain style -n "$max_results"
}

# Search Color Palettes
search_color() {
    read -p "Enter search keywords (e.g., 'saas dashboard'): " keywords
    read -p "Max results (default: 3): " max_results
    max_results=${max_results:-3}
    
    echo ""
    echo "${BLUE}Searching color palettes...${NC}"
    echo ""
    
    python3 "$UI_UX_SCRIPT" "$keywords" --domain color -n "$max_results"
}

# Search Typography
search_typography() {
    read -p "Enter search keywords (e.g., 'elegant professional'): " keywords
    read -p "Max results (default: 3): " max_results
    max_results=${max_results:-3}
    
    echo ""
    echo "${BLUE}Searching typography...${NC}"
    echo ""
    
    python3 "$UI_UX_SCRIPT" "$keywords" --domain typography -n "$max_results"
}

# Search Stack Guidelines (Vue)
search_stack_vue() {
    read -p "Enter search keywords (e.g., 'dashboard components'): " keywords
    read -p "Max results (default: 3): " max_results
    max_results=${max_results:-3}
    
    echo ""
    echo "${BLUE}Searching Vue guidelines...${NC}"
    echo ""
    
    python3 "$UI_UX_SCRIPT" "$keywords" --stack vue -n "$max_results"
}

# Search Stack Guidelines (html-tailwind)
search_stack_tailwind() {
    read -p "Enter search keywords (e.g., 'layout responsive'): " keywords
    read -p "Max results (default: 3): " max_results
    max_results=${max_results:-3}
    
    echo ""
    echo "${BLUE}Searching html-tailwind guidelines...${NC}"
    echo ""
    
    python3 "$UI_UX_SCRIPT" "$keywords" --stack html-tailwind -n "$max_results"
}

# Main loop
main() {
    check_python
    check_script
    
    while true; do
        show_menu
        
        case $choice in
            1)
                generate_design_system_persist
                ;;
            2)
                generate_design_system_console
                ;;
            3)
                search_ux
                ;;
            4)
                search_style
                ;;
            5)
                search_color
                ;;
            6)
                search_typography
                ;;
            7)
                search_stack_vue
                ;;
            8)
                search_stack_tailwind
                ;;
            0)
                echo "👋 Goodbye!"
                exit 0
                ;;
            *)
                echo "❌ Invalid option. Please try again."
                ;;
        esac
        
        echo ""
        read -p "Press Enter to continue..."
    done
}

# Run main
main
