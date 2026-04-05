# Job Automation Suite

![Python](https://img.shields.io/badge/python-3.9-blue)
![CI/CD](https://img.shields.io/github/actions/workflow/status/aguo890/Job-Automation-Suite/daily_scrape.yml?label=daily%20scrape)
![Build](https://img.shields.io/github/actions/workflow/status/aguo890/Job-Automation-Suite/docker-ci.yml?label=docker-ci)
![License](https://img.shields.io/badge/license-MIT-green)

A production-grade, hardened suite for **automated job scraping**, **analysis**, and **instant CV tailoring**. Built with SRE best practices to ensure a "Set it and Forget it" experience.

---

## 🚀 Key Features

-   **🔍 Automated Scraping**:  Fetches jobs from high-signal sources and aggregates them into a clean dashboard.
-   **📄 Instant CV Tailoring**: Generates custom PDF CVs with one click, injecting relevant keywords and summaries via `rendercv`.
-   **📊 Smart Dashboard**: Filter, sort, and track applications in real-time with a Streamlit-powered UI.
-   **🤖 AI-Powered**: Optional LLM integration for analyzing job descriptions and drafting cover letters.
-   **🛡️ Hardened SRE**: Built for reliability, with automated state management, anti-bot protections, and disaster recovery.

---

## 🏗️ "Set it and Forget it" CI/CD

The suite runs fully autonomously via GitHub Actions. The `daily_scrape.yml` pipeline handles the heavy lifting:

-   **Autonomous Execution**: Scheduled to run daily (with peak/off-peak frequencies) to ensure the platform is never stale.
-   **State Management**: Automatically commits results to a dedicated `data-state` branch, separating application logic from persistent data.
-   **Hermetic Testing**: The `docker-ci.yml` pipeline verifies every commit in an immutable container environment, ensuring total parity between local and production.

---

## 🛡️ SRE & Resiliency Features

This suite is engineered for 99.9% reliability in scraping and data integrity:

-   **Anti-Bot Mitigation**: Implements a randomized **1-10 minute execution jitter** to protect datacenter IPs and mimic human behavior.
-   **State Persistence**: Handles Git Submodule boundaries to persist data from `job-scraping-app` to the root repository, using `--force` pushes to the `data-state` branch for a clean history.
-   **Disaster Recovery (DR)**: Automated nightly backups create `.tar` archives of the critical data state, pushed to a secure remote using authenticated `x-access-token` credentials.
-   **Crash Prevention**: Automated `.lock` file clearing (`rm -f *.lock`) before every execution prevents "ghost crashes" and ensures the scraper always recovers from interrupted states.

---

## 📦 Dependency Management

We use a pure-data, cross-platform architecture powered by `pip-tools`:

-   **Python 3.9 Pinned**: Guaranteed environment parity between macOS (M-series), Linux CI runners, and Docker containers.
-   **Deterministic Lockfiles**: Using `pip-compile` to generate hash-free, annotation-free `requirements.txt` files that eliminate cross-platform wheel mismatches.
-   **SLSA Compliance**: Lockfile drift checks in CI ensure that the current environment perfectly matches the source of truth.

---

## 🛠️ Quick Start

### Prerequisites
-   Python 3.9 (Recommended via `pyenv` or `conda`)
-   Git
-   Docker (Optional, for hermetic execution)

### Installation

```bash
git clone --recursive https://github.com/aguo890/Job-Automation-Suite.git
cd Job-Automation-Suite
make install
```

### Usage

**1. Run the Dashboard:**
```bash
make run
```
*Access at: http://localhost:8501*

**2. Generate a CV:**
Select a job in the dashboard and click **"Generate CV for Selected"**.

---

## 📂 Project Structure

-   **`job-scraping-app/`**: The intelligence core (Scraper + Dashboard) [Submodule].
-   **`rendercv/`**: The LaTeX/PDF rendering engine.
-   **`cv_bridge.py`**: The orchestrator linking scraping data to CV generation.
-   **`.github/workflows/`**: The SRE engine (Daily scrapes, Docker CI, Backups).

---

## 🤝 Contributing & License

We love contributions! Please read our [CONTRIBUTING.md](CONTRIBUTING.md).
Licensed under the **MIT License**.
