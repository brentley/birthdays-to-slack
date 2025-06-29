#!/bin/bash

echo "🔍 Verifying GHCR Authentication Setup"
echo "===================================="
echo ""

# Check Docker config
echo "1. Checking Docker config file..."
if [ -f "/home/ec2-user/.docker/config.json" ]; then
    echo "   ✅ Docker config exists"
    if grep -q "ghcr.io" /home/ec2-user/.docker/config.json; then
        echo "   ✅ Contains ghcr.io authentication"
    else
        echo "   ❌ Missing ghcr.io authentication"
    fi
else
    echo "   ❌ Docker config not found"
fi

echo ""
echo "2. Testing direct Docker pull with current authentication..."
echo "   Attempting to pull ghcr.io/brentley/statushub:latest..."

if docker pull ghcr.io/brentley/statushub:latest 2>&1 | grep -q "Pull complete\|Image is up to date\|Downloaded newer image"; then
    echo "   ✅ Docker can pull from GHCR successfully!"
else
    echo "   ❌ Docker pull failed - authentication issue"
fi

echo ""
echo "3. Checking Watchtower container configurations..."
echo ""

# Check a sample of Watchtower containers
containers=(statushub-watchtower growthiq-watchtower slack-broker-watchtower)

for container in "${containers[@]}"; do
    if docker ps --format "{{.Names}}" | grep -q "^${container}$"; then
        echo "   Checking $container:"
        
        # Check mounts
        has_config_mount=$(docker inspect "$container" | jq -r '.[0].Mounts[] | select(.Destination == "/config.json") | .Source')
        if [ -n "$has_config_mount" ]; then
            echo "     ✅ Docker config mounted"
        else
            echo "     ❌ Docker config NOT mounted"
        fi
        
        # Check environment
        has_docker_config=$(docker inspect "$container" | jq -r '.[0].Config.Env[]' | grep -c "DOCKER_CONFIG=/config.json")
        if [ "$has_docker_config" -gt 0 ]; then
            echo "     ✅ DOCKER_CONFIG environment set"
        else
            echo "     ❌ DOCKER_CONFIG environment NOT set"
        fi
        
        echo ""
    fi
done

echo "4. Summary of docker-compose.yml files:"
echo ""

# Check all compose files
for compose_file in /home/ec2-user/*/docker-compose.yml; do
    if [ -f "$compose_file" ] && grep -q "watchtower" "$compose_file"; then
        project=$(basename $(dirname "$compose_file"))
        
        # Check for both required configs
        has_mount=$(grep -c "/home/ec2-user/.docker/config.json:/config.json:ro" "$compose_file")
        has_env=$(grep -c "DOCKER_CONFIG=/config.json" "$compose_file")
        
        if [ "$has_mount" -gt 0 ] && [ "$has_env" -gt 0 ]; then
            echo "   ✅ $project - Properly configured"
        else
            echo "   ❌ $project - Missing configuration"
            [ "$has_mount" -eq 0 ] && echo "      - Missing Docker config mount"
            [ "$has_env" -eq 0 ] && echo "      - Missing DOCKER_CONFIG environment"
        fi
    fi
done

echo ""
echo "===================================="
echo "🎯 Next Steps:"
echo ""
echo "1. Wait for Watchtower to run its next check cycle (every 5 minutes)"
echo "2. Monitor logs with: docker logs <watchtower-container> --tail 50"
echo "3. Look for successful image checks without authentication errors"
echo ""
echo "If you still see authentication errors after the next cycle:"
echo "- The GitHub token might be expired or invalid"
echo "- You may need to login again: docker login ghcr.io -u brentley"
echo ""