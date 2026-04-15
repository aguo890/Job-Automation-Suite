import os
import shutil
import json
import tempfile
import time
from datetime import datetime
import pathlib
import uuid
import re
import ai_tailor
from io import StringIO

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
    def __init__(self, base_cv_filename="Master_CV.yaml"):
        self.root_dir = pathlib.Path(__file__).resolve().parent
        cv_dir = self.root_dir / "rendercv"
        
        # 1. PRIMARY CHECK: Look for the specific filename provided
        target_path = cv_dir / base_cv_filename
        if target_path.exists() and self._is_valid_cv(target_path):
            self.base_cv_path = target_path
        else:
            # 2. SECONDARY CHECK: Look for standard names (case-insensitive)
            standard_names = ["Master_CV.yaml", "master_cv.yaml", "CV.yaml", "cv.yaml"]
            detected_path = None
            
            for name in standard_names:
                p = cv_dir / name
                if p.exists() and self._is_valid_cv(p):
                    detected_path = p
                    break
            
            if not detected_path:
                # 3. FALLBACK: Glob for any .yaml/.yml and perform a safe content "peek"
                # This helps users who renamed their file to "My_Resume.yaml" etc.
                candidates = list(cv_dir.glob("*.yaml")) + list(cv_dir.glob("*.yml"))
                blacklist = ["mkdocs.yaml", "docker-compose.yml", "docker-compose.yaml"]
                
                for p in candidates:
                    if p.name.lower() in blacklist or p.name.startswith("."):
                        continue
                    if self._is_valid_cv(p):
                        detected_path = p
                        break
            
            self.base_cv_path = detected_path

        self.output_dir = self.root_dir / "generated_cvs"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.backups_dir = self.root_dir / "rendercv" / "backups"
        self.backups_dir.mkdir(parents=True, exist_ok=True)

    def _is_valid_cv(self, file_path):
        """
        Performs a safe plain-text peek to verify if a file is a RenderCV file.
        Uses regex to avoid crashing on complex YAML tags in non-CV files.
        """
        try:
            # Read first 1000 chars to cover comments/header
            content = file_path.read_text(encoding='utf-8', errors='ignore')[:1000]
            # Look for the 'cv:' root key at the start of a line (ignoring comments)
            # This regex allows for optional leading whitespace but ensures it's a root key
            return bool(re.search(r'^\s*cv:\s*$', content, re.MULTILINE) or 
                        re.search(r'^\s*cv:\s+[\S]', content, re.MULTILINE))
        except Exception:
            return False
        
        self.output_dir = self.root_dir / "generated_cvs"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.backups_dir = self.root_dir / "rendercv" / "backups"
        self.backups_dir.mkdir(parents=True, exist_ok=True)

    def generate_tailored_cv(self, job_details, use_ai=False, status_callback=None, overrides=None):
        """
        Reads base YAML, injects job-specific details, and renders PDF.
        """
        if not run_rendercv:
            raise EnvironmentError("RenderCV library is not installed.")

        if not self.base_cv_path or not self.base_cv_path.exists():
             raise FileNotFoundError(
                 "MASTER CV MISSING: No valid RenderCV file found in the 'rendercv/' directory. "
                 "Please ensure your master CV (e.g., Master_CV.yaml) exists and contains a 'cv:' root key."
             )

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

        # C. Summary Injection (using native overrides)
        if not use_ai:
            if not overrides:
                overrides = {}
            # Standard pattern: Inject targeting line at the top of the summary section
            # NOTE: We use RenderCV's dotted path syntax for overrides
            overrides["cv.sections.summary.0"] = f"Targeting the {role} position at **{company}**."

        # D. Prepare Filenames
        safe_company = "".join([c for c in company if c.isalnum() or c in (' ', '_', '-')]).strip().replace(' ', '_')
        unique_id = uuid.uuid4().hex[:8]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        cv_stem = self.base_cv_path.stem
        new_filename = f"{cv_stem}_{safe_company}_{timestamp}_{unique_id}" 

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
                        pdf_path=expected_pdf_path,
                        overrides=overrides
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

    def reset_playground(self):
        """Removes playground-specific files to ensure a fresh start."""
        playground_yaml = self.output_dir / "playground.yaml"
        playground_pdf = self.output_dir / "playground.pdf"
        
        try:
            if playground_yaml.exists():
                playground_yaml.unlink()
            if playground_pdf.exists():
                playground_pdf.unlink()
        except Exception as e:
            print(f"Warning: Could not reset playground files: {e}")

    def load_job_cv(self, job_id):
        """Load CV content for a given job. For 'master_cv', always loads the base file."""
        if job_id == "master_cv":
            if self.base_cv_path and self.base_cv_path.exists():
                return self.base_cv_path.read_text(encoding='utf-8')
            return "# Error: Master CV not found. Please ensure a valid YAML file with a 'cv:' key is in the 'rendercv/' folder."

        tailored_path = self.output_dir / f"{job_id}.yaml"
        if tailored_path.exists():
            return tailored_path.read_text(encoding='utf-8')
        
        if self.base_cv_path and self.base_cv_path.exists():
            return self.base_cv_path.read_text(encoding='utf-8')
            
        return "# Error: Master CV missing. Check your 'rendercv/' directory."

    def save_job_cv(self, job_id, yaml_content):
        """Save CV content. Routes to save_master_cv for 'master_cv' ID."""
        if job_id == "master_cv":
            return self.save_master_cv(yaml_content)

        save_path = self.output_dir / f"{job_id}.yaml"
        save_path.write_text(yaml_content, encoding='utf-8')
        return str(save_path)

    def save_master_cv(self, new_content):
        """
        Saves the Master CV with high-reliability practices:
        1. Validates YAML syntax.
        2. Creates a timestamped backup.
        3. Performs an atomic write to prevent corruption.
        Returns dict with 'success' and optionally 'error'.
        """
        import yaml as pyyaml_validator  # for safe_load validation

        # 1. VALIDATION: Fail fast if YAML is invalid
        try:
            pyyaml_validator.safe_load(new_content)
        except pyyaml_validator.YAMLError as e:
            return {"success": False, "error": f"Invalid YAML: {str(e)}"}

        # 2. BACKUP: Timestamped rotation
        if not self.base_cv_path:
            return {"success": False, "error": "Cannot save: No valid Master CV destination identified."}

        self.backups_dir.mkdir(parents=True, exist_ok=True)
        timestamp = int(time.time())
        cv_name = self.base_cv_path.name
        backup_path = self.backups_dir / f"{cv_name}_{timestamp}.bak"

        if self.base_cv_path.exists():
            try:
                shutil.copy2(str(self.base_cv_path), str(backup_path))
                self._rotate_backups(keep=5)
            except Exception as e:
                return {"success": False, "error": f"Backup failed: {str(e)}"}

        # 3. ATOMIC WRITE: Write temp -> os.replace
        temp_name = None
        try:
            dir_name = str(self.base_cv_path.parent)
            with tempfile.NamedTemporaryFile('w', dir=dir_name, suffix='.yaml.tmp',
                                             delete=False, encoding='utf-8') as tmp_file:
                tmp_file.write(new_content)
                temp_name = tmp_file.name

            os.replace(temp_name, str(self.base_cv_path))
            return {"success": True}

        except Exception as e:
            if temp_name and os.path.exists(temp_name):
                os.remove(temp_name)
            return {"success": False, "error": f"Write failed: {str(e)}"}

    def set_master_theme(self, theme_name):
        """
        [AST MUTATION]: Strictly enforces ruamel.yaml to update the theme key 
        while preserving comments, spacing, and structural formatting of the 
        Master_CV.yaml file.
        """
        if not self.base_cv_path or not self.base_cv_path.exists():
            return {"success": False, "error": "Master CV file not found."}

        try:
            # Re-read with ruamel.yaml specifically for mutation
            with open(self.base_cv_path, 'r', encoding='utf-8') as f:
                data = yaml_handler.load(f)
            
            # AST Update
            data['cv']['theme'] = theme_name
            
            # Atomic rewrite using the robust save_master_cv logic (round-trip)
            # Actually, to preserve comments perfectly, we should dump to a buffer
            # and then use the save_master_cv logic.
            from io import StringIO
            stream = StringIO()
            yaml_handler.dump(data, stream)
            new_content = stream.getvalue()
            
            return self.save_master_cv(new_content)
        except Exception as e:
            return {"success": False, "error": f"Theme update failed: {str(e)}"}

    def _rotate_backups(self, keep=5):
        """Delete old backups, keeping only the most recent `keep` files."""
        try:
            files = sorted(
                [f for f in self.backups_dir.iterdir() if f.suffix == '.bak'],
                key=lambda f: f.stat().st_mtime
            )  # oldest first
            if len(files) > keep:
                for f in files[:len(files) - keep]:
                    f.unlink()
        except Exception:
            pass  # Non-critical failure

    def render_from_content(self, job_id, yaml_content, overrides=None):
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
                        pdf_path=expected_pdf_path,
                        overrides=overrides
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
