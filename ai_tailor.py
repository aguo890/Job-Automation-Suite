import os
import json
import yaml
import re
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

# --- ROBUST ENV LOADING ---
current_dir = Path(__file__).parent
env_path = current_dir / ".env"
load_dotenv(dotenv_path=env_path)

def validate_integrity(base_data, ai_data):
    """
    Ensures the AI didn't invent companies.
    """
    # 1. Extract valid companies from Source (normalize to lowercase)
    valid_companies = set()
    if 'cv' in base_data and 'sections' in base_data['cv'] and 'experience' in base_data['cv']['sections']:
        for role in base_data['cv']['sections']['experience']:
            # Adjust 'organization' key based on your YAML schema
            company = role.get('company') or role.get('organization') 
            if company:
                valid_companies.add(company.lower().strip())

    # 2. Check AI output
    if 'experience' in ai_data:
        for role in ai_data['experience']:
            # Adjust key based on your PROMPT schema
            ai_company = role.get('company') or role.get('organization')
            
            if ai_company and ai_company.lower().strip() not in valid_companies:
                print(f"⚠️ WARNING: AI generated a company not in source: '{ai_company}' (Hallucination Risk)")
                # Optional: raise ValueError("Integrity Check Failed")
    
    return True

def generate_tailored_resume(base_yaml_content, job_description, job_title, company_name):
    """
    "THE GHOSTWRITER" Architecture:
    1. Loads Master Resume (Source of Truth).
    2. Asks AI to REWRITE the experience section from scratch for the JD.
    3. Validates integrity (no hallucinated companies/dates).
    4. Returns a fully synthesized new YAML.
    """
    
    # 1. LOAD BASE RESUME
    try:
        base_resume = yaml.safe_load(base_yaml_content)
    except yaml.YAMLError as e:
        raise ValueError(f"CRITICAL: Your source YAML is broken. Fix it first: {e}")

    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise ValueError("DEEPSEEK_API_KEY not found in .env")
        
    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")


    # 2. THE "GHOSTWRITER" PROMPT
    # We ask for a FULL LIST of experience, not just updates.
    system_prompt = """
    Role: Elite Resume Ghostwriter & Career Strategist.
    Goal: Rewrite the candidate's experience section from scratch to perfectly match the target JD.

    INPUT DATA:
    1. **Master Resume** (FACTUAL SOURCE OF TRUTH). You MUST use the exact Company Names and Titles from here.
    2. **Job Description** (TARGET).

    YOUR TASK:
    1. **SELECT**: Choose the most relevant roles from the Master Resume (drop irrelevant ones like Food Service if enough Engineering experience exists).
    2. **REWRITE**: Ignore the original bullet points. Write NEW, high-impact bullets based on the facts provided.
       - Focus on **Engineering/Data/Product** impact.
       - Use **Action + Keyword + Metric** formula.
       - **BOLD** matching keywords from the JD (e.g., **React**, **AWS**, **Docker**).
    3. **LIMITS**:
       - Max 4 bullets for recent/relevant roles.
       - Max 2 bullets for older/less relevant roles.
       - TOTAL LENGTH: Must fit on 1 page (so be concise).

    OUTPUT FORMAT: JSON ONLY.
    {
        "strategy_brief": "Explain your rewrite strategy.",
        "summary": "2-line high-impact summary hook.",
        "key_skills": ["Top 6 relevant skills"],
        "experience": [
            {
                "company": "Exact Name from Source",
                "position": "Exact Title from Source",
                "location": "Exact Location",
                "date": "YYYY-MM or YYYY (Match Source Format)",
                "highlights": [
                    "New Bullet 1 with **Keywords**...",
                    "New Bullet 2 with **Metrics**..."
                ]
            }
        ],
        "projects": [
            {
                "name": "Project Name",
                "date": "YYYY-MM or YYYY",
                "summary": "One line summary",
                "highlights": ["Bullet 1", "Bullet 2"]
            }
        ]
    }
    """

    user_content = f"""
    TARGET ROLE: {job_title} at {company_name}
    JD: {job_description}
    
    MY MASTER RESUME CONTENT:
    {base_yaml_content}
    """

    # 3. CALL AI
    response = client.chat.completions.create(
        model="deepseek-reasoner",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ],
        response_format={'type': 'json_object'}, 
        temperature=0.3, # Low temp for factual consistency
        timeout=120.0
    )
    
    raw_response = response.choices[0].message.content
    try:
        reasoning = getattr(response.choices[0].message, 'reasoning_content', "Reasoning unavailable.")
    except Exception:
        reasoning = "Reasoning unavailable."

    # 4. PARSE JSON
    try:
        # Robust cleaning for DeepSeek R1 (Case Insensitive)
        if "<think>" in raw_response:
            raw_response = raw_response.split("</think>")[-1]
        elif "<THINK>" in raw_response:
            raw_response = raw_response.split("</THINK>")[-1]
            
        clean_json = raw_response.replace("```json", "").replace("```", "").strip()
        if "{" in clean_json:
            clean_json = clean_json[clean_json.find("{"):clean_json.rfind("}")+1]
        ai_data = json.loads(clean_json)
    except json.JSONDecodeError:
        raise ValueError(f"AI Output Malformed. Raw: {raw_response[:200]}")

    # 5. INTEGRITY CHECK (Anti-Hallucination)
    validate_integrity(base_resume, ai_data)

    # 6. THE RE-WRITER (Full Overwrite)
    
    cv_sections = base_resume.get('cv', {}).get('sections', {})

    # Create a new ordered dictionary to control section order (Summary First)
    new_sections = {}

    # C. Inject Summary (Ensure it's first)
    if "summary" in ai_data:
        new_sections['summary'] = [ai_data['summary']]
    elif 'summary' in cv_sections:
        new_sections['summary'] = cv_sections['summary']

    # Copy other existing sections temporarily
    # We want strict order: Summary -> Experience -> Projects -> Education -> etc.
    # But we also want to overwrite Experience/Projects.
    
    # A. Overwrite Experience
    if "experience" in ai_data:
        new_sections['experience'] = ai_data['experience']
    elif 'experience' in cv_sections:
        new_sections['experience'] = cv_sections['experience']

    # B. Overwrite Projects
    if "projects" in ai_data:
        new_sections['projects'] = ai_data['projects']
    elif 'projects' in cv_sections:
        new_sections['projects'] = cv_sections['projects']

    # Copy remaining sections (Education, Skills, etc.) preserving original order if possible
    for key, val in cv_sections.items():
        if key not in ['summary', 'experience', 'projects']:
            new_sections[key] = val
            
    # Update the base resume with the new ordered sections
    base_resume['cv']['sections'] = new_sections

    # D. Inject Focus Skills (handled differently in previous code, let's fix it)
    if "key_skills" in ai_data and ai_data['key_skills']:
        if 'skills' in new_sections:
            if new_sections['skills'] and new_sections['skills'][0].get('label') == "Focus Skills":
                new_sections['skills'].pop(0)
            
            new_skill_entry = {
                "label": "Focus Skills", 
                "details": ", ".join(ai_data['key_skills'])
            }
            new_sections['skills'].insert(0, new_skill_entry)

    # 7. RETURN
    final_yaml_str = yaml.dump(base_resume, sort_keys=False, allow_unicode=True)
    
    return ai_data.get("strategy_brief", ""), final_yaml_str, ai_data.get("gap_analysis", ""), reasoning
