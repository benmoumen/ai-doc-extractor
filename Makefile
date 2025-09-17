# Makefile for AI Data Extractor Docker Operations

.PHONY: help build up down restart logs clean dev prod shell test

# Prefer modern Docker Compose v2. Override via: make <target> DOCKER_COMPOSE="docker-compose"
DOCKER_COMPOSE ?= docker compose

help: ## Show this help message
	@echo "Usage: make [target]"
	@echo ""
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-20s %s\n", $$1, $$2}'

# Development commands
dev: ## Start development environment with hot reloading
	$(DOCKER_COMPOSE) -f docker-compose.yml -f docker-compose.dev.yml up

dev-build: ## Build and start development environment
	$(DOCKER_COMPOSE) -f docker-compose.yml -f docker-compose.dev.yml up --build

dev-down: ## Stop development environment
	$(DOCKER_COMPOSE) -f docker-compose.yml -f docker-compose.dev.yml down

# Production commands
prod: ## Start production environment in detached mode
	$(DOCKER_COMPOSE) -f docker-compose.yml -f docker-compose.prod.yml up -d

prod-build: ## Build and start production environment
	$(DOCKER_COMPOSE) -f docker-compose.yml -f docker-compose.prod.yml up -d --build

prod-down: ## Stop production environment
	$(DOCKER_COMPOSE) -f docker-compose.yml -f docker-compose.prod.yml down

# Basic commands
build: ## Build all Docker images
	$(DOCKER_COMPOSE) build

up: ## Start all services
	$(DOCKER_COMPOSE) up -d

down: ## Stop all services
	$(DOCKER_COMPOSE) down

restart: ## Restart all services
	$(DOCKER_COMPOSE) restart

logs: ## View logs from all services
	$(DOCKER_COMPOSE) logs -f

logs-backend: ## View backend logs
	$(DOCKER_COMPOSE) logs -f backend

logs-frontend: ## View frontend logs
	$(DOCKER_COMPOSE) logs -f frontend

# Shell access
shell-backend: ## Access backend container shell
	$(DOCKER_COMPOSE) exec backend /bin/bash

shell-frontend: ## Access frontend container shell
	$(DOCKER_COMPOSE) exec frontend /bin/sh


# Maintenance commands
clean: ## Remove all containers, networks, and volumes
	$(DOCKER_COMPOSE) down -v
	docker system prune -f

clean-all: ## Remove everything including images
	$(DOCKER_COMPOSE) down -v --rmi all
	docker system prune -af

# Testing
test-backend: ## Run backend tests
	$(DOCKER_COMPOSE) exec backend python -m pytest tests/

test-frontend: ## Run frontend tests
	$(DOCKER_COMPOSE) exec frontend npm test

test-all: test-backend test-frontend ## Run all tests

# Health checks
health: ## Check health of all services
	@echo "Checking service health..."
	@$(DOCKER_COMPOSE) ps
	@echo "\nBackend health:"
	@curl -s http://localhost:8000/health || echo "Backend not healthy"
	@echo "\nFrontend health:"
	@curl -s http://localhost:3000/api/health || echo "Frontend not healthy"

# Environment setup
env-setup: ## Copy .env.example to .env
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "Created .env file. Please update it with your API keys."; \
	else \
		echo ".env file already exists."; \
	fi

# Quick start
quickstart: env-setup build up ## Quick start: setup environment, build, and start services
	@echo "Services started! Access the application at:"
	@echo "  - Frontend: http://localhost:3000"
	@echo "  - Backend: http://localhost:8000"
	@echo ""
	@echo "Remember to update your .env file with API keys!"

# Development utilities
format: ## Format code (requires services to be running)
	$(DOCKER_COMPOSE) exec backend black .
	$(DOCKER_COMPOSE) exec backend isort .
	$(DOCKER_COMPOSE) exec frontend npm run format

lint: ## Lint code (requires services to be running)
	$(DOCKER_COMPOSE) exec backend flake8 .
	$(DOCKER_COMPOSE) exec backend mypy .
	$(DOCKER_COMPOSE) exec frontend npm run lint