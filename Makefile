# -----------------------------------------------------------------------------
# OS Detection & Configuration
# -----------------------------------------------------------------------------
ifeq ($(OS),Windows_NT)
    # Windows Settings
    VENV_BIN = venv/Scripts
    PYTHON = $(VENV_BIN)/python
    PIP = $(VENV_BIN)/pip
    RM_DIR = rmdir /s /q
    RM_FILE = del /q
    FIX_PATH = $(subst /,\,$(1))
    MKDIR_P = mkdir
    # Run from subdir, so use relative path to venv in root
    RUN_SCRAPER = cd job-scraping-app && ..\$(subst /,\,$(PYTHON)) main.py
else
    # Unix Settings
    VENV_BIN = venv/bin
    PYTHON = $(VENV_BIN)/python
    PIP = $(VENV_BIN)/pip
    RM_DIR = rm -rf
    RM_FILE = rm -f
    FIX_PATH = $(1)
    MKDIR_P = mkdir -p
    # Run from subdir
    RUN_SCRAPER = cd job-scraping-app && ../$(PYTHON) main.py
endif

# -----------------------------------------------------------------------------
# Targets
# -----------------------------------------------------------------------------
.PHONY: install run scrape test clean help docker-up docker-build docker-down

help:
	@echo "Local Commands:"
	@echo "  make install       - Create venv and install all dependencies"
	@echo "  make run           - Launch the Streamlit Dashboard (Local)"
	@echo "  make scrape        - Run the Job Scraper (Local)"
	@echo "  make test          - Run verification tests"
	@echo "  make clean         - Remove temp files and venv"
	@echo ""
	@echo "Docker Commands:"
	@echo "  make docker-up     - Build and run the full suite in Docker"
	@echo "  make docker-down   - Stop and remove the Docker container"
	@echo "  make docker-build  - Force rebuild the Docker image"

# --- Local Development ---

install:
	@echo "Creating virtual environment..."
	python -c "import os; import venv; venv.create('venv', with_pip=True) if not os.path.exists('venv') else None"
	@echo "Installing dependencies..."
	.$(FIX_PATH)/venv/Scripts/python -m pip install --upgrade pip
	@echo "Installing root requirements..."
	.$(FIX_PATH)/venv/Scripts/python -m pip install -r requirements.txt
	@echo "Installing local packages (Editable Mode)..."
	.$(FIX_PATH)/venv/Scripts/python -m pip install -e "./rendercv[full]"
	.$(FIX_PATH)/venv/Scripts/python -m pip install -e ./job-scraping-app

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
	docker-compose up --build

docker-down:
	@echo "Stopping Docker container..."
	docker-compose down

docker-build:
	@echo "Building Docker image..."
	docker-compose build
