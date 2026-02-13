import os
import re
import uuid
import yaml # pyyaml
from openai import OpenAI
from dotenv import load_dotenv

# Load env variables (DEEPSEEK_API_KEY)
# Force loading from the same directory as this script (project root)
env_path = os.path.join(os.path.dirname(__file__), '.env')
# Force loading from the same directory as this script (project root)
env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path=env_path)

def repair_yaml_syntax(yaml_str):
    """
    Heuristically fixes common LLM YAML errors, specifically unquoted colons.
    Example input:  'project: Project: Zero'
    Example output: 'project: "Project: Zero"'
    """
    lines = yaml_str.split('\n')
    fixed_lines = []
    
    # Regex to find a key (and optional dash) followed by a value that contains a colon
    # Pattern explanation:
    # ^(\s*-?\s*[^:]+:)  -> Capture Group 1: The key (e.g., "  - name:")
    # \s+                -> Whitespace separator
    # ([^"'].*:.*[^"'])  -> Capture Group 2: The value, IF it has a colon and NO quotes at start/end
    pattern = re.compile(r'^(\s*-?\s*[^:]+:)\s+([^"\'].*:.*[^"\'])$')

    for line in lines:
        match = pattern.match(line)
        if match:
            # We found a line like: "Title: Subtitle: The Movie"
            key_part = match.group(1)
            value_part = match.group(2)
            
            # Double check we aren't double-quoting (basic check)
            if not value_part.strip().startswith('"') and not value_part.strip().startswith("'"):
                # Escape existing quotes inside the value just in case
                value_part = value_part.replace('"', '\\"')
                fixed_line = f'{key_part} "{value_part}"'
                fixed_lines.append(fixed_line)
                continue
        
        fixed_lines.append(line)
    
    return '\n'.join(fixed_lines)

    return '\n'.join(fixed_lines)

def enforce_rendercv_schema(yaml_data):
    """
    Fixes logical schema errors.
    1. Ensures 'cv.sections.summary' is a list, not a string.
    """
    try:
        # Navigate to sections
        sections = yaml_data.get('cv', {}).get('sections', {})
        
        # FIX: Summary must be a list
        if 'summary' in sections:
            summary_content = sections['summary']
            if isinstance(summary_content, str):
                print("🔧 DEBUG: Schema Fix - Converting 'summary' from String to List")
                sections['summary'] = [summary_content]
                
        return yaml_data
    except Exception as e:
        print(f"⚠️ Warning: Schema enforcement failed slightly: {e}")
        return yaml_data

def generate_tailored_resume(base_yaml_content, job_description, job_title, company_name):
    """
    Sends the base resume and JD to DeepSeek-R1 to generate a tailored YAML.
    Sends the base resume and JD to DeepSeek-R1 to generate a tailored YAML.
    Returns: (strategy_text, new_yaml_content, gap_analysis_text, reasoning_text)
    """
    
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise ValueError("DEEPSEEK_API_KEY not found in .env")

    # Initialize Client (DeepSeek uses OpenAI SDK)
    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

    # Construct the System Prompt (The "Ruthless Recruiter")
    system_prompt = """
    Role: Act as a ruthless Executive Recruiter and Resume Strategist.
    Goal: Rewrite the resume YAML to ensure an interview for the specific role provided.
    
    Your task is to analyze the provided JOB DESCRIPTION and the BASE RESUME YAML. You must adapt the resume to perfectly align with the job requirements, using the language and keywords from the JD, while maintaining truthfulness.
    
    STRATEGY INSTRUCTIONS:
    1. Analyze the Gap: Identify what the candidate is missing compared to the JD.
    2. Bridge the Gap: Rewrite bullet points to highlight transferrable skills and relevant experiences. Use strong action verbs.
    3. Keyword Optimization: Integrate specific keywords from the JD into the resume.
    4. Profile Summary: Rewrite the summary to be a powerful elevator pitch for this specific role.
    
    CRITICAL OUTPUT FORMATTING RULES:
    1. Output the Strategy Brief wrapped in <STRATEGY> tags. Explain your approach and why you made specific changes.
    2. Output the VALID YAML ONLY wrapped in ```yaml code blocks```. This YAML must be valid and ready for RenderCV.
    3. Output the Gap Analysis wrapped in <GAP_ANALYSIS> tags. Be honest about weaknesses or missing skills tailored to this role.
    4. Ensure the YAML 'settings' section has the 'pdf_path' updated to: "rendercv_output/{job_title}_{company_name}_CV.pdf" (snake_case).
    5. CRITICAL YAML FORMATTING RULES:
       - **ESCAPE COLONS:** If a value contains a colon (e.g., "Project: Title"), you MUST enclose the entire value in double quotes.
         - BAD: name: JEGA: Academic Test Facility
         - GOOD: name: "JEGA: Academic Test Facility"
       - **NO UNQUOTED SPECIAL CHARACTERS:** Wrap all strings with special chars in quotes.
    6. **LISTS ONLY:** The 'cv.sections.summary' MUST be a list of strings, not a single string block.
       - BAD: summary: "My summary text..."
       - GOOD: summary: 
                 - "My summary text..."
    7. Do not output the <think> chain in the final response, just the result.
    """

    user_content = f"""
    TARGET ROLE: {job_title} at {company_name}
    
    [JOB DESCRIPTION]
    {job_description}

    [BASE YAML RESUME]
    {base_yaml_content}
    """

    # Call DeepSeek-R1 (Reasoning Model)
    response = client.chat.completions.create(
        model="deepseek-reasoner",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ],
        temperature=0.6, # Low temp for structured YAML, but enough for creativity in phrasing
        timeout=120.0 # Extend timeout to 120s for R1 thinking time
    )

    full_response = response.choices[0].message.content
    try:
        reasoning = response.choices[0].message.reasoning_content
    except AttributeError:
        # Fallback if attribute is missing
        reasoning = "No reasoning content found in API response."
    
    # --- Debug Logging ---
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    with open(f"{log_dir}/deepseek_raw_{uuid.uuid4().hex}.txt", "w", encoding="utf-8") as log:
        log.write(f"--- CONTENT ---\n{full_response}\n\n--- REASONING ---\n{reasoning}")
    
    # --- Robust Parsing Logic ---
    
    # 1. Extract YAML (Find content between ```yaml and ```)
    # improved regex to handle potential leading/trailing whitespace or text
    yaml_match = re.search(r"```yaml\n?(.*?)```", full_response, re.DOTALL)
    if not yaml_match:
        # Fallback: Try to find the YAML structure if code blocks are missing
        # We look for the start of the CV definition typified by "cv:"
        yaml_match = re.search(r"(cv:.*)", full_response, re.DOTALL)
    
    new_yaml = yaml_match.group(1).strip() if yaml_match else None
    
    if not new_yaml:
        # Last ditch effort: if the response is ONLY yaml potentially
        if "cv:" in full_response:
             new_yaml = full_response.strip()
    if not new_yaml:
        # Last ditch effort: if the response is ONLY yaml potentially
        if "cv:" in full_response:
             new_yaml = full_response.strip()
        else:
             raise ValueError("DeepSeek failed to generate valid YAML structure.")

    # --- 🛠️ SYNTAX REPAIR 🛠️ ---
    print(f"🔧 DEBUG: Attempting to repair YAML syntax...")
    new_yaml = repair_yaml_syntax(new_yaml)
    
    # --- 🛠️ SCHEMA ENFORCEMENT 🛠️ ---
    try:
        # Load string to dict
        data = yaml.safe_load(new_yaml)
        
        # Apply Schema Fixes
        data = enforce_rendercv_schema(data)
        
        # Dump back to string (safe round-trip)
        new_yaml = yaml.dump(data, allow_unicode=True, sort_keys=False)
        
    except yaml.YAMLError as e:
        # If syntax is still bad, we might fail here, but we returned new_yaml anyway if we can't parse it
        # But wait, if safe_load fails, we can't enforce schema.
        # We'll just let it fail downstream or handle it here.
        pass # Let standard return happen, runner will catch syntax error logic elsewhere if needed

    # 2. Extract Strategy
    strategy_match = re.search(r"<STRATEGY>(.*?)</STRATEGY>", full_response, re.DOTALL)
    strategy = strategy_match.group(1).strip() if strategy_match else "Strategy not parsed."

    # 3. Extract Gap Analysis
    gap_match = re.search(r"<GAP_ANALYSIS>(.*?)</GAP_ANALYSIS>", full_response, re.DOTALL)
    gap_analysis = gap_match.group(1).strip() if gap_match else "Gap analysis not parsed."

    return strategy, new_yaml, gap_analysis, reasoning
