# Job Automation Suite

A comprehensive suite for automated job scraping, analysis, and CV tailoring.

## Overview

This project unifies `job-scraping-app` and `rendercv` into a powerful monorepo. It features:
- **Centralized Build System**: A root `Makefile` that handles installation, running, and testing across platforms.
- **AI-Powered CV Tailoring**: Using `cv_bridge.py`, you can generate custom PDFs for any job with a single click.
- **Race-Condition-Free Architecture**: Safe for concurrent usage.
- **Pinned Dependencies**: Ensures stability.

## Quick Start

### Prerequisites
- Python 3.10+
- (Optional) GNU Make (Windows users can use Git Bash or chocolatey `make`)

### Installation

```bash
make install
```

### Usage

Run the scraper and launch the dashboard:

```bash
make run
# Output: Streamlit app running at http://localhost:8501
```

Or just scrape:

```bash
make scrape
```

## Structure

- `job-scraping-app/`: The main dashboard and scraper logic.
- `rendercv/`: The engine for rendering LaTeX/PDF CVs from YAML.
- `cv_bridge.py`: The integration layer orchestrating CV generation.
- `generated_cvs/`: Output directory for tailored CVs.
