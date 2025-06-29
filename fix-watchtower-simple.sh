#!/bin/bash

# Simple script to fix Watchtower authentication for GHCR

echo "🔧 Fixing Watchtower authentication for GHCR"
echo "==========================================="

# Check if Docker config exists
if [ ! -f "/home/ec2-user/.docker/config.json" ]; then
    echo "❌ Docker config not found at /home/ec2-user/.docker/config.json"
    echo "Please login to ghcr.io first: docker login ghcr.io"
    exit 1
fi

echo "✓ Docker config found"

# Function to fix a single docker-compose file
fix_compose_file() {
    local file="$1"
    local project_name=$(basename $(dirname "$file"))
    
    echo ""
    echo "Processing: $file"
    echo "Project: $project_name"
    
    # Create backup
    cp "$file" "${file}.bak"
    
    # Create a temporary file with fixed configuration
    cat "$file" | awk '
    BEGIN { in_watchtower = 0; in_volumes = 0; in_env = 0; config_added = 0 }
    
    /^[[:space:]]*[[:alnum:]_-]*watchtower[[:alnum:]_-]*:/ { 
        in_watchtower = 1
        print
        next
    }
    
    in_watchtower && /^[[:space:]]+volumes:/ {
        in_volumes = 1
        print
        next
    }
    
    in_watchtower && in_volumes && /^[[:space:]]+-[[:space:]]+\/var\/run\/docker\.sock/ {
        print
        print "      - /home/ec2-user/.docker/config.json:/config.json:ro"
        config_added = 1
        next
    }
    
    in_watchtower && /^[[:space:]]+environment:/ {
        in_env = 1
        in_volumes = 0
        print
        next
    }
    
    # Skip REPO_USER and REPO_PASS lines
    in_watchtower && in_env && /REPO_USER=|REPO_PASS=/ {
        next
    }
    
    # Exit watchtower block on new service
    /^[[:alnum:]]/ && in_watchtower {
        in_watchtower = 0
        in_volumes = 0
        in_env = 0
    }
    
    # Exit sub-blocks on new property
    in_watchtower && /^[[:space:]]+[[:alnum:]_-]+:/ {
        in_volumes = 0
        in_env = 0
    }
    
    { print }
    ' > "${file}.tmp"
    
    # Check if the modification was successful
    if grep -q "/home/ec2-user/.docker/config.json:/config.json:ro" "${file}.tmp" && \
       ! grep -q "REPO_USER\|REPO_PASS" "${file}.tmp"; then
        mv "${file}.tmp" "$file"
        rm -f "${file}.bak"
        echo "  ✅ Fixed successfully"
        return 0
    else
        rm -f "${file}.tmp"
        mv "${file}.bak" "$file"
        echo "  ❌ Failed to fix (restored backup)"
        return 1
    fi
}

# Find all production docker-compose files with watchtower
echo ""
echo "Finding docker-compose files with watchtower..."

# List of known project directories
projects=(
    "/home/ec2-user/statushub"
    "/home/ec2-user/growthiq"
    "/home/ec2-user/birthdays-to-slack"
    "/home/ec2-user/account-leaser"
    "/home/ec2-user/slack-broker"
    "/home/ec2-user/slack-duo-verifier"
    "/home/ec2-user/symphoniq"
    "/home/ec2-user/privatemcp"
    "/home/ec2-user/leaser"
)

fixed_count=0
total_count=0

for project_dir in "${projects[@]}"; do
    if [ -f "$project_dir/docker-compose.yml" ]; then
        if grep -q "watchtower" "$project_dir/docker-compose.yml" 2>/dev/null; then
            total_count=$((total_count + 1))
            if fix_compose_file "$project_dir/docker-compose.yml"; then
                fixed_count=$((fixed_count + 1))
            fi
        fi
    fi
done

echo ""
echo "==========================================="
echo "Fixed $fixed_count out of $total_count files"
echo ""

# Restart watchtower containers
echo "Restarting Watchtower containers..."
containers=$(docker ps --format "{{.Names}}" | grep -i watchtower)

if [ -z "$containers" ]; then
    echo "No running Watchtower containers found"
else
    for container in $containers; do
        echo "  Restarting $container..."
        docker restart "$container" >/dev/null 2>&1
        if [ $? -eq 0 ]; then
            echo "    ✓ Restarted successfully"
        else
            echo "    ❌ Failed to restart"
        fi
    done
fi

echo ""
echo "🎉 Done!"
echo ""
echo "To verify, check Watchtower logs:"
echo "  docker logs <watchtower-container> --tail 20"
echo ""
echo "Look for authentication success messages for ghcr.io"