import os
import shutil
from datetime import datetime
import contextlib
import pathlib
import sys
import uuid

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

    def generate_tailored_cv(self, job_details):
        """
        Reads base YAML, injects job-specific details, and renders PDF.
        Returns: Path to the generated PDF.
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
        
        # 3. TAILORING LOGIC
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
                return expected_pdf_path
            
            raise RuntimeError(f"PDF was not created at {expected_pdf_path}")

        except (Exception, SystemExit) as e:
            # If temp file still exists, clean it up
            if os.path.exists(temp_yaml_path):
                os.remove(temp_yaml_path)
            
            if isinstance(e, SystemExit):
                if e.code == 0 and os.path.exists(expected_pdf_path):
                    return expected_pdf_path
                raise RuntimeError(f"RenderCV exited with code {e.code}")
            
            # If it's a ruamel error or other exception
            import traceback
            traceback.print_exc()
            raise RuntimeError(f"Rendering failed: {e}")
