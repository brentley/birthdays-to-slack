# Watchtower GHCR Authentication Fix Summary

## Problem
Watchtower containers were showing "auth not present" errors when trying to pull images from GitHub Container Registry (ghcr.io).

## Root Cause
The Watchtower containers were configured with incorrect authentication methods:
- Using `REPO_USER` and `REPO_PASS` environment variables (which don't work for GHCR)
- Missing proper Docker config file mount
- Missing `DOCKER_CONFIG` environment variable

## Solution Implemented

### 1. Fixed Configuration
For each Watchtower service, the following changes were made:

```yaml
watchtower:
  image: containrrr/watchtower
  volumes:
    - /var/run/docker.sock:/var/run/docker.sock
    - /home/ec2-user/.docker/config.json:/config.json:ro  # Added this
  environment:
    - DOCKER_CONFIG=/config.json  # Added this
    - WATCHTOWER_CLEANUP=true
    - WATCHTOWER_INCLUDE_STOPPED=false
    - WATCHTOWER_SCOPE=<project-name>
    - WATCHTOWER_POLL_INTERVAL=300
    # Removed REPO_USER and REPO_PASS
```

### 2. Projects Fixed
✅ **Successfully configured (8 projects):**
- statushub
- growthiq
- birthdays-to-slack
- account-leaser
- slack-broker
- slack-duo-verifier
- symphoniq
- privatemcp

⚠️ **Partially configured (1 project):**
- leaser (configuration updated but container recreation failed due to missing .env file)

❌ **Not applicable (1 backup):**
- symphoniq-backup-20250618 (backup directory, not active)

### 3. Verification
- ✅ Docker can pull directly from ghcr.io (authentication works)
- ✅ All active Watchtower containers have proper mounts and environment
- ✅ Configuration files updated correctly

## Scripts Created
The following scripts were created in `/home/ec2-user/git/birthdays-to-slack/`:

1. `fix-watchtower-simple.sh` - Main script to fix Watchtower configurations
2. `add-docker-config-env.sh` - Script to add DOCKER_CONFIG environment variable
3. `recreate-watchtower-containers.sh` - Script to recreate containers with new config
4. `verify-ghcr-auth.sh` - Verification script to check authentication setup

## Next Steps

1. **Monitor Watchtower logs** after the next update cycle (every 5 minutes):
   ```bash
   docker logs <watchtower-container> --tail 50
   ```

2. **Look for successful pulls** without authentication errors:
   - You should see messages like "Found new image" or "Image is up to date"
   - No more "403 Forbidden" or "auth: not present" errors

3. **If issues persist**, the GitHub token might be expired:
   ```bash
   docker login ghcr.io -u brentley
   ```

## Monitoring Commands

Check specific Watchtower container:
```bash
docker logs statushub-watchtower --tail 30
```

Check all Watchtower containers for errors:
```bash
for c in $(docker ps --format "{{.Names}}" | grep watchtower); do
  echo "=== $c ==="
  docker logs "$c" 2>&1 | tail -10 | grep -E "(auth|403|unauthorized|Found|pull)"
  echo
done
```

Verify configuration:
```bash
docker inspect <watchtower-container> | jq '.[0] | {
  Mounts: .Mounts | map(select(.Destination == "/config.json")),
  DockerConfig: .Config.Env | map(select(. | contains("DOCKER_CONFIG")))
}'
```

## Cleanup
All backup files (*.bak) were automatically removed after successful updates.