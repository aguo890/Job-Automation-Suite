# Contributing to Job Automation Suite

We welcome contributions! Whether you're fixing a bug, improving the scraper, or adding new CV templates.

## Getting Started

1.  **Fork** the repository on GitHub.
2.  **Clone** your fork:
    ```bash
    git clone --recursive https://github.com/YOUR_USERNAME/Job-Automation-Suite.git
    cd Job-Automation-Suite
    ```
    *Note: The `--recursive` flag is important to pull in submodules.*

3.  **Install** dependencies:
    ```bash
    make install
    ```

## Workflow

1.  Create a branch for your feature: `git checkout -b feature/amazing-idea`
2.  Make your changes.
3.  Test your changes:
    -   `make test` (Checks CV generation)
    -   `make run` (Checks dashboard)
4.  Commit your changes using conventional commits (e.g., `feat: add new filter`, `fix: scraper timeout`).

## Structure

-   **`job-scraping-app/`**: Main logic. If you change core scraper code, it goes here.
-   **`rendercv/`**: CV templating engine.
-   **`cv_bridge.py`**: The glue between the scraper and the CV generator.
-   **`root Makefile`**: The build system.

## Pull Requests

Submit your PR to the `main` branch. Please describe what you changed and why.
