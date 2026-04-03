import os
import sys
import yaml

# Correct Python path
sys.path.insert(0, os.getcwd())
from ai_tailor import validate_integrity

def test_hallucination_gate():
    master_cv = {
        "cv": {
            "sections": {
                "experience": [
                    {"company": "SpaceX", "position": "Launch Engineer"},
                    {"company": "Tesla", "position": "Firmware Engineer"}
                ]
            }
        }
    }
    
    # CASE 1: Valid Optimization
    valid_suggestion = {
        "experience": [
            {"company": "SpaceX", "position": "Launch Engineer", "highlights": ["Optimized bullet"]}
        ]
    }
    is_intact, violations = validate_integrity(master_cv, valid_suggestion)
    assert is_intact == True
    print("✅ Valid Optimization Passed")
    
    # CASE 2: Invented Company
    hallucinated_co = {
        "experience": [
            {"company": "Mars Colonization Corp", "position": "Lead Terraformer"}
        ]
    }
    is_intact, violations = validate_integrity(master_cv, hallucinated_co)
    assert is_intact == False
    assert "HAL01: Invented Company 'mars colonization corp'" in violations
    print("✅ Hallucinated Company Blocked")
    
    # CASE 3: Modified Title
    modified_title = {
        "experience": [
            {"company": "SpaceX", "position": "CEO"}
        ]
    }
    is_intact, violations = validate_integrity(master_cv, modified_title)
    assert is_intact == False
    assert "HAL02: Modified Title 'ceo' at spacex" in violations
    print("✅ Modified Title Blocked")

if __name__ == "__main__":
    test_hallucination_gate()
    print("\n✨ ALL INTEGRITY CHECKS PASSED!")
