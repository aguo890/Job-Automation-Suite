# Job Automation Suite

![Python](https://img.shields.io/badge/python-3.12-blue)
![CI/CD](https://img.shields.io/github/actions/workflow/status/aguo890/Job-Automation-Suite/daily_scrape.yml?label=daily%20scrape)
![Build](https://img.shields.io/github/actions/workflow/status/aguo890/Job-Automation-Suite/docker-ci.yml?label=docker-ci)
![License](https://img.shields.io/badge/license-MIT-green)

A powerful, highly-configurable suite designed to automate your job search. It scrapes high-signal job boards, ranks opportunities using a custom alignment algorithm, and generates perfectly tailored PDF resumes with a single click.

---

## 📖 The Story Behind the Suite

I built this project out of pure frustration. The traditional application loop—finding a relevant role, mapping out the right skills, agonizing over keyword optimization, rewriting bullet points, fixing PDF formatting, and finally submitting—takes hours. All of that effort goes into a document that might only get a six-second glance from a recruiter.

I wanted my time back. I created this all-in-one suite to compress that exhausting, manual cycle down to about one minute per application. It has saved me countless hours of my life and played a direct role in helping me land data and engineering internships at great companies. I open-sourced it in the hopes that it saves you just as much time.

---

## ✨ Core Capabilities

- **🧠 Smart Ranking Algorithm:** Stop scrolling through irrelevant postings. A powerful, fine-tuned algorithm evaluates and ranks scraped jobs based on your specific skills, experience, and alignment criteria.
- **📄 Custom CV Engine:** Integrated with a modern `rendercv` pipeline. Select a highly-ranked job from the dashboard and instantly generate a beautifully formatted, tailor-made PDF resume injected with the optimal keywords.
- **🎛️ Fine-Tuned Configuration:** Complete control over your search. Easily tweak target job titles, locations, ranking weights, and resume templates to perfectly match your career goals.
- **🤖 "Set it and Forget it" Automation:** The suite runs fully autonomously via GitHub Actions. It scrapes daily, persists the data, and updates your dashboard without any manual intervention.

---

## 🚀 Quick Start: How to Run

You can run the Job Automation Suite locally or in a fully isolated Docker container. 

### Option A: Run via Docker (Recommended)
The simplest way to get started without worrying about system dependencies.

```bash
git clone --recursive https://github.com/aguo890/Job-Automation-Suite.git
cd Job-Automation-Suite
make docker-up
```

*Access the Streamlit dashboard at: http://localhost:8501*

### Option B: Run Locally

If you prefer to run it natively, ensure you have **Python 3.12** installed.

```bash
# 1. Clone the repo and submodules
git clone --recursive https://github.com/aguo890/Job-Automation-Suite.git
cd Job-Automation-Suite

# 2. Set up the Python 3.12 environment
python3.12 -m venv venv
source venv/bin/activate

# 3. Install dependencies and run
make install
make run
```

---

## ⚙️ Under the Hood (SRE & Architecture)

While the suite is easy to use, it is backed by production-grade infrastructure:

  - **Hermetic Dependency Management:** Built on Python 3.12 using `pip-tools` for deterministic, cross-platform parity.
  - **Automated State Persistence:** The GitHub Actions pipeline bridges submodule boundaries, automatically pushing fresh job data to a dedicated `data-state` branch.
  - **Anti-Bot Protections:** The scraper utilizes randomized 1-10 minute execution jitters to protect IPs and mimic human behavior during automated cloud runs.
  - **Disaster Recovery:** Automated `.tar` backups are securely archived to prevent data loss.

---

## 📂 Project Structure

  - **`job-scraping-app/`**: The intelligence core. Contains the scraping engine, ranking algorithm, and the Streamlit dashboard (Submodule).
  - **`rendercv/`**: The modern LaTeX/PDF rendering engine for tailored resumes.
  - **`cv_bridge.py`**: The orchestrator linking the job data directly to the CV generator.
  - **`.github/workflows/`**: The SRE automation engine handling daily scrapes and Docker CI.

---

## 🙏 Acknowledgments

This suite stands on the shoulders of giants. It integrates and modifies two incredible open-source projects as its core engines:

* **[job-scraping-app by billyweinberger](https://github.com/billyweinberger/job-scraping-app):** Provided the foundational architecture for the multi-ATS scraping engine (Greenhouse, Lever, Ashby), data normalization, and the ranking logic.
* **[RenderCV by sinaatalay](https://github.com/sinaatalay/rendercv):** Powers the entire PDF generation pipeline, transforming structured YAML data into beautifully formatted, typographically perfect LaTeX resumes.

A massive thank you to both authors for their phenomenal work in the open-source community.

---

## 🤝 Contributing & License

We love contributions! Please read our [CONTRIBUTING.md](https://github.com/aguo890/Job-Automation-Suite/blob/main/CONTRIBUTING.md).
Licensed under the **MIT License**.
