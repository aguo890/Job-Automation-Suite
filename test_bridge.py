import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

from cv_bridge import CVOrchestrator

def test_bridge():
    print("Testing CV Bridge...")
    try:
        orchestrator = CVOrchestrator()
        print("Orchestrator initialized.")
        
        job_details = {
            "company": "TestCorp",
            "title": "Senior AI Architect"
        }
        
        print(f"Generating CV for {job_details['company']}...")
        pdf_path = orchestrator.generate_tailored_cv(job_details)
        
        print(f"Result: {pdf_path}")
        
        if os.path.exists(pdf_path):
            print("SUCCESS: PDF file exists.")
        else:
            print("FAILURE: PDF file does not exist at returned path.")
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_bridge()
