.PHONY: help install format lint test test-ai test-fast clean docker-build docker-up docker-down

# Default target
.DEFAULT_GOAL := help

# Python interpreter
PYTHON := python3
PIP := $(PYTHON) -m pip

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install dependencies
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	$(PIP) install -r requirements-dev.txt 2>/dev/null || true

format: ## Format code with black and isort
	black .
	isort .

lint: ## Run linting checks
	black --check .
	isort --check-only .
	flake8 .
	mypy --install-types --non-interactive .

test: ## Run all tests
	pytest tests/ -v

test-ai: ## Run AI-specific tests (requires Ollama)
	pytest tests/test_ai_architecture.py tests/test_ollama_planning.py -v

test-fast: ## Run fast tests (no AI/integration)
	pytest tests/ -v -m "not ai and not integration and not slow"

test-coverage: ## Run tests with coverage report
	pytest tests/ -v --cov=ai_core --cov-report=html --cov-report=term

clean: ## Clean up temporary files
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.coverage" -delete
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf htmlcov
	rm -rf dist
	rm -rf build
	rm -rf *.egg-info

docker-build: ## Build Docker images
	docker-compose -f docker/compose/docker-compose.yml build

docker-up: ## Start Docker services
	docker-compose -f docker/compose/docker-compose.yml up -d

docker-down: ## Stop Docker services
	docker-compose -f docker/compose/docker-compose.yml down

docker-logs: ## View Docker logs
	docker-compose -f docker/compose/docker-compose.yml logs -f

dev: ## Start development environment
	@echo "Starting Ollama..."
	@ollama serve > /dev/null 2>&1 &
	@sleep 2
	@echo "Starting web server..."
	$(PYTHON) web_ui_server.py

setup-ollama: ## Install and setup Ollama with required models
	@echo "Installing Ollama..."
	@curl -fsSL https://ollama.com/install.sh | sh
	@echo "Pulling required models..."
	@ollama pull deepseek-coder:1.3b
	@ollama pull llama3.2
	@echo "Ollama setup complete!"

learning-stats: ## Show AI learning statistics
	@$(PYTHON) -c "import asyncio; from ai_core.enhanced_adaptive_planner import EnhancedAdaptivePlanner; \
	async def show_stats(): \
		planner = EnhancedAdaptivePlanner(); \
		stats = await planner.get_learning_stats(); \
		print('Learning Statistics:', stats); \
	asyncio.run(show_stats())"

tool-list: ## List all registered AI tools
	@$(PYTHON) -c "from ai_core.registry import tool_registry; \
	tools = tool_registry.list_tools(); \
	print(f'Registered tools ({len(tools)}):'); \
	for tool in sorted(tools): print(f'  - {tool}')"

pre-commit: format lint test-fast ## Run pre-commit checks

release: ## Create a new release (use: make release VERSION=v1.0.0)
	@if [ -z "$(VERSION)" ]; then \
		echo "Error: VERSION is required. Usage: make release VERSION=v1.0.0"; \
		exit 1; \
	fi
	@echo "Creating release $(VERSION)..."
	@git tag -a $(VERSION) -m "Release $(VERSION)"
	@git push origin $(VERSION)
	@echo "Release $(VERSION) created and pushed!"
