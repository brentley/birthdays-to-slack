#!/bin/bash

# Script to fix Watchtower authentication for GHCR across all VisiQuate projects

echo "Fixing Watchtower authentication for GHCR across all projects..."
echo "============================================"

# Find all docker-compose files that contain watchtower
compose_files=$(find /home/ec2-user -name "docker-compose*.yml" -type f -exec grep -l "watchtower" {} \; 2>/dev/null | grep -v ".git/" | grep -v "docker-compose.dev.yml" | grep -v "docker-compose.test.yml")

# Function to update watchtower configuration
update_watchtower_config() {
    local file="$1"
    echo ""
    echo "Processing: $file"
    
    # Create a backup
    cp "$file" "${file}.bak"
    
    # Read the file content
    content=$(cat "$file")
    
    # Check if it already has the correct config mount
    if grep -q "/home/ec2-user/.docker/config.json:/config.json:ro" "$file"; then
        echo "  ✓ Already has Docker config mount"
        
        # Check if it still has old REPO_USER/REPO_PASS variables
        if grep -q "REPO_USER\|REPO_PASS" "$file"; then
            echo "  ⚠ Found old REPO_USER/REPO_PASS variables, removing them..."
            # Remove REPO_USER and REPO_PASS lines
            sed -i '/- REPO_USER=/d' "$file"
            sed -i '/- REPO_PASS=/d' "$file"
            echo "  ✓ Removed old authentication variables"
        fi
    else
        echo "  ⚠ Missing Docker config mount, adding it..."
        
        # First, remove any existing REPO_USER and REPO_PASS lines
        sed -i '/- REPO_USER=/d' "$file"
        sed -i '/- REPO_PASS=/d' "$file"
        
        # Add the Docker config mount to watchtower volumes
        # This finds the watchtower service and adds the config mount after docker.sock
        awk '
        /watchtower:/ { in_watchtower=1 }
        in_watchtower && /volumes:/ { in_volumes=1 }
        in_watchtower && in_volumes && /\/var\/run\/docker.sock:\/var\/run\/docker.sock/ {
            print $0
            print "      - /home/ec2-user/.docker/config.json:/config.json:ro"
            next
        }
        in_watchtower && /^  [^ ]/ { in_watchtower=0; in_volumes=0 }
        { print }
        ' "$file" > "${file}.tmp" && mv "${file}.tmp" "$file"
        
        echo "  ✓ Added Docker config mount"
    fi
    
    # Verify the changes
    if grep -q "/home/ec2-user/.docker/config.json:/config.json:ro" "$file" && ! grep -q "REPO_USER\|REPO_PASS" "$file"; then
        echo "  ✅ Configuration fixed successfully"
        rm -f "${file}.bak"
    else
        echo "  ❌ Failed to fix configuration, restoring backup"
        mv "${file}.bak" "$file"
    fi
}

# Process all found docker-compose files
for file in $compose_files; do
    update_watchtower_config "$file"
done

echo ""
echo "============================================"
echo "Configuration updates complete!"
echo ""
echo "Now restarting affected Watchtower containers..."
echo ""

# Find and restart all watchtower containers
watchtower_containers=$(docker ps --format "table {{.Names}}" | grep -i watchtower | grep -v NAMES)

if [ -z "$watchtower_containers" ]; then
    echo "No running Watchtower containers found."
else
    for container in $watchtower_containers; do
        echo "Restarting $container..."
        docker restart "$container"
        if [ $? -eq 0 ]; then
            echo "  ✓ Successfully restarted $container"
        else
            echo "  ❌ Failed to restart $container"
        fi
    done
fi

echo ""
echo "============================================"
echo "All done! Watchtower authentication has been fixed."
echo ""
echo "To verify the fix, check the logs of any Watchtower container:"
echo "  docker logs <watchtower-container-name> --tail 50"
echo ""
echo "Look for successful image pull messages from ghcr.io"