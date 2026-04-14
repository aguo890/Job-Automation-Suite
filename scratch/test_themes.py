import re

def get_theme_from_yaml(yaml_content):
    """Robustly extracts theme name from RenderCV YAML."""
    match = re.search(r'(?m)^\s*theme\s*:\s*["\']?([a-zA-Z0-9_-]+)["\']?', yaml_content)
    if match:
        return match.group(1)
    return "classic"

def apply_theme_to_yaml(yaml_content, theme_name):
    """Robustly replaces the theme value in RenderCV YAML while preserving whitespace and comments."""
    pattern = r'(?m)^(\s*theme\s*:\s*).+'
    replacement = rf'\g<1>{theme_name}'
    return re.sub(pattern, replacement, yaml_content)

# Test cases
test_yaml_1 = """
design:
  theme: classic # current theme
  page: 0.5in
"""

test_yaml_2 = """
design:
    theme:  "moderncv"
    page: 0.5in
"""

test_yaml_3 = """
design:
  theme: 'engineeringresumes'
"""

def test():
    print("Testing get_theme_from_yaml:")
    print(f"Test 1: {get_theme_from_yaml(test_yaml_1)}")
    print(f"Test 2: {get_theme_from_yaml(test_yaml_2)}")
    print(f"Test 3: {get_theme_from_yaml(test_yaml_3)}")
    
    print("\nTesting apply_theme_to_yaml:")
    new_yaml_1 = apply_theme_to_yaml(test_yaml_1, "sb2nov")
    print(f"Test 1 Updated:\n{new_yaml_1}")
    
    new_yaml_2 = apply_theme_to_yaml(test_yaml_2, "ink")
    print(f"Test 2 Updated:\n{new_yaml_2}")

if __name__ == "__main__":
    test()
