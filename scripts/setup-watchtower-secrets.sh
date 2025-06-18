#!/bin/bash
# Script to configure GitHub secrets for Watchtower deployments

set -e

echo "🔧 Watchtower GitHub Secrets Configuration"
echo "=========================================="
echo ""

# Function to check if gh CLI is installed
check_gh_cli() {
    if ! command -v gh &> /dev/null; then
        echo "❌ GitHub CLI (gh) is not installed"
        echo "Install it from: https://cli.github.com/"
        exit 1
    fi
    
    # Check if authenticated
    if ! gh auth status &> /dev/null; then
        echo "❌ Not authenticated with GitHub"
        echo "Run: gh auth login"
        exit 1
    fi
}

# Function to set a secret
set_secret() {
    local name=$1
    local value=$2
    echo "Setting secret: $name"
    echo "$value" | gh secret set "$name"
}

# Main menu
show_menu() {
    echo "Choose configuration type:"
    echo "1) Single Watchtower instance"
    echo "2) Multiple Watchtower instances"
    echo "3) Show current secrets"
    echo "4) Generate secure token"
    echo "5) Exit"
    echo ""
    read -p "Enter choice [1-5]: " choice
    
    case $choice in
        1) configure_single ;;
        2) configure_multiple ;;
        3) show_secrets ;;
        4) generate_token ;;
        5) exit 0 ;;
        *) echo "Invalid choice"; show_menu ;;
    esac
}

# Configure single Watchtower
configure_single() {
    echo ""
    echo "📝 Single Watchtower Configuration"
    echo ""
    read -p "Enter Watchtower URL (e.g., http://18.118.142.110:8080): " url
    read -p "Enter Watchtower token: " -s token
    echo ""
    
    if [[ -z "$url" ]] || [[ -z "$token" ]]; then
        echo "❌ URL and token are required"
        return
    fi
    
    set_secret "WATCHTOWER_URL" "$url"
    set_secret "WATCHTOWER_TOKEN" "$token"
    
    echo "✅ Single Watchtower configuration saved"
    echo ""
    show_menu
}

# Configure multiple Watchtowers
configure_multiple() {
    echo ""
    echo "📝 Multiple Watchtower Configuration"
    echo ""
    echo "You'll be adding multiple Watchtower endpoints."
    echo "Press Ctrl+C to cancel at any time."
    echo ""
    
    endpoints="["
    first=true
    
    while true; do
        echo "--- New Watchtower Instance ---"
        read -p "Name (e.g., prod, staging): " name
        if [[ -z "$name" ]]; then
            break
        fi
        
        read -p "URL (e.g., http://server:8080): " url
        read -p "Token: " -s token
        echo ""
        
        if [[ -n "$url" ]] && [[ -n "$token" ]]; then
            if [[ "$first" == "false" ]]; then
                endpoints+=","
            fi
            endpoints+="{\"name\":\"$name\",\"url\":\"$url\",\"token\":\"$token\"}"
            first=false
            echo "✅ Added: $name"
        fi
        
        read -p "Add another? (y/N): " another
        if [[ "$another" != "y" ]] && [[ "$another" != "Y" ]]; then
            break
        fi
        echo ""
    done
    
    endpoints+="]"
    
    if [[ "$endpoints" != "[]" ]]; then
        set_secret "WATCHTOWER_ENDPOINTS" "$endpoints"
        echo "✅ Multiple Watchtower configuration saved"
    else
        echo "❌ No endpoints configured"
    fi
    
    echo ""
    show_menu
}

# Show current secrets
show_secrets() {
    echo ""
    echo "📋 Current GitHub Secrets:"
    echo ""
    gh secret list | grep -E "WATCHTOWER|DEPLOY" || echo "No Watchtower secrets found"
    echo ""
    show_menu
}

# Generate secure token
generate_token() {
    echo ""
    echo "🔑 Generating secure token..."
    echo ""
    token=$(openssl rand -base64 32)
    echo "Token: $token"
    echo ""
    echo "Copy this token and use it in your Watchtower configuration"
    echo ""
    show_menu
}

# Main execution
check_gh_cli
show_menu