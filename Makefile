# -----------------------------------------------------------------------------
# OS Detection & Configuration
# -----------------------------------------------------------------------------
ifeq ($(OS),Windows_NT)
    # Windows Settings
    PYTHON_SYS = python
    VENV_BIN = venv/Scripts
    RM_DIR = rmdir /s /q
    RM_FILE = del /q
    FIX_PATH = $(subst /,\,$(1))
    MKDIR_P = mkdir
else
    # Unix Settings
    PYTHON_SYS = python3
    VENV_BIN = venv/bin
    RM_DIR = rm -rf
    RM_FILE = rm -f
    FIX_PATH = $(1)
    MKDIR_P = mkdir -p
endif

# Common Variables
PYTHON = $(VENV_BIN)/python
PIP = $(VENV_BIN)/pip

# Run from subdir
ifeq ($(OS),Windows_NT)
    RUN_SCRAPER = cd job-scraping-app && ..\$(subst /,\,$(PYTHON)) main.py
else
    RUN_SCRAPER = cd job-scraping-app && ../$(PYTHON) main.py
endif

# -----------------------------------------------------------------------------
# Targets
# -----------------------------------------------------------------------------
.PHONY: install run scrape test clean help docker-up docker-build docker-down docker-test docker-logs push

help:
	@echo "Local Commands:"
	@echo "  make install       - Create venv and install all dependencies"
	@echo "  make run           - Launch the Streamlit Dashboard (Local)"
	@echo "  make scrape        - Run the Job Scraper (Local)"
	@echo "  make test          - Run verification tests"
	@echo "  make clean         - Remove temp files and venv"
	@echo "  make push          - Run the push script"
	@echo ""
	@echo "Docker Commands:"
	@echo "  make docker-up     - Build and run the full suite in Docker"
	@echo "  make docker-down   - Stop and remove the Docker container"
	@echo "  make docker-build  - Force rebuild the Docker image"
	@echo "  make docker-test   - Run scraper unit tests inside the container"
	@echo "  make docker-logs   - Tail the recent logs for the scraper"

# --- Local Development ---

install:
	@echo "Creating virtual environment..."
	$(PYTHON_SYS) -m venv venv
	@echo "Installing dependencies..."
	$(PIP) install --upgrade pip
	@echo "Installing root requirements..."
	$(PIP) install -r requirements.txt
	@echo "Installing local packages (Editable Mode)..."
	-$(PIP) install -e "./rendercv[full]"
	$(PIP) install -e ./job-scraping-app

run:
	@echo "Starting Dashboard..."
	$(PYTHON) -m streamlit run job-scraping-app/dashboard.py

scrape:
	@echo "Starting Scraper..."
	$(RUN_SCRAPER)

push:
	$(PYTHON) scripts/universal_push.py

test:
	$(PYTHON) test_bridge.py

clean:
	@echo "Cleaning artifacts..."
	-$(RM_DIR) venv
	-$(RM_DIR) __pycache__
	-$(RM_DIR) .pytest_cache
	-$(RM_DIR) job-scraping-app\__pycache__
	-$(RM_DIR) rendercv\__pycache__

# --- Docker Integration ---

docker-up:
	@echo "Starting Docker container..."
	COMPOSE_DOCKER_CLI_BUILD=1 DOCKER_BUILDKIT=1 docker-compose up --build

docker-down:
	@echo "Stopping Docker container..."
	docker-compose down

docker-build:
	@echo "Building Docker image..."
	docker-compose build

docker-test:
	@echo "Running scraper scheduler tests inside Docker..."
	docker-compose run --rm scraper python -m unittest tests/test_scheduler_logic.py

docker-logs:
	@echo "Tailing scraper logs..."
	docker-compose logs scraper --tail 20 -f
