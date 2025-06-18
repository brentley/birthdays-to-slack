.PHONY: help dev test build deploy logs shell stop clean

help:
	@echo "Available commands:"
	@echo "  make dev     - Start development environment"
	@echo "  make test    - Run tests"
	@echo "  make build   - Build Docker image"
	@echo "  make deploy  - Deploy to production"
	@echo "  make logs    - View logs"
	@echo "  make shell   - Access container shell"
	@echo "  make stop    - Stop all containers"
	@echo "  make clean   - Clean up everything"

dev:
	docker compose --profile dev up

test:
	docker compose --profile test up --abort-on-container-exit

build:
	docker compose build

deploy:
	./deploy-smart.sh

logs:
	docker compose logs -f

shell:
	docker compose exec birthdays-to-slack /bin/bash

stop:
	docker compose down

clean:
	docker compose down -v
	docker system prune -f