import os
import shutil
import json
from datetime import datetime
import pathlib
import uuid
import ai_tailor

# --- YAML Handler Setup ---
try:
    from ruamel.yaml import YAML
    yaml_handler = YAML()
    yaml_handler.preserve_quotes = True
except ImportError:
    import yaml as pyyaml
    class YamlHandler:
        def load(self, stream):
            return pyyaml.safe_load(stream)
        def dump(self, data, stream):
            return pyyaml.dump(data, stream)
    yaml_handler = YamlHandler()
    print("WARNING: ruamel.yaml not found. Using PyYAML.")

# --- RenderCV Setup ---
try:
    from rendercv.cli.render_command.run_rendercv import run_rendercv
    from rendercv.cli.render_command.progress_panel import ProgressPanel
except ImportError:
    run_rendercv = None
    ProgressPanel = None
    print("WARNING: rendercv not found. Ensure it is installed.")

class CVOrchestrator:
    def __init__(self, base_cv_filename="Aaron_Guo_CV.yaml"):
        # 1. Deterministic Root: The directory where THIS script lives
        self.root_dir = pathlib.Path(__file__).resolve().parent

        # 2. Strict Paths
        # Looks for: /app/rendercv/Aaron_Guo_CV.yaml (Docker) or ./rendercv/Aaron_Guo_CV.yaml (Local)
        self.base_cv_path = self.root_dir / "rendercv" / base_cv_filename
        
        self.output_dir = self.root_dir / "generated_cvs"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_tailored_cv(self, job_details, use_ai=False, status_callback=None):
        """
        Reads base YAML, injects job-specific details, and renders PDF.
        """
        if not run_rendercv:
            raise EnvironmentError("RenderCV library is not installed.")

        if not self.base_cv_path.exists():
             raise FileNotFoundError(f"MASTER CV MISSING. Expected at: {self.base_cv_path}")

        # A. Load Base YAML
        with open(self.base_cv_path, 'r', encoding='utf-8') as f:
            cv_data = yaml_handler.load(f)

        company = job_details.get('company', 'Generic')
        role = job_details.get('title', 'Software Engineer')
        
        if status_callback: status_callback("Reading base resume...")
        
        # B. AI Tailoring
        strategy_report = "Standard generation (No AI used)."
        if use_ai:
            if status_callback: status_callback(f"Consulting DeepSeek-R1 for {company}...")
            print(f"🤖 DeepSeek-R1 is tailoring CV for {company}...")
            try:
                # Read raw content for AI context
                raw_yaml = self.base_cv_path.read_text(encoding='utf-8')
                strategy, new_yaml_content, gap_analysis, reasoning = ai_tailor.generate_tailored_resume(
                    base_yaml_content=raw_yaml,
                    job_description=job_details.get('description', ''),
                    job_title=role,
                    company_name=company
                )
                strategy_report = f"## 🧠 AI Strategy\n{strategy}\n\n## 💭 Chain of Thought\n{reasoning}\n\n## ⚠️ Gap Analysis\n{gap_analysis}"
                if status_callback: status_callback("AI generation complete. Parsing new YAML...")
                cv_data = yaml_handler.load(new_yaml_content)
            except Exception as e:
                print(f"AI Tailoring failed: {e}")
                strategy_report = f"AI Tailoring failed: {e}"

        # C. Manual Injection Fallback (if AI not used)
        if not use_ai:
            try:
                # Safely try to inject summary if structure permits
                summary_list = cv_data.get('cv', {}).get('sections', {}).get('summary', [])
                if isinstance(summary_list, list):
                    tailored_line = f"Targeting the {role} position at **{company}**."
                    summary_list.insert(0, tailored_line)
            except Exception:
                pass

        # D. Prepare Filenames
        safe_company = "".join([c for c in company if c.isalnum() or c in (' ', '_', '-')]).strip().replace(' ', '_')
        unique_id = uuid.uuid4().hex[:8]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        new_filename = f"Aaron_Guo_CV_{safe_company}_{timestamp}_{unique_id}" 

        # E. Save Temp YAML (Must be in same folder as base CV for assets)
        base_cv_folder = self.base_cv_path.parent
        temp_yaml_name = f"temp_{unique_id}.yaml"
        temp_yaml_path = base_cv_folder / temp_yaml_name
        
        with open(temp_yaml_path, 'w', encoding='utf-8') as f:
            yaml_handler.dump(cv_data, f)

        expected_pdf_path = self.output_dir / f"{new_filename}.pdf"
        history_yaml_path = self.output_dir / f"{new_filename}.yaml"

        # Save history copy
        try:
            shutil.copy2(temp_yaml_path, history_yaml_path)
        except Exception as e:
            print(f"Warning: Could not save history YAML: {e}")

        if status_callback: status_callback("Compiling PDF...")

        # F. Render PDF
        try:
            with ProgressPanel(quiet=True) as progress:
                # Switch CWD so RenderCV finds relative image paths
                current_cwd = os.getcwd()
                os.chdir(base_cv_folder)
                try:
                    run_rendercv(
                        pathlib.Path(temp_yaml_name),
                        progress,
                        pdf_path=expected_pdf_path
                    )
                finally:
                    os.chdir(current_cwd)
            
            # G. Cleanup & Verify
            if temp_yaml_path.exists():
                temp_yaml_path.unlink()
            
            if expected_pdf_path.exists():
                # Success! Return strings for compatibility
                return str(expected_pdf_path), strategy_report
            
            raise RuntimeError(f"PDF not found at {expected_pdf_path}")

        except Exception as e:
            if temp_yaml_path.exists():
                temp_yaml_path.unlink()
            raise RuntimeError(f"Rendering failed: {e}")

    # --- CV Editor Methods ---

    def load_job_cv(self, job_id):
        tailored_path = self.output_dir / f"{job_id}.yaml"
        if tailored_path.exists():
            return tailored_path.read_text(encoding='utf-8')
        
        if self.base_cv_path.exists():
            return self.base_cv_path.read_text(encoding='utf-8')
            
        return f"# Error: Master CV not found at {self.base_cv_path}"

    def save_job_cv(self, job_id, yaml_content):
        save_path = self.output_dir / f"{job_id}.yaml"
        save_path.write_text(yaml_content, encoding='utf-8')
        return str(save_path)

    def render_from_content(self, job_id, yaml_content):
        if not run_rendercv: return None, "RenderCV missing."

        base_cv_folder = self.base_cv_path.parent
        temp_yaml_name = f"temp_{job_id}.yaml"
        temp_yaml_path = base_cv_folder / temp_yaml_name
        expected_pdf_path = self.output_dir / f"{job_id}.pdf"

        try:
            temp_yaml_path.write_text(yaml_content, encoding='utf-8')

            with ProgressPanel(quiet=True) as progress:
                current_cwd = os.getcwd()
                os.chdir(base_cv_folder)
                try:
                    run_rendercv(
                        pathlib.Path(temp_yaml_name),
                        progress,
                        pdf_path=expected_pdf_path
                    )
                finally:
                    os.chdir(current_cwd)

            if temp_yaml_path.exists():
                temp_yaml_path.unlink()

            if expected_pdf_path.exists():
                yaml_path = self.save_job_cv(job_id, yaml_content)
                self.update_tracking(job_id, yaml_path, str(expected_pdf_path))
                return str(expected_pdf_path), "Success"
            
            return None, "PDF generation failed."

        except Exception as e:
            if temp_yaml_path.exists():
                temp_yaml_path.unlink()
            return None, str(e)

    def update_tracking(self, job_id, yaml_path, pdf_path):
        """
        Updates tracking.json. Ensures paths are converted to strings first.
        """
        tracking_file = self.root_dir / "data" / "tracking.json"
        
        # Fallback for local dev structure if needed
        if not tracking_file.exists():
            fallback = self.root_dir / "job-scraping-app" / "data" / "tracking.json"
            if fallback.exists():
                tracking_file = fallback
            else:
                return # Can't find tracking file

        try:
            with open(tracking_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if job_id in data:
                # Force string conversion for JSON serialization
                data[job_id]["cv_yaml_path"] = str(yaml_path)
                data[job_id]["cv_pdf_path"] = str(pdf_path)
                data[job_id]["cv_status"] = "Tailored"

                with open(tracking_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not update tracking: {e}")
