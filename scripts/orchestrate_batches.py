import time
import subprocess
import logging
from typing import Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_enrichment_health(config_path: str):
    """
    Calculates verification success rate and alerts if errors are high.
    """
    import yaml
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Failed to read config for health check: {e}")
        return
    
    companies = data.get('companies', [])
    total = len(companies)
    verified = sum(1 for c in companies if c.get('enrichment', {}).get('status') == 'verified')
    errors = sum(1 for c in companies if c.get('enrichment', {}).get('status') == 'error')
    
    logger.info(f"--- Enrichment Health Report ---")
    logger.info(f"Verified: {verified}/{total} | Errors: {errors}")
    
    if total > 0 and (errors / total) > 0.1:
        logger.warning("⚠️ ALERT: Error rate exceeding 10%. Consider manual header calibration or checking for new ATS bot-blocks.")

def run_migration_batches(batch_count: int = 1, size: int = 50, interval_hours: float = 24.0, config_path: str = "job-scraping-app/config/companies.yaml"):
    """
    Orchestrates the company enrichment migration in safe, timed chunks.
    """
    for i in range(batch_count):
        logger.info(f"--- Starting Migration Batch {i+1} of {batch_count} (Size: {size}) ---")
        
        try:
            # Trigger the enrichment script for the next slice
            subprocess.run(["python3", "scripts/enrich_companies.py", "--batch", str(size)], check=True)
            logger.info(f"Batch {i+1} completed successfully.")
            
            # Run health check
            check_enrichment_health(config_path)
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Batch {i+1} failed with error: {e}")
            break
        
        if i < batch_count - 1:
            interval_seconds = interval_hours * 3600
            logger.info(f"Sleeping for {interval_hours} hours to comply with scheduling limits...")
            time.sleep(interval_seconds)

    logger.info("Migration Orchestration Complete.")

if __name__ == "__main__":
    # Example execution: Can be called via cron or manually
    import argparse
    parser = argparse.ArgumentParser(description="Orchestrate company enrichment batches.")
    parser.add_argument("--count", type=int, default=1, help="Number of batches to run.")
    parser.add_argument("--size", type=int, default=50, help="Size of each batch.")
    parser.add_argument("--interval", type=float, default=12.0, help="Interval between batches in hours.")
    
    args = parser.parse_args()
    run_migration_batches(batch_count=args.count, size=args.size, interval_hours=args.interval)
