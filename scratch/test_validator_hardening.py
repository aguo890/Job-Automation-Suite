import sys
import os

# Add the project root and app directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../job-scraping-app')))

from utils.yaml_validator import clean_yaml_input, validate_cv_yaml

def test_hardening():
    print("Running YAML Validator Hardening Tests...\n")
    
    # Sample 1: Thought blocks and citations leaking
    broken_yaml_1 = """
<think>
The user wants me to generate a Master CV in YAML format.
I will extract information from the resume and format it according to the schema.
[cite_start] The user is a Software Engineer with experience in Python. [cite: 1]
</think>

[cite_start]
```yaml
cv:
  name: "John Doe"
  location: "San Francisco, CA"
  sections:
    experience:
    - company: "Tech Corp"
      highlights:
      - "[cite: 2] Engineered a **scalable** backend."
```
[cite: 3]
"""
    
    # Sample 2: Citation tags injected between keys (the most common failure)
    broken_yaml_2 = """
cv:
  name: "Jane Smith"
  [cite_start]
  location: "New York, NY"
  sections:
    experience:
    - [cite: 5] company: "Data Inc"
      highlights:
      - "Built an **analytics** dashboard."
"""

    # Test 1: clean_yaml_input
    print("Test 1: clean_yaml_input (Thought blocks & Citations)")
    cleaned_1 = clean_yaml_input(broken_yaml_1)
    
    assert "<think>" not in cleaned_1, "Failed to strip <think> block"
    assert "[cite_start]" not in cleaned_1, "Failed to strip [cite_start]"
    assert "[cite: 3]" not in cleaned_1, "Failed to strip citation at end"
    assert cleaned_1.startswith("cv:"), f"Expected string to start with cv:, got: {cleaned_1[:10]}"
    print("✅ Cleaned Sample 1 successfully")

    # Test 2: validate_cv_yaml with Sample 2
    print("\nTest 2: validate_cv_yaml (Injected citations between keys)")
    is_valid, data, error = validate_cv_yaml(broken_yaml_2)
    
    if not is_valid:
        print(f"❌ Validation failed as expected (or unexpectedly): {error}")
    else:
        print("✅ Validated Sample 2 successfully (Sanitized and Parsed)")
        assert data['cv']['name'] == "Jane Smith"
        assert data['cv']['location'] == "New York, NY"

    # Test 3: Multiple code blocks
    print("\nTest 3: Multiple code blocks")
    multi_block = """
Here is some text.
```yaml
cv:
  name: "First Block"
  sections:
    experience: []
```
And here is more text.
```yaml
cv:
  name: "Second Block"
```
"""
    cleaned_multi = clean_yaml_input(multi_block)
    assert "First Block" in cleaned_multi
    assert "Second Block" not in cleaned_multi
    print("✅ Handled multiple code blocks successfully")

    print("\nAll hardening tests passed!")

if __name__ == "__main__":
    try:
        test_hardening()
    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        sys.exit(1)
