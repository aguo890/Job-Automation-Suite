# Job Automation Suite

![Python](https://img.shields.io/badge/python-3.12-blue)
![CI/CD](https://img.shields.io/github/actions/workflow/status/aguo890/Job-Automation-Suite/daily_scrape.yml?label=daily%20scrape)
![Build](https://img.shields.io/github/actions/workflow/status/aguo890/Job-Automation-Suite/docker-ci.yml?label=docker-ci)
![License](https://img.shields.io/badge/license-MIT-green)

A powerful, highly-configurable suite designed to automate your job search. It scrapes high-signal job boards, ranks opportunities using a custom alignment algorithm, and generates perfectly tailored PDF resumes with a single click.

---

## 📖 The Story Behind the Suite

I built this project out of pure frustration. I first stumbled upon the **job-scraping-app** (see below), and I was like, "Okay, I now have all these hundreds of jobs I can apply to!" But the friction was still immense. The traditional application loop—mapping out the right skills, agonizing over keyword optimization, rewriting bullet points, and fixing PDF formatting—still takes hours. All of that effort goes into a document that might only get a six-second glance from a recruiter.

Then I found **RenderCV**, which was amazing for the rendering part. But after another few days of using both of them in conjunction, a thought struck me: *How nice would it be if I was able to directly generate the CV within the same interface, allowing me to integrate AI and other tools to handle the heavy lifting?*

That idea turned into an unhealthy obsession to make the process perfect. Honestly, I probably spent longer building this suite than I actually used it to apply to jobs. But let's be real: applying to jobs is boring, but making something minutely more efficient is way funner.

To make this as intuitive as possible, I built a dedicated **Streamlit dashboard**—because while I have deep respect for the terminal-only roots of the foundational tools, I find staring at a flickering CLI for hours on end to be... let's just say, "unnecessarily character-building" (and slightly ugly). This suite has saved me countless hours of my life (and costed hundreds of more hours, but i view that as "learning") and played a direct role in helping me land data and engineering internships at great companies. I open-sourced it in the hopes that it saves you just as much time.

---

## 🙏 Acknowledgments

This suite stands on the shoulders of giants. It integrates and modifies two incredible open-source projects as its core engines:

* **[job-scraping-app by billyweinberger](https://github.com/billyweinberger/job-scraping-app):** Provided the foundational architecture for the multi-ATS scraping engine (Greenhouse, Lever, Ashby), data normalization, and the ranking logic.
* **[RenderCV by sinaatalay](https://github.com/sinaatalay/rendercv):** Powers the entire PDF generation pipeline, transforming structured YAML data into beautifully formatted, typographically perfect LaTeX resumes.

A massive thank you to both authors for their phenomenal work in the open-source community.

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

## ⚙️ Configuration & Environment Variables

The suite is highly configurable via environmental flags. To get started, copy the template and edit it with your credentials:

```bash
cp .env.example .env
```

### Key Toggles

| Variable | Default | Description |
| :--- | :--- | :--- |
| `USE_GITHUB_DATA` | `false` | **Crucial:** Set to `true` to fetch data from your GitHub `data-state` branch. Set to `false` (Local Mode) to read the 1,459+ jobs you've scraped directly to your disk. |
| `GITHUB_TOKEN` | `N/A` | Required if `USE_GITHUB_DATA=true` or for automated state backups. |
| `OPENAI_API_KEY` | `N/A` | (Optional) Enables AI-powered resume tailoring with GPT models. |
| `DEEPSEEK_API_KEY` | `N/A` | (Optional) Enables high-performance, cost-effective reasoning via DeepSeek. |
| `USER_AGENT` | `N/A` | (Optional) Override the default browser identity to avoid bot detection. |

### 🤖 Enabling Automated AI Matching & Tailoring
To use the automated AI resume tailoring and job matching features, you **must** configure either an `OPENAI_API_KEY` or `DEEPSEEK_API_KEY` in your `.env` file. Without this key, the AI buttons in the CV Editor will be disabled or fail to generate content.

### ⚡ Fast Configuration (Advanced Users)
While the Streamlit Dashboard provides a nice UI for configuration, if you want to set up massive lists of target companies or skills quickly (e.g. formatting a bulk list using AI), you can bypass the UI and directly edit the RAW YAML files located in `job-scraping-app/config/`. The core files are `companies.yaml` and `filtering.yaml`.

---

## 🏗️ Under the Hood (SRE & Architecture)

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

## 🤝 Contributing & License

We love contributions! Please read our [CONTRIBUTING.md](https://github.com/aguo890/Job-Automation-Suite/blob/main/CONTRIBUTING.md).
Licensed under the **MIT License**.
