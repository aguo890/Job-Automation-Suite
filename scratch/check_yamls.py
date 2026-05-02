import os
import glob
from ruamel.yaml import YAML

yaml_handler = YAML()

for filepath in glob.glob('/Users/aaronguo/Github/Job-Automation-Suite/generated_cvs/*.yaml'):
    try:
        with open(filepath, 'r') as f:
            yaml_handler.load(f)
    except Exception as e:
        print(f"Error in {filepath}: {e}")
