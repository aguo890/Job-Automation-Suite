import os
import json
import re
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv
from ruamel.yaml import YAML

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

def generate_tailored_resume(base_yaml_content, job_description, job_title, company_name):
    """
    "THE GHOSTWRITER" Architecture (Hardened):
    1. Loads Master Resume via ruamel.yaml to preserve formatting.
    2. Uses a 'Delta-Optimization' prompt to generate specific optimizations.
    3. Enforces a 'Strict Hallucination Gate' on company/title integrity.
    4. Performs selective patching, keeping 100% of human formatting/comments.
    """
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
    # Focused only on strategy, hooks, and bullet optimization.
    system_prompt = """
    Role: Senior Resume Ghostwriter & Tech Strategist.
    Goal: Optimize the candidate's bullets and summary to align with the target JD.
    
    STRICT COMPLIANCE RULES:
    1. ZERO HALLUCINATION: You are forbidden from inventing companies, dates, or degrees.
    2. SOURCE ANCHORING: You must use the EXACT Company Names and Job Titles provided in the Master Resume.
    3. FORMATTING: BOLD matching technical keywords (e.g., **Python**, **Kubernetes**).
    
    TASK:
    - Write a 2-sentence high-impact summary hook.
    - Select the Top 6 Key Skills matching the JD.
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
                "highlights": ["Optimized bullet 1", "Optimized bullet 2"]
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
    try:
        if "<think>" in raw_response:
            raw_response = raw_response.split("</think>")[-1]
        clean_json = raw_response.replace("```json", "").replace("```", "").strip()
        ai_data = json.loads(clean_json)
    except json.JSONDecodeError:
        raise ValueError(f"AI Output Malformed: {raw_response[:200]}")

    # 5. HALLUCINATION GATE (Atomic Verification)
    is_intact, violations = validate_integrity(master_cv, ai_data)
    if not is_intact:
        print(f"🛑 GHOSTWRITER ABORTED: Hallucinations detected: {violations}")
        # In a real-world scenario, we might retry or fail. For now, we log and fallback to master values.
        # We will strip the offending items from ai_data to proceed safely
        ai_data['experience'] = [e for e in ai_data.get('experience', []) if not any(v in str(e) for v in violations)]

    # 6. SELECTIVE PATCHING (The Pro-Tier Move)
    # This preserves your header, education, and comments while updating the meat.
    cv_sections = master_cv.get('cv', {}).get('sections', {})
    
    # A. Patch Summary
    if "summary" in ai_data:
        cv_sections['summary'] = [ai_data['summary']]
        
    # B. Patch Experience
    if "experience" in ai_data:
        # Match by company/title to ensure we maintain order
        for suggested in ai_data['experience']:
            for master_role in cv_sections.get('experience', []):
                m_co = (master_role.get('company') or master_role.get('organization') or "").strip()
                m_pos = (master_role.get('position') or master_role.get('title') or "").strip()
                
                if m_co == suggested.get('company') and m_pos == suggested.get('position'):
                    master_role['highlights'] = suggested['highlights']

    # C. Patch Projects
    if "projects" in ai_data:
        for suggested in ai_data['projects']:
            for master_proj in cv_sections.get('projects', []):
                if master_proj.get('name') == suggested.get('name'):
                    master_proj['highlights'] = suggested['highlights']

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
    
    return (
        ai_data.get("strategy_brief", ""), 
        final_yaml_str, 
        ai_data.get("gap_analysis", ""), 
        reasoning
    )
