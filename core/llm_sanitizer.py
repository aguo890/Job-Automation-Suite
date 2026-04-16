"""
LLM Sanitizer & Resilience Layer.

Provides format-agnostic "healing" for AI-generated payloads (YAML/JSON).
Strips thought blocks, AI citations, and markdown fences to prevent parse errors.
"""
import re
import os
import yaml


def sanitize_llm_payload(raw_text: str) -> str:
    """
    Format-agnostic "Healer" for AI payloads.
    
    1. Strips <think> reasoning blocks (DeepSeek-R1).
    2. Strips AI citations ([cite_start], [cite: 1]) with smart whitespace handling.
    3. Extracts content from markdown code fences (json, yaml, yml).
    4. Falls back to sanitized raw text if no fences are found.
    """
    if not raw_text:
        return ""
    
    text = raw_text.strip()
    
    # 1. Strip Thought Blocks (e.g. <think> reasoning </think>)
    # Using re.DOTALL to match across multiple lines
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    
    # 2. Strip AI Citations (e.g. [cite_start], [cite: 1, 2], etc.)
    # Smart whitespace handling: strip trailing whitespace to prevent YAML/JSON indentation errors.
    text = re.sub(r"\[cite_?start\]\s*", "", text)
    text = re.sub(r"\[cite:?\s*[\d,\s]*\]\s*", "", text)
    
    # 3. Handle markdown code fences (json, yaml, yml, bare)
    # This regex is format-agnostic and handles the most common AI artifacts.
    fence_pattern = r"```(?:json|ya?ml)?\s*\n(.*?)```"
    match = re.search(fence_pattern, text, re.DOTALL)
    
    if match:
        # Return the content of the first code fence found
        return match.group(1).strip()
    
    # 4. Fallback: If no fences found, just return the stripped/sanitized text
    # (Sometimes AI output is a bare JSON or YAML string)
    return text.strip()


def validate_cv_yaml(raw_text: str) -> tuple:
    """
    Validates pasted CV YAML against the expected RenderCV schema.
    Returns: (is_valid: bool, parsed_data: dict | None, error_message: str)
    """
    cleaned = sanitize_llm_payload(raw_text)
    
    if not cleaned:
        return False, None, "Input is empty."
    
    try:
        data = yaml.safe_load(cleaned)
    except yaml.YAMLError as e:
        line_info = ""
        if hasattr(e, 'problem_mark') and e.problem_mark:
            line_info = f" (line {e.problem_mark.line + 1}, column {e.problem_mark.column + 1})"
        return False, None, f"YAML Syntax Error{line_info}: {str(e)}"
    
    if not isinstance(data, dict) or "cv" not in data:
        return False, None, "Missing required key: `cv`."
    
    return True, data, ""


def validate_filtering_yaml(raw_text: str) -> tuple:
    """
    Validates pasted filtering YAML against the expected config schema.
    """
    cleaned = sanitize_llm_payload(raw_text)
    
    if not cleaned:
        return False, None, "Input is empty."
    
    try:
        data = yaml.safe_load(cleaned)
    except yaml.YAMLError as e:
        return False, None, f"YAML Syntax Error: {str(e)}"
    
    if not isinstance(data, dict):
        return False, None, "Invalid structure: Expected a dictionary."
    
    if "tiered_skills" not in data or "titles" not in data:
        return False, None, "Missing required keys: `tiered_skills` or `titles`."
    
    return True, data, ""


def merge_filtering_with_defaults(user_config: dict, defaults_path: str) -> dict:
    """
    Deep-merges user-provided filtering config with defaults.
    """
    defaults = {}
    if os.path.exists(defaults_path):
        try:
            with open(defaults_path, "r", encoding="utf-8") as f:
                defaults = yaml.safe_load(f) or {}
        except Exception:
            defaults = {}
    
    merged = dict(defaults)
    for key, value in user_config.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = {**merged[key], **value}
        else:
            merged[key] = value
    
    return merged


def extract_cv_filename(cv_data: dict) -> str:
    """
    Parses cv.name and returns a safe filename.
    """
    try:
        name = cv_data.get("cv", {}).get("name", "")
        if not name or not isinstance(name, str):
            return "Master_CV.yaml"
        
        safe_name = "".join(c for c in name if c.isalnum() or c in (" ", "-")).strip()
        safe_name = safe_name.replace(" ", "_")
        return f"{safe_name}_CV.yaml"
    except Exception:
        return "Master_CV.yaml"
