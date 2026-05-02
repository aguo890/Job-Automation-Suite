import os
import glob
from ruamel.yaml import YAML

yaml_handler = YAML()

for root, dirs, files in os.walk('/Users/aaronguo/Github/Job-Automation-Suite'):
    if 'venv' in root or '.git' in root or 'node_modules' in root:
        continue
    for file in files:
        if file.endswith('.yaml') or file.endswith('.yml'):
            filepath = os.path.join(root, file)
            try:
                with open(filepath, 'r') as f:
                    yaml_handler.load(f)
            except Exception as e:
                print(f"Error in {filepath}: {e}")
