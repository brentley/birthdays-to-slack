#!/usr/bin/env python3
"""
Fix Watchtower authentication for GitHub Container Registry (ghcr.io)
across all VisiQuate projects.
"""

import os
import re
import shutil
import subprocess
import sys
import yaml
from pathlib import Path

def find_docker_compose_files():
    """Find all docker-compose files containing watchtower."""
    compose_files = []
    
    # Search in common project locations
    search_paths = [
        "/home/ec2-user",
        "/home/ec2-user/git"
    ]
    
    for search_path in search_paths:
        if not os.path.exists(search_path):
            continue
            
        for root, dirs, files in os.walk(search_path):
            # Skip .git directories and test/dev compose files
            if '.git' in root:
                continue
                
            for file in files:
                if file.startswith('docker-compose') and file.endswith('.yml'):
                    # Skip dev and test files
                    if 'dev' in file or 'test' in file:
                        continue
                        
                    filepath = os.path.join(root, file)
                    
                    # Check if file contains watchtower
                    try:
                        with open(filepath, 'r') as f:
                            content = f.read()
                            if 'watchtower' in content:
                                compose_files.append(filepath)
                    except Exception:
                        pass
    
    # Remove duplicates
    compose_files = list(set(compose_files))
    return sorted(compose_files)


def update_watchtower_config(filepath):
    """Update watchtower configuration in a docker-compose file."""
    print(f"\nProcessing: {filepath}")
    
    # Create backup
    backup_path = f"{filepath}.bak"
    shutil.copy2(filepath, backup_path)
    
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        
        # Parse YAML
        data = yaml.safe_load(content)
        
        if not data or 'services' not in data:
            print("  ⚠ Invalid docker-compose structure")
            return False
        
        # Find watchtower service
        watchtower_service = None
        watchtower_key = None
        
        for service_name, service_config in data['services'].items():
            if 'watchtower' in service_name.lower():
                watchtower_service = service_config
                watchtower_key = service_name
                break
        
        if not watchtower_service:
            print("  ⚠ No watchtower service found")
            return False
        
        print(f"  ✓ Found watchtower service: {watchtower_key}")
        
        # Update volumes
        if 'volumes' not in watchtower_service:
            watchtower_service['volumes'] = []
        
        docker_config_mount = "/home/ec2-user/.docker/config.json:/config.json:ro"
        
        # Check if config mount already exists
        has_config_mount = any(docker_config_mount in str(v) for v in watchtower_service['volumes'])
        
        if not has_config_mount:
            watchtower_service['volumes'].append(docker_config_mount)
            print("  ✓ Added Docker config mount")
        else:
            print("  ✓ Docker config mount already present")
        
        # Remove old authentication environment variables
        if 'environment' in watchtower_service:
            new_env = []
            removed_vars = []
            
            for env_var in watchtower_service['environment']:
                if isinstance(env_var, str):
                    if not (env_var.startswith('REPO_USER=') or env_var.startswith('REPO_PASS=')):
                        new_env.append(env_var)
                    else:
                        removed_vars.append(env_var.split('=')[0])
                elif isinstance(env_var, dict):
                    # Handle dictionary format
                    if 'REPO_USER' not in env_var and 'REPO_PASS' not in env_var:
                        new_env.append(env_var)
                    else:
                        removed_vars.extend(env_var.keys())
            
            if removed_vars:
                watchtower_service['environment'] = new_env
                print(f"  ✓ Removed old authentication variables: {', '.join(removed_vars)}")
        
        # Write updated content back
        # We need to preserve the original formatting as much as possible
        # So we'll do a targeted replacement
        
        # Read original content line by line
        with open(filepath, 'r') as f:
            lines = f.readlines()
        
        # Find watchtower service block
        in_watchtower = False
        in_volumes = False
        in_environment = False
        new_lines = []
        i = 0
        
        while i < len(lines):
            line = lines[i]
            
            # Check if we're entering watchtower service
            if re.match(r'^\s*\w*watchtower\w*:', line, re.IGNORECASE):
                in_watchtower = True
                new_lines.append(line)
            elif in_watchtower and re.match(r'^[^\s]', line):
                # Exiting watchtower service (new top-level key)
                in_watchtower = False
                in_volumes = False
                in_environment = False
                new_lines.append(line)
            elif in_watchtower:
                # Inside watchtower service
                if re.match(r'^\s*volumes:', line):
                    in_volumes = True
                    in_environment = False
                    new_lines.append(line)
                    
                    # Process volumes
                    i += 1
                    volumes_added = False
                    config_mount_exists = False
                    
                    while i < len(lines):
                        next_line = lines[i]
                        if re.match(r'^\s*-\s*', next_line):
                            # This is a volume entry
                            if docker_config_mount in next_line:
                                config_mount_exists = True
                            new_lines.append(next_line)
                            i += 1
                        elif re.match(r'^\s*[a-zA-Z]', next_line):
                            # New section started
                            if not config_mount_exists and not volumes_added:
                                # Add the config mount with proper indentation
                                indent = '      '  # Standard docker-compose indentation
                                new_lines.append(f"{indent}- {docker_config_mount}\n")
                                volumes_added = True
                            break
                        else:
                            i += 1
                    
                    i -= 1  # Adjust because we'll increment at end of loop
                    in_volumes = False
                    
                elif re.match(r'^\s*environment:', line):
                    in_environment = True
                    in_volumes = False
                    new_lines.append(line)
                    
                    # Process environment variables
                    i += 1
                    while i < len(lines):
                        next_line = lines[i]
                        if re.match(r'^\s*-\s*', next_line):
                            # This is an environment entry
                            if 'REPO_USER=' not in next_line and 'REPO_PASS=' not in next_line:
                                new_lines.append(next_line)
                            i += 1
                        elif re.match(r'^\s*[a-zA-Z]', next_line):
                            # New section started
                            break
                        else:
                            i += 1
                    
                    i -= 1  # Adjust because we'll increment at end of loop
                    in_environment = False
                else:
                    # Regular line in watchtower service
                    if not ('REPO_USER' in line or 'REPO_PASS' in line):
                        new_lines.append(line)
            else:
                # Outside watchtower service
                new_lines.append(line)
            
            i += 1
        
        # Write the updated content
        with open(filepath, 'w') as f:
            f.writelines(new_lines)
        
        print("  ✅ Configuration updated successfully")
        
        # Remove backup
        os.remove(backup_path)
        return True
        
    except Exception as e:
        print(f"  ❌ Error updating configuration: {e}")
        # Restore backup
        shutil.move(backup_path, filepath)
        return False


def restart_watchtower_containers():
    """Restart all running watchtower containers."""
    print("\nRestarting Watchtower containers...")
    
    try:
        # Get list of running watchtower containers
        result = subprocess.run(
            ["docker", "ps", "--format", "{{.Names}}", "--filter", "name=watchtower"],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print("  ❌ Failed to list containers")
            return
        
        containers = [c for c in result.stdout.strip().split('\n') if c]
        
        if not containers:
            print("  No running Watchtower containers found")
            return
        
        for container in containers:
            print(f"  Restarting {container}...")
            restart_result = subprocess.run(
                ["docker", "restart", container],
                capture_output=True
            )
            
            if restart_result.returncode == 0:
                print(f"    ✓ Successfully restarted")
            else:
                print(f"    ❌ Failed to restart")
                
    except Exception as e:
        print(f"  ❌ Error restarting containers: {e}")


def check_docker_config():
    """Check if Docker config file exists with GHCR authentication."""
    config_path = "/home/ec2-user/.docker/config.json"
    
    if not os.path.exists(config_path):
        print("❌ Docker config file not found at /home/ec2-user/.docker/config.json")
        return False
    
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            
        if 'auths' in config and 'ghcr.io' in config['auths']:
            print("✓ Docker config file contains ghcr.io authentication")
            return True
        else:
            print("❌ Docker config file does not contain ghcr.io authentication")
            return False
    except Exception as e:
        print(f"❌ Error reading Docker config: {e}")
        return False


def main():
    print("🔧 Fixing Watchtower authentication for GHCR across all VisiQuate projects")
    print("=" * 70)
    
    # Check Docker config
    if not check_docker_config():
        print("\n⚠️  Please ensure Docker is logged in to ghcr.io first:")
        print("   docker login ghcr.io -u YOUR_GITHUB_USERNAME")
        sys.exit(1)
    
    # Find all docker-compose files
    compose_files = find_docker_compose_files()
    
    if not compose_files:
        print("\nNo docker-compose files with watchtower found.")
        return
    
    print(f"\nFound {len(compose_files)} docker-compose files with watchtower")
    
    # Update each file
    success_count = 0
    for filepath in compose_files:
        if update_watchtower_config(filepath):
            success_count += 1
    
    print(f"\n{'=' * 70}")
    print(f"✅ Successfully updated {success_count}/{len(compose_files)} files")
    
    # Restart containers
    restart_watchtower_containers()
    
    print("\n🎉 All done!")
    print("\nTo verify the fix, check the logs of any Watchtower container:")
    print("  docker logs <watchtower-container-name> --tail 50")
    print("\nLook for successful image pull messages from ghcr.io")


if __name__ == "__main__":
    main()