# OS Detection
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

.PHONY: install run test clean help scrape

help:
	@echo "Available commands:"
	@echo "  make install      - specific install for dev local"
	@echo "  make run          - Run the dashboard"
	@echo "  make scrape       - Run the scraper to fetch jobs"
	@echo "  make test         - Run verification"
	@echo "  make clean        - Remove artifacts"

install:
	@echo "Setting up environment..."
	python -c "import os; import venv; venv.create('venv', with_pip=True) if not os.path.exists('venv') else None"
	@echo "Upgrading pip..."
	.$(FIX_PATH)/venv/Scripts/python -m pip install --upgrade pip
	@echo "Installing rendercv..."
	.$(FIX_PATH)/venv/Scripts/python -m pip install -e "./rendercv[full]"
	@echo "Installing job-scraping-app..."
	.$(FIX_PATH)/venv/Scripts/python -m pip install -e ./job-scraping-app
	@echo "Installing requirements..."
	.$(FIX_PATH)/venv/Scripts/python -m pip install -r requirements.txt

run: scrape
	$(PYTHON) -m streamlit run job-scraping-app/dashboard.py

scrape:
	$(RUN_SCRAPER)

test:
	.$(FIX_PATH)/venv/Scripts/python test_bridge.py

clean:
	-$(RM_DIR) venv
	-$(RM_DIR) __pycache__
	-$(RM_DIR) .pytest_cache
