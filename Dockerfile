FROM python:3.9-slim

# Set working directory
WORKDIR /app

# -----------------------------------------------------------------------------
# Stage 1: OS Dependencies
# -----------------------------------------------------------------------------
# Install system packages required for PDF generation and compilation
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    git \
    libgl1 \
    libglib2.0-0 \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# -----------------------------------------------------------------------------
# [AI AGENT CONTEXT]: Dependencies are managed via pip-tools and pyproject.toml.
# This requirements.txt and job-scraping-app/requirements.txt contain 
# cryptographic hashes for supply chain security.
COPY requirements.txt ./
COPY job-scraping-app/requirements.txt ./job-scraping-app/
COPY rendercv/pyproject.toml ./rendercv/

# Install Python dependencies using the exact-version lockfiles
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r job-scraping-app/requirements.txt
# Note: rendercv deps are installed in Stage 4 via pip install -e

# -----------------------------------------------------------------------------
# Stage 3: Application Code
# -----------------------------------------------------------------------------
# Copy the actual source code
COPY rendercv/ ./rendercv/
COPY job-scraping-app/ ./job-scraping-app/
COPY scripts/ ./scripts/
COPY cv_bridge.py ai_tailor.py ./

# -----------------------------------------------------------------------------
# Stage 4: Local Package Install
# -----------------------------------------------------------------------------
# Install local packages in editable mode so changes to source are immediate
RUN pip install -e "./rendercv[full]"
RUN pip install -e ./job-scraping-app

# -----------------------------------------------------------------------------
# Stage 5: Entry
# -----------------------------------------------------------------------------
EXPOSE 8501

# Run the dashboard
CMD ["streamlit", "run", "job-scraping-app/dashboard.py", "--server.port=8501", "--server.address=0.0.0.0"]
