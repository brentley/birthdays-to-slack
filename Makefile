.PHONY: build up down dev test clean logs shell deploy help

# Default target
help:
	@echo "Available commands:"
	@echo "  build    - Build the Docker image"
	@echo "  up       - Start the birthday service (production)"
	@echo "  down     - Stop the birthday service"
	@echo "  dev      - Start the service in development mode"
	@echo "  test     - Run tests"
	@echo "  logs     - View service logs"
	@echo "  shell    - Get a shell in the container"
	@echo "  deploy   - Sync deployment files to server"
	@echo "  clean    - Remove Docker images and containers"

# Build the Docker image
build:
	docker compose build

# Start the birthday service (production)
up:
	docker compose up -d

# Stop the birthday service
down:
	docker compose down

# Start in development mode
dev:
	docker compose --profile dev up

# Run tests
test:
	docker compose --profile test run --rm test

# View logs
logs:
	docker compose logs -f

# Get a shell in the container for debugging
shell:
	docker compose exec birthdays-to-slack bash

# Deploy to server
deploy:
	./sync-deploy.sh

# Clean up Docker images and containers
clean:
	docker compose down --rmi all --volumes --remove-orphans
	docker system prune -f