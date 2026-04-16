import sys
import os
import json
import yaml

# Add root to sys.path
sys.path.append(os.getcwd())

from core.llm_sanitizer import sanitize_llm_payload, validate_cv_yaml

def test_resilience():
    print("Testing AI Resilience Layer (core.llm_sanitizer)...\n")
    
    # 1. TEST: JSON Payload with Reasoning + Citations
    json_payload = """
<think>
User wants to tailor their resume for a Senior AI role.
I will emphasize their experience with LLMs and RAG.
[cite_start] The candidate has built multiple RAG pipelines. [cite: 1]
</think>

```json
{
  "strategy_brief": "Focused on RAG and LLM infrastructure.",
  "experience": [
    {
      "company": "Tech Corp",
      "position": "AI Engineer",
      "highlights": [
        "[cite: 2] Engineered a **scalable** RAG pipeline."
      ]
    }
  ]
}
```
"""
    print("Test 1: JSON Payload Sanitization")
    sanitized_json = sanitize_llm_payload(json_payload)
    
    assert "<think>" not in sanitized_json
    assert "[cite_start]" not in sanitized_json
    assert "```json" not in sanitized_json
    
    # Verify it parses as JSON
    data = json.loads(sanitized_json)
    assert data['strategy_brief'] == "Focused on RAG and LLM infrastructure."
    print("✅ JSON Sanitization & Parsing Successful")

    # 2. TEST: YAML Payload (Onboarding)
    yaml_payload = """
[cite_start]
```yaml
cv:
  name: "Aaron Guo"
  sections:
    experience:
    - company: "Google"
      [cite: 5] position: "AI Researcher"
```
"""
    print("\nTest 2: YAML Payload Sanitization")
    sanitized_yaml = sanitize_llm_payload(yaml_payload)
    
    assert "[cite_start]" not in sanitized_yaml
    assert "```yaml" not in sanitized_yaml
    
    # Verify it parses as YAML
    is_valid, cv_data, err = validate_cv_yaml(yaml_payload)
    assert is_valid, f"YAML Validation failed: {err}"
    assert cv_data['cv']['name'] == "Aaron Guo"
    print("✅ YAML Sanitization & Parsing Successful")

    # 3. TEST: Bare Payload (No Fences)
    bare_payload = """
<think> Reasoning here </think>
{
  "status": "success"
}
"""
    print("\nTest 3: Bare Payload (No Fences)")
    sanitized_bare = sanitize_llm_payload(bare_payload)
    assert sanitized_bare.startswith("{")
    assert "status" in sanitized_bare
    print("✅ Bare Payload Sanitization Successful")

    print("\nAll Resilience Layer tests passed!")

if __name__ == "__main__":
    try:
        test_resilience()
    except Exception as e:
        print(f"\n❌ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
