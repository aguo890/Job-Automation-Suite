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

def generate_tailored_resume(base_yaml_content, job_description, job_title, company_name):
    """
    1. Loads Base YAML (Dictionary).
    2. Asks AI for specific text updates in JSON.
    3. Injects updates into the Base structure safely.
    """
    
    # 1. LOAD BASE RESUME (Golden Structure)
    try:
        base_resume = yaml.safe_load(base_yaml_content)
    except yaml.YAMLError as e:
        raise ValueError(f"CRITICAL: Your source YAML is broken. Fix it first: {e}")

    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise ValueError("DEEPSEEK_API_KEY not found in .env")
        
    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

    # 2. THE "NUCLEAR" PROMPT
    # We use Few-Shot examples to force the style.
    system_prompt = """
    Role: Ruthless FAANG Technical Recruiter & Resume Editor.
    Task: Rewrite resume content to strictly match a JD.
    
    CRITICAL RULES (VIOLATION = FAILURE):
    1. **MANDATORY BOLDING**: You MUST bold (using **text**) ANY skill mentioned in the JD.
       - BAD: "Built a React app with Python."
       - GOOD: "Architected a **React** frontend backed by **Python** and **FastAPI**."
    
    2. **DELETE FLUFF**: Banned phrases: "team player", "demonstrating", "responsible for", "helped", "worked on", "gained experience".
       - BAD: "Responsible for creating a dashboard demonstrating data visualization."
       - GOOD: "Deployed a **Real-Time Dashboard** processing 10k+ events/sec."
    
    3. **METRIC OBSESSION**: Every bullet point SHOULD have a number (%, $, time saved, users, latency).
    
    4. **SUMMARY STYLE**: No "Passionate student...". Go straight to value.
       - GOOD: "**Software Engineer** with 3+ years in **Distributed Systems**. Scaled **Kubernetes** clusters handling 5M requests/day."
    
    OUTPUT FORMAT:
    Return valid JSON only. Do not wrap in markdown blocks.
    {
        "strategy_brief": "Briefly explain what you fixed (max 2 sentences).",
        "gap_analysis": "Identify 2-3 missing critical skills from the JD.",
        "summary": "The new 2-line summary.",
        "key_skills": ["List", "Of", "Top", "Matched", "Skills"],
        "experience_updates": [
            {
                "company": "Exact Company Name From Resume",
                "tailored_bullets": [
                    "Action Verb + **Keyword** + **Metric** + Result.",
                    "Action Verb + **Keyword** + **Metric** + Result."
                ]
            }
        ]
    }
    """

    user_content = f"""
    JOB TARGET: {job_title} at {company_name}
    
    JOB DESCRIPTION (KEYWORDS TO EXTRACT & BOLD):
    {job_description}
    
    CURRENT RESUME CONTENT:
    {base_yaml_content}
    
    INSTRUCTIONS:
    1. Scan the JD for technical keywords (e.g., React, AWS, CI/CD).
    2. Rewrite my experience bullets to include these keywords IF I have done them.
    3. Bold the keywords using markdown (**Keyword**).
    4. Shorten bullets to be punchy.
    """

    # 3. CALL AI
    # Lower temperature for stricter formatting
    response = client.chat.completions.create(
        model="deepseek-reasoner",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ],
        response_format={'type': 'json_object'}, 
        temperature=0.3, 
        timeout=120.0
    )
    
    raw_response = response.choices[0].message.content
    
    # Extract Reasoning Content (for dashboard display)
    try:
        reasoning = getattr(response.choices[0].message, 'reasoning_content', "Reasoning not accessible.")
    except Exception:
        reasoning = "Reasoning unavailable."

    # 4. PARSE JSON (Robust)
    try:
        # R1 sometimes puts the json inside ```json ... ``` or just raw.
        clean_json = raw_response.replace("```json", "").replace("```", "").strip()
        # Specific fix if R1 adds chatter before the JSON
        if "{" in clean_json:
            clean_json = clean_json[clean_json.find("{"):clean_json.rfind("}")+1]
        
        ai_data = json.loads(clean_json)
    except json.JSONDecodeError:
        # Fallback: simple text extraction if JSON fails hard
        raise ValueError(f"AI Output Malformed. Raw: {raw_response[:200]}")

    # 5. THE ASSEMBLER (Injecting)
    
    # A. Inject Summary
    if "summary" in ai_data:
        if 'sections' not in base_resume.get('cv', {}):
             if 'cv' not in base_resume: base_resume['cv'] = {}
             base_resume['cv']['sections'] = {}
        base_resume['cv']['sections']['summary'] = [ai_data['summary']]

    # B. Inject Focus Skills (Top of Skills Section)
    if "key_skills" in ai_data and ai_data['key_skills']:
        sections = base_resume['cv'].get('sections', {})
        if 'skills' in sections:
            # Check if we already added Focus Skills to avoid duplicates on re-runs
            if sections['skills'] and sections['skills'][0].get('label') == "Focus Skills":
                sections['skills'].pop(0)
            
            new_skill_entry = {
                "label": "Focus Skills",
                "details": ", ".join(ai_data['key_skills'])
            }
            sections['skills'].insert(0, new_skill_entry)

    # C. Inject Experience
    if "experience_updates" in ai_data:
        resume_experiences = base_resume['cv']['sections'].get('experience', [])
        for update in ai_data['experience_updates']:
            target_company = update.get('company', '').lower()
            # Fuzzy match company name
            for entry in resume_experiences:
                if target_company in entry.get('company', '').lower() or entry.get('company', '').lower() in target_company:
                    entry['highlights'] = update['tailored_bullets']
                    break

    # 6. DUMP YAML
    final_yaml_str = yaml.dump(base_resume, sort_keys=False, allow_unicode=True)
    
    return ai_data.get("strategy_brief", ""), final_yaml_str, ai_data.get("gap_analysis", ""), reasoning
