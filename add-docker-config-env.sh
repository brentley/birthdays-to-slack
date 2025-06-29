#!/bin/bash

# Script to add DOCKER_CONFIG environment variable to Watchtower services

echo "🔧 Adding DOCKER_CONFIG environment variable to Watchtower services"
echo "================================================================"

# List of projects
projects=(
    "/home/ec2-user/statushub"
    "/home/ec2-user/growthiq"
    "/home/ec2-user/birthdays-to-slack"
    "/home/ec2-user/account-leaser"
    "/home/ec2-user/slack-broker"
    "/home/ec2-user/slack-duo-verifier"
    "/home/ec2-user/symphoniq"
    "/home/ec2-user/privatemcp"
)

for project_dir in "${projects[@]}"; do
    compose_file="$project_dir/docker-compose.yml"
    
    if [ ! -f "$compose_file" ]; then
        continue
    fi
    
    project_name=$(basename "$project_dir")
    echo ""
    echo "Processing $project_name..."
    
    # Check if DOCKER_CONFIG is already set
    if grep -q "DOCKER_CONFIG" "$compose_file"; then
        echo "  ✓ DOCKER_CONFIG already set"
        continue
    fi
    
    # Add DOCKER_CONFIG environment variable
    # Find the watchtower environment section and add the variable
    awk '
    BEGIN { in_watchtower = 0; in_env = 0; added = 0 }
    
    /^[[:space:]]*[[:alnum:]_-]*watchtower[[:alnum:]_-]*:/ { 
        in_watchtower = 1
    }
    
    in_watchtower && /^[[:space:]]+environment:/ {
        in_env = 1
        print
        next
    }
    
    in_watchtower && in_env && /^[[:space:]]+-[[:space:]]+WATCHTOWER_CLEANUP/ && !added {
        print "      - DOCKER_CONFIG=/config.json"
        added = 1
    }
    
    /^[[:alnum:]]/ && in_watchtower {
        in_watchtower = 0
        in_env = 0
    }
    
    { print }
    ' "$compose_file" > "${compose_file}.tmp" && mv "${compose_file}.tmp" "$compose_file"
    
    echo "  ✅ Added DOCKER_CONFIG environment variable"
done

echo ""
echo "================================================================"
echo "✅ Configuration update complete!"
echo ""
echo "Now recreating Watchtower containers with the updated config..."

# Recreate all watchtower containers
for project_dir in "${projects[@]}"; do
    if [ -f "$project_dir/docker-compose.yml" ]; then
        project_name=$(basename "$project_dir")
        echo ""
        echo "Recreating $project_name-watchtower..."
        cd "$project_dir"
        docker compose stop watchtower 2>/dev/null
        docker compose rm -f watchtower 2>/dev/null
        docker compose up -d watchtower
    fi
done

echo ""
echo "================================================================"
echo "🎉 All done! Waiting 10 seconds for containers to start..."
sleep 10

echo ""
echo "Checking for authentication errors in logs..."
echo ""

# Check a sample of watchtower logs
for container in statushub-watchtower growthiq-watchtower slack-broker-watchtower; do
    if docker ps --format "{{.Names}}" | grep -q "^${container}$"; then
        echo "=== $container ==="
        # Look for recent logs that show authentication status
        docker logs "$container" 2>&1 | tail -20 | grep -E "(Watchtower|auth|Found|manifest|pull|ghcr.io)" | tail -10
        echo ""
    fi
done

echo "To verify authentication is working, wait for the next update cycle and check:"
echo "  docker logs <watchtower-container> --tail 50"
echo ""
echo "You should see successful image checks without authentication errors."