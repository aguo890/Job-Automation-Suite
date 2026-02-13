import os
import shutil
from datetime import datetime
import contextlib
import pathlib
import sys
import uuid
import ai_tailor

# Use ruamel.yaml for better YAML handling (preserves quotes/comments, handles * correctly presumably)
try:
    from ruamel.yaml import YAML
    yaml_handler = YAML()
    yaml_handler.preserve_quotes = True
except ImportError:
    # Fallback to pyyaml if ruamel is missing, but it will likely fail on the CV file
    import yaml as pyyaml
    class YamlHandler:
        def load(self, stream):
            return pyyaml.safe_load(stream)
        def dump(self, data, stream):
            return pyyaml.dump(data, stream)
    yaml_handler = YamlHandler()
    print("WARNING: ruamel.yaml not found. Using PyYAML (may fail on some aliases).")

# Try importing rendercv CLI modules
try:
    from rendercv.cli.render_command.run_rendercv import run_rendercv
    from rendercv.cli.render_command.progress_panel import ProgressPanel
except ImportError:
    run_rendercv = None
    ProgressPanel = None
    print("WARNING: rendercv not found or structure changed. Ensure it is installed in this environment.")

class CVOrchestrator:
    def __init__(self, base_cv_relative_path="rendercv/Aaron_Guo_CV.yaml"):
        # Calculate absolute paths relative to this script
        self.root_dir = os.path.dirname(os.path.abspath(__file__))
        self.base_cv_path = os.path.join(self.root_dir, base_cv_relative_path)
        
        # Output folder for generated PDFs
        self.output_dir = os.path.join(self.root_dir, "generated_cvs")
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def generate_tailored_cv(self, job_details, use_ai=False, status_callback=None):
        """
        Reads base YAML, injects job-specific details (optionally using AI), and renders PDF.
        Returns: (Path to the generated PDF, Strategy Report String)
        """
        if not run_rendercv:
            raise EnvironmentError("RenderCV library is not installed correctly (modules missing).")

        if not os.path.exists(self.base_cv_path):
             raise FileNotFoundError(f"Base CV not found at: {self.base_cv_path}")

        # 1. Load the Base YAML
        with open(self.base_cv_path, 'r', encoding='utf-8') as f:
            cv_data = yaml_handler.load(f)

        # 2. Extract Job Info
        company = job_details.get('company', 'Generic')
        role = job_details.get('title', 'Software Engineer')
        
        if status_callback: status_callback("Reading base resume and job details...")
        
        # 3. TAILORING LOGIC
        strategy_report = "Standard generation (No AI used)."
        
        if use_ai:
            if status_callback: status_callback(f"Consulting DeepSeek-R1 for {company} (this may take 30-60s)...")
            print(f"🤖 DeepSeek-R1 is tailoring CV for {company}...")
            try:
                strategy, new_yaml_content, gap_analysis, reasoning = ai_tailor.generate_tailored_resume(
                    base_yaml_content=open(self.base_cv_path, 'r', encoding='utf-8').read(),
                    job_description=job_details.get('description', 'No description provided'),
                    job_title=role,
                    company_name=company
                )
                strategy_report = f"## 🧠 AI Strategy\n{strategy}\n\n## 💭 Chain of Thought\n{reasoning}\n\n## ⚠️ Gap Analysis\n{gap_analysis}"
                if status_callback: status_callback("AI generation complete. Parsing new YAML...")
                
                # Update cv_data with the new YAML structure
                # We need to reload it into our yaml_handler to ensure consistency or just write it directly later
                # Since we write to temp_yaml_path later, let's just use the string content if AI is used.
                cv_data = yaml_handler.load(new_yaml_content)
                
                # --- SAFETY: Force specific filename ---
                # DeepSeek might hallucinate paths. We override it here to match our expectation.
                # We use the 'new_filename' we calculated, but we need to ensure it's in the 'rendercv_output' subfolder
                # relative to where we run rendercv (which is base_cv_folder).
                # RenderCV defaults to creating a folder with the name of the input file if not specified, 
                # or we can specify `pdf_path` in the command. 
                # But for the YAML to be "valid" and consistent, let's update it.
                if 'cv' in cv_data:
                    # RenderCV v2 structure: cv -> ...
                    # But wait, rendercv settings are usually top level in some versions or under 'rendercv'.
                    # Let's check if the root has 'rendercv' or if it's the root itself.
                    # Actually standard RenderCV YAML has `cv:` key.
                    # Settings are usually optional. 
                    pass 
                
                # We will rely on run_rendercv(pdf_path=...) to handle the actual file location.
                # However, to prevent any confusion if RenderCV looks at the yaml, let's try to set it if safe.
                # For now, we just proceed.
                
            except Exception as e:
                print(f"AI Tailoring failed: {e}")
                strategy_report = f"AI Tailoring failed: {e}"
                # Fallback to standard injection if AI fails?
                # For now let's just proceed with standard injection or raise? 
                # User probably wants to know if AI failed.
                # Let's fallback to standard logic but warn.
        
        # If AI wasn't used OR if AI failed (and we re-loaded base/kept cv_data), do standard injection if needed
        # But if AI succeeded, cv_data is already the tailored version.
        
        if not use_ai:
            try:
                if 'cv' in cv_data and 'sections' in cv_data['cv'] and 'summary' in cv_data['cv']['sections']:
                    summary_list = cv_data['cv']['sections']['summary']
                    if isinstance(summary_list, list) and len(summary_list) > 0:
                        tailored_line = f"Targeting the {role} position at **{company}**."
                        summary_list.insert(0, tailored_line)
            except Exception as e:
                print(f"Non-critical warning: Could not inject summary. {e}")

        # 4. Define Output Filenames with UUID to prevent collisions
        safe_company = "".join([c for c in company if c.isalnum() or c in (' ', '_', '-')]).strip().replace(' ', '_')
        unique_id = uuid.uuid4().hex[:8]
        # We want the final PDF to be readable but unique enough for this session/request
        new_filename = f"Aaron_Guo_CV_{safe_company}_{unique_id}" 

        # 5. Save Temporary Tailored YAML
        # CRITICAL: We save the temp yaml in the SAME directory as the base yaml
        # to preserve relative paths for images/assets referenced in the YAML.
        base_cv_folder = os.path.dirname(self.base_cv_path)
        
        # Use a unique name for the temp yaml too
        temp_yaml_name = f"temp_{unique_id}.yaml"
        temp_yaml_path = os.path.join(base_cv_folder, temp_yaml_name)
        
        with open(temp_yaml_path, 'w', encoding='utf-8') as f:
            yaml_handler.dump(cv_data, f)

        # Target PDF Path
        expected_pdf_path = os.path.join(self.output_dir, f"{new_filename}.pdf")

        if status_callback: status_callback("Compiling PDF with RenderCV...")

        # 6. Render the CV
        try:
            # We strictly control inputs to run_rendercv
            with ProgressPanel(quiet=True) as progress:
                # We switch CWD to base folder just in case
                start_dir = os.getcwd()
                os.chdir(base_cv_folder)
                try:
                    run_rendercv(
                        pathlib.Path(temp_yaml_name), # Relative to CWD
                        progress,
                        pdf_path=pathlib.Path(expected_pdf_path) # Absolute path
                    )
                finally:
                    os.chdir(start_dir)
            
            # 7. Cleanup and Verify
            if os.path.exists(temp_yaml_path):
                os.remove(temp_yaml_path) # Cleanup temp yaml
            
            if os.path.exists(expected_pdf_path):
                return expected_pdf_path, strategy_report
            
            raise RuntimeError(f"PDF was not created at {expected_pdf_path}")

        except (Exception, SystemExit) as e:
            # If temp file still exists, clean it up
            if os.path.exists(temp_yaml_path):
                os.remove(temp_yaml_path)
            
            if isinstance(e, SystemExit):
                if e.code == 0 and os.path.exists(expected_pdf_path):
                    return expected_pdf_path, strategy_report
                raise RuntimeError(f"RenderCV exited with code {e.code}")
            
            # If it's a ruamel error or other exception
            import traceback
            traceback.print_exc()
            
            # Helper for Windows users
            if isinstance(e, PermissionError) or "Permission denied" in str(e):
                raise PermissionError(f"COMBAT LOCK: Please CLOSE the PDF file '{os.path.basename(expected_pdf_path)}' if it is open!")
                
            raise RuntimeError(f"Rendering failed: {e}")
