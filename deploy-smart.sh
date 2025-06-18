#!/bin/bash
set -euo pipefail

# Smart deploy script that detects if running on server or remotely

# Configuration
PROJECT_NAME="birthdays-to-slack"
DEPLOY_SERVER="ec2-user@18.118.142.110"
REMOTE_PATH="~/${PROJECT_NAME}/"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[${PROJECT_NAME}]${NC} $1"
}

print_error() {
    echo -e "${RED}[${PROJECT_NAME}]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[${PROJECT_NAME}]${NC} $1"
}

# Detect if we're on the deployment server
detect_environment() {
    local current_host=$(hostname -f 2>/dev/null || hostname)
    local current_ip=$(hostname -I 2>/dev/null | awk '{print $1}')
    
    # Check multiple conditions to determine if we're on the server:
    # 1. Direct IP match
    # 2. We're in the git directory and the deployment directory exists
    # 3. We can't SSH to ourselves (would fail)
    if [[ "$current_ip" == "18.118.142.110" ]] || \
       [[ -d "/home/ec2-user/${PROJECT_NAME}" && "$PWD" == "/home/ec2-user/git/${PROJECT_NAME}" ]] || \
       [[ "$current_host" == *"ip-"*".ec2.internal" ]]; then
        echo "server"
    else
        echo "local"
    fi
}

# Deploy from local machine
deploy_from_local() {
    print_status "Deploying from local machine to ${DEPLOY_SERVER}"
    
    # Check if deploy directory exists
    if [ ! -d "deploy" ]; then
        print_error "Deploy directory not found!"
        exit 1
    fi
    
    # Sync files to server
    print_status "Syncing deployment files..."
    rsync -avz --delete \
        deploy/ \
        ${DEPLOY_SERVER}:${REMOTE_PATH} \
        --exclude='.env.example' \
        --exclude='README.md'
    
    # Copy certificates if they exist
    if [ -d "certs" ]; then
        print_status "Copying LDAP certificates..."
        rsync -avz certs/ ${DEPLOY_SERVER}:${REMOTE_PATH}certs/
    fi
    
    # Execute deployment on server
    print_status "Executing deployment on server..."
    ssh ${DEPLOY_SERVER} "cd ${REMOTE_PATH} && ./deploy.sh"
    
    print_status "Deployment complete!"
}

# Deploy on server
deploy_on_server() {
    print_status "Deploying directly on server"
    
    # If we're in the git directory, switch to deployment directory
    if [[ "$PWD" == "/home/ec2-user/git/${PROJECT_NAME}" ]]; then
        print_status "Switching from git directory to deployment directory"
        cd "/home/ec2-user/${PROJECT_NAME}" || {
            print_error "Deployment directory /home/ec2-user/${PROJECT_NAME} not found!"
            exit 1
        }
    fi
    
    # Check if we're in the right directory
    if [ ! -f "docker-compose.yml" ]; then
        print_error "docker-compose.yml not found. Are you in the ${PROJECT_NAME} directory?"
        exit 1
    fi
    
    # Check for .env file
    if [ ! -f ".env" ]; then
        print_error ".env file not found!"
        print_warning "Copy .env.example to .env and configure it first"
        exit 1
    fi
    
    # Source the .env file
    set -a
    source .env
    set +a
    
    # Authenticate with GitHub Container Registry if token is provided
    if [ -n "${GITHUB_TOKEN:-}" ]; then
        print_status "Authenticating with GitHub Container Registry..."
        echo "${GITHUB_TOKEN}" | docker login ghcr.io -u "${GITHUB_USERNAME:-brentley}" --password-stdin
    else
        print_warning "GITHUB_TOKEN not set, assuming public images or already authenticated"
    fi
    
    # Create data directory if it doesn't exist
    mkdir -p data
    
    # Pull latest images
    print_status "Pulling latest Docker images..."
    docker compose pull
    
    # Stop existing containers
    print_status "Stopping existing containers..."
    docker compose down
    
    # Start new containers
    print_status "Starting new containers..."
    docker compose up -d
    
    # Wait for services to be healthy
    print_status "Waiting for services to be healthy..."
    sleep 10
    
    # Show container status
    print_status "Container status:"
    docker compose ps
    
    # Check health endpoint
    print_status "Checking health endpoint..."
    if curl -f http://localhost:5000/api/status >/dev/null 2>&1; then
        print_status "Health check passed!"
    else
        print_warning "Health check failed, but service may still be starting..."
    fi
    
    print_status "Deployment complete!"
}

# Main execution
main() {
    local environment=$(detect_environment)
    
    print_status "Detected environment: ${environment}"
    
    if [ "$environment" == "server" ]; then
        deploy_on_server
    else
        deploy_from_local
    fi
}

# Run main function
main "$@"