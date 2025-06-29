#!/bin/bash

# Script to recreate Watchtower containers with proper config

echo "🔧 Recreating Watchtower containers with proper GHCR authentication"
echo "=================================================================="

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
    "/home/ec2-user/leaser"
)

for project_dir in "${projects[@]}"; do
    project_name=$(basename "$project_dir")
    
    if [ -f "$project_dir/docker-compose.yml" ]; then
        echo ""
        echo "Processing $project_name..."
        
        # Change to project directory
        cd "$project_dir"
        
        # Stop and remove the watchtower container
        echo "  Stopping watchtower container..."
        docker compose stop watchtower 2>/dev/null
        
        echo "  Removing watchtower container..."
        docker compose rm -f watchtower 2>/dev/null
        
        # Recreate the watchtower container with new config
        echo "  Creating watchtower container with new config..."
        docker compose up -d watchtower
        
        if [ $? -eq 0 ]; then
            echo "  ✅ Successfully recreated $project_name-watchtower"
        else
            echo "  ❌ Failed to recreate $project_name-watchtower"
        fi
    fi
done

echo ""
echo "=================================================================="
echo "✅ Container recreation complete!"
echo ""
echo "Now let's verify the authentication is working..."
echo ""

# Wait a moment for containers to start
sleep 5

# Check a few watchtower logs
for container in statushub-watchtower growthiq-watchtower slack-broker-watchtower; do
    if docker ps --format "{{.Names}}" | grep -q "^${container}$"; then
        echo "Checking $container logs:"
        docker logs "$container" --tail 5 | grep -E "(auth|unauthorized|403|pull)" || echo "  No authentication errors found in recent logs"
        echo ""
    fi
done

echo "To manually check any Watchtower container:"
echo "  docker logs <container-name> --tail 30"