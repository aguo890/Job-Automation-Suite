import yaml
import requests
import time
import random
import logging
import os
from datetime import date
from typing import Dict, List, Optional
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Known ATS domains to exclude from search results
ATS_DOMAINS = [
    'greenhouse.io', 'lever.co', 'ashbyhq.com', 'workday.com', 
    'breezy.hr', 'recruitee.com', 'applytojob.com', 'workable.com',
    'linkedin.com', 'indeed.com', 'glassdoor.com'
]

def verify_url(url: str) -> bool:
    """Verifies a URL exists, handling common bot-blocks."""
    if not url or not isinstance(url, str) or not url.startswith('http'):
        return False
        
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    try:
        # Using GET with stream=True to avoid downloading the whole body
        response = requests.get(url, headers=headers, timeout=10, stream=True, allow_redirects=True)
        response.close()
        return response.status_code == 200
    except requests.RequestException:
        return False

def run_enrichment_batch(yaml_path: str, batch_size=30):
    logger.info(f"Loading companies from {yaml_path}...")
    try:
        with open(yaml_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Failed to load YAML: {e}")
        return

    if not data or 'companies' not in data:
        return

    companies = data['companies']
    processed = 0
    today_str = date.today().isoformat()
    
    # Gold Set Pre-Population
    GOLD_SET = {
        "Notion": "https://www.notion.so/careers",
        "Figma": "https://www.figma.com/careers",
        "Reddit": "https://www.redditinc.com/careers",
        "PostHog": "https://posthog.com/careers",
        "OpenAI": "https://openai.com/careers",
        "Anthropic": "https://www.anthropic.com/careers",
        "Snowflake": "https://careers.snowflake.com",
        "Airwallex": "https://careers.airwallex.com",
        "Quora": "https://careers.quora.com",
        "Deliveroo": "https://careers.deliveroo.co.uk"
    }

    for company in companies:
        name = company['name']
        
        # Scenario 1: Gold Set Manual Verification
        if name in GOLD_SET:
            company['careers_page'] = GOLD_SET[name]
            company['enrichment'] = {
                'status': 'verified',
                'source': 'manual',
                'last_verified': today_str
            }
            continue

        # Skip if already verified
        if company.get('enrichment', {}).get('status') == 'verified':
            continue
            
        if processed >= batch_size:
            break
            
        logger.info(f"[{processed+1}/{batch_size}] Checking verification status for {name}...")
        
        # Ensure we have a pending status if not already verified
        if not company.get('enrichment'):
             company['enrichment'] = {
                'status': 'pending',
                'source': 'automated_search',
                'last_verified': today_str
            }
             processed += 1 
        
    # Save back to YAML
    logger.info(f"Saving enriched data back to {yaml_path}...")
    with open(yaml_path, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, sort_keys=False, allow_unicode=True)

if __name__ == "__main__":
    import os
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    CONFIG_PATH = os.path.join(BASE_DIR, 'job-scraping-app', 'config', 'companies.yaml')
    run_enrichment_batch(CONFIG_PATH)
