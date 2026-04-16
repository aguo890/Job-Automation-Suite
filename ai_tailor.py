import os
import json
import logging
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv
from ruamel.yaml import YAML

# --- SETUP LOGGING ---
logger = logging.getLogger("ai_tailor")
logger.setLevel(logging.INFO)
# Ensure it prints to stdout if not already configured by parent
if not logger.handlers:
    sh = logging.StreamHandler()
    sh.setFormatter(logging.Formatter('🤖 %(name)s: %(message)s'))
    logger.addHandler(sh)

# --- ROBUST ENV LOADING ---
current_dir = Path(__file__).parent
env_path = current_dir / ".env"
load_dotenv(dotenv_path=env_path)

def validate_integrity(master_cv_data, ai_suggested_data):
    """
    STRICT HALLUCINATION GATE (Anti-Fabrication).
    Ensures the AI didn't invent companies or modify official titles.
    Returns: (bool, list_of_violations)
    """
    violations = []
    
    # 1. Extract valid factual anchors from Master CV
    factual_anchors = {} # {company_lower: set(valid_titles_lower)}
    
    cv_sections = master_cv_data.get('cv', {}).get('sections', {})
    experience = cv_sections.get('experience', [])
    
    for role in experience:
        company = (role.get('company') or role.get('organization') or "").lower().strip()
        title = (role.get('position') or role.get('title') or "").lower().strip()
        if company:
            if company not in factual_anchors:
                factual_anchors[company] = set()
            if title:
                factual_anchors[company].add(title)

    # 2. Verify AI Suggestions against factual anchors
    if 'experience' in ai_suggested_data:
        for suggestion in ai_suggested_data['experience']:
            ai_company = (suggestion.get('company') or suggestion.get('organization') or "").lower().strip()
            ai_title = (suggestion.get('position') or suggestion.get('title') or "").lower().strip()
            
            if not ai_company or ai_company not in factual_anchors:
                violations.append(f"HAL01: Invented Company '{ai_company}'")
                continue
                
            if ai_title and ai_title not in factual_anchors[ai_company]:
                violations.append(f"HAL02: Modified Title '{ai_title}' at {ai_company}")
    
    return len(violations) == 0, violations

def generate_tailored_resume(base_yaml_content, job_description, job_title, company_name, status_callback=None):
    """
    "THE GHOSTWRITER" Architecture (Hardened):
    1. Loads Master Resume via ruamel.yaml to preserve formatting.
    2. Uses a 'Delta-Optimization' prompt to generate specific optimizations.
    3. Enforces a 'Strict Hallucination Gate' on company/title integrity.
    4. Performs selective patching, keeping 100% of human formatting/comments.
    """
    msg = "🔍 Initializing & Parsing Master Resume..."
    if status_callback: status_callback(msg)
    logger.info(msg)
    
    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.indent(mapping=2, sequence=4, offset=2)
    
    # 1. LOAD MASTER RESUME (FORMAT PRESERVING)
    try:
        master_cv = yaml.load(base_yaml_content)
    except Exception as e:
        raise ValueError(f"CRITICAL: Master YAML parsing failed: {e}")

    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise ValueError("DEEPSEEK_API_KEY not found in .env")
        
    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

    # 2. THE "DELTA-OPTIMIZATION" PROMPT
    # ... (rest of prompt logic stays same)
    system_prompt = """
    Role: Senior Resume Ghostwriter & Tech Strategist.
    Goal: Optimize the candidate's bullets and summary to align with the target JD.
    
    STRICT COMPLIANCE RULES:
    1. ZERO HALLUCINATION: You are forbidden from inventing companies, dates, or degrees.
    2. SOURCE ANCHORING: You must use the EXACT Company Names and Job Titles provided in the Master Resume.
    3. FORMATTING: BOLD matching technical keywords (e.g., **Python**, **Kubernetes**).
    4. LENGTH CONSTRAINT: Goal is 1.25 pages. Max 1.5 pages.
    
    TASK:
    - Write a 2-sentence high-impact summary hook.
    - Select ONLY the Top 3-4 most relevant experiences and top 2 projects.
    - EXPERIENCE STRATEGY (Truncate for Continuity): Retain metadata for all roles provided, but for low-signal roles, return an EMPTY `highlights` list. For high-signal roles, provide 3-4 optimized bullets.
    - PROJECT STRATEGY (Omit for Space): If a project is irrelevant to the JD, completely EXCLUDE it from the JSON output. High-signal projects should have 1-2 optimized bullets.
    - Rewrite experience bullets using 'Action + Keyword + Metric'. 
    - Identify 'Gaps' where the candidate lacks a required skill.

    OUTPUT: JSON ONLY.
    {
        "strategy_brief": "Short explanation of tailoring approach.",
        "gap_analysis": "What skills are missing for this role?",
        "summary": "Tailored summary hook.",
        "key_skills": ["Skill 1", "Skill 2"...],
        "experience": [
            {
                "company": "Exact Name from Source",
                "position": "Exact Title from Source",
                "highlights": ["Optimized bullet 1", "Optimized bullet 2"] or [] for low-signal
            }
        ],
        "projects": [
            {
                "name": "Project Name from Source",
                "highlights": ["Optimized bullet 1"] 
            }
        ]
    }
    """

    user_content = f"""
    TARGET: {job_title} at {company_name}
    JD: {job_description}
    
    MASTER SOURCE (DO NOT INVENT FROM HERE):
    {base_yaml_content}
    """

    # 3. CALL AI (DEEPSEEK REASONER)
    msg = "🧠 Sending Payload to DeepSeek R1 (Thinking Engine)..."
    if status_callback: status_callback(msg)
    logger.info(msg)
    
    response = client.chat.completions.create(
        model="deepseek-reasoner",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ],
        response_format={'type': 'json_object'}, 
        temperature=0.3
    )
    
    raw_response = response.choices[0].message.content
    reasoning = getattr(response.choices[0].message, 'reasoning_content', "Reasoning unavailable.")

    # 4. PARSE & CLEAN
    msg = "📝 Parsing Response & Cleaning JSON..."
    if status_callback: status_callback(msg)
    logger.info(msg)
    try:
        if "<think>" in raw_response:
            raw_response = raw_response.split("</think>")[-1]
        clean_json = raw_response.replace("```json", "").replace("```", "").strip()
        ai_data = json.loads(clean_json)
    except json.JSONDecodeError:
        raise ValueError(f"AI Output Malformed: {raw_response[:200]}")

    # 5. HALLUCINATION GATE (Atomic Verification)
    msg = "🛂 Validating Integrity (Hallucination Gate)..."
    if status_callback: status_callback(msg)
    logger.info(msg)
    is_intact, violations = validate_integrity(master_cv, ai_data)
    if not is_intact:
        print(f"🛑 GHOSTWRITER ABORTED: Hallucinations detected: {violations}")
        # In a real-world scenario, we might retry or fail. For now, we log and fallback to master values.
        # We will strip the offending items from ai_data to proceed safely
        ai_data['experience'] = [e for e in ai_data.get('experience', []) if not any(v in str(e) for v in violations)]

    # 6. SELECTIVE PATCHING (The Pro-Tier Move)
    msg = "🎨 Finalizing Tailored YAML..."
    if status_callback: status_callback(msg)
    logger.info(msg)
    # This preserves your header, education, and comments while updating the meat.
    cv_sections = master_cv.get('cv', {}).get('sections', {})
    
    # A. Patch Summary
    if "summary" in ai_data:
        cv_sections['summary'] = [ai_data['summary']]
        
    # B. Patch Experience (Truncate for Continuity)
    if "experience" in ai_data:
        # We iterate through ALL master roles to ensure we don't drop history
        # but we strip bullets for roles the AI didn't prioritize.
        for master_role in cv_sections.get('experience', []):
            m_co = (master_role.get('company') or master_role.get('organization') or "").strip()
            m_pos = (master_role.get('position') or master_role.get('title') or "").strip()
            
            # Look for a match in AI suggestions
            match = next((s for s in ai_data['experience'] 
                          if s.get('company') == m_co and s.get('position') == m_pos), None)
            
            if match:
                master_role['highlights'] = match.get('highlights', [])
            else:
                # Truncate for continuity (bare minimum metadata)
                master_role['highlights'] = []

    # C. Patch Projects (Omit for Space)
    if "projects" in ai_data:
        # Rebuild the projects list to ONLY include AI-selected items.
        # This reclaiming vertical space for high-signal roles.
        selected_projects = []
        for suggested in ai_data['projects']:
            for master_proj in cv_sections.get('projects', []):
                if master_proj.get('name') == suggested.get('name'):
                    master_proj['highlights'] = suggested.get('highlights', [])
                    selected_projects.append(master_proj)
                    break
        cv_sections['projects'] = selected_projects

    # D. Patch Skills (Focus Skills Injection)
    if "key_skills" in ai_data and 'skills' in cv_sections:
        new_skill_entry = {"label": "Focus Skills", "details": ", ".join(ai_data['key_skills'])}
        # Prepend to skills list if not already there
        if cv_sections['skills'] and cv_sections['skills'][0].get('label') != "Focus Skills":
            cv_sections['skills'].insert(0, new_skill_entry)
        else:
            cv_sections['skills'][0] = new_skill_entry

    # 7. EXPORT (FULL FORMAT PRESERVING)
    import io
    output_stream = io.StringIO()
    yaml.dump(master_cv, output_stream)
    final_yaml_str = output_stream.getvalue()
    
    msg = "✅ Tailoring Complete!"
    if status_callback: status_callback(msg)
    logger.info(msg)
    
    return (
        ai_data.get("strategy_brief", ""), 
        final_yaml_str, 
        ai_data.get("gap_analysis", ""), 
        reasoning
    )

if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Tailor a RenderCV resume using AI.")
    parser.add_argument("--cv", required=True, help="Path to the master CV YAML file")
    parser.add_argument("--jd", required=True, help="Path to the job description text file")
    parser.add_argument("--output", required=True, help="Path to save the tailored YAML file")
    parser.add_argument("--title", default="Software Engineer", help="Job Title")
    parser.add_argument("--company", default="Target Company", help="Company Name")

    args = parser.parse_args()

    try:
        with open(args.cv, "r", encoding="utf-8") as f:
            cv_content = f.read()
        
        with open(args.jd, "r", encoding="utf-8") as f:
            jd_content = f.read()

        print(f"🤖 Brain is tailoring CV for {args.company}...")
        brief, tailored_yaml, gaps, reasoning = generate_tailored_resume(
            cv_content, jd_content, args.title, args.company
        )

        with open(args.output, "w", encoding="utf-8") as f:
            f.write(tailored_yaml)
        
        print(f"✅ Tailoring successful! Saved to {args.output}")
        print(f"\n🧠 STRATEGY BRIEF:\n{brief}")
        if gaps:
            print(f"\n⚠️ GAP ANALYSIS:\n{gaps}")

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
