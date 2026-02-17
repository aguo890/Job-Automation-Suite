# Job Automation Suite

![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Build](https://img.shields.io/badge/build-passing-brightgreen)
![PRs Welcome](https://img.shields.io/badge/PRs-welcome-orange)

A powerful, all-in-one suite for **automated job scraping**, **analysis**, and **instant CV tailoring**.

Stop manually applying to jobs. Let the suite do the work.

## 🚀 Key Features

-   **🔍 Automated Scraping**:  Fetches jobs from multiple sources and aggregates them into a clean dashboard.
-   **📄 Instant CV Tailoring**: Generates a custom PDF CV for *any* job with a single click, injecting relevant keywords and summaries.
-   **📊 Smart Dashboard**: Filter, sort, and track your applications in real-time.
-   **🤖 AI-Powered**: Uses LLMs (Optional) to analyze job descriptions and draft cover letters.
-   **🔄 Continuous Sync**: Built-in `make push` keeps your code and data synced across repositories automatically.

## 🛠️ Quick Start

### Prerequisites
-   Python 3.10+
-   Git

### Installation

Clone the repo and install everything with one command:

```bash
git clone --recursive https://github.com/aguo890/Job-Automation-Suite.git
cd Job-Automation-Suite
make install
```

### Usage

**1. Run the Dashboard:**
This command auto-fetches the latest jobs and launches the UI.
```bash
make run
```
*Access at: http://localhost:8501*

**2. Generate a CV:**
-   Select a job in the dashboard.
-   Click **"Generate CV for Selected"**.
-   Download your PDF!

### 🐳 Docker Support

Run the entire suite in a container without installing Python locally.

**Build and Run:**
```bash
docker-compose up --build
```
*Access at: http://localhost:8501*

**Features:**
-   **Hot-reloading**: Code changes in `render_cv/` or `job-scraping-app/` require a rebuild unless mounted for dev.
-   **Persistence**: Config, data, and generated CVs are saved to your host machine automatically.

## 📂 Project Structure

It's a monorepo containing:
-   **`job-scraping-app/`**: The intelligence core (Scraper + Dashboard).
-   **`rendercv/`**: The LaTeX/PDF rendering engine.
-   **`cv_bridge.py`**: The orchestrator linking them together.

## 🤝 Contributing

We love contributions! Please read our [CONTRIBUTING.md](CONTRIBUTING.md) for details on how to get started.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
