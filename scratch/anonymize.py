import os

file_path = "rendercv/master_cv.yaml.example"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

replacements = {
    "Aaron Guo": "John Doe",
    "Washington, D.C.": "New York, NY",
    "Washington, DC": "New York, NY",
    "aguo890@gwmail.gwu.edu": "johndoe@example.com",
    "+1 980-337-0681": "+1 555-010-0000",
    "https://aguo890.github.io/": "https://johndoe.com",
    "guo-aaron": "johndoe",
    "aguo890/Job-Automation-Suite": "johndoe/Enterprise-Automation-Suite",
    "aguo890/capstone": "johndoe/capstone",
    "aguo890": "johndoe",
    "xAI": "Tech Innovators Inc",
    "LineSight - AI Factory Analytics Platform": "DataFlow Systems - AI Analytics",
    "LineSight": "DataFlow Systems",
    "The George Washington University": "State University",
    "George Washington University": "State University",
    "Three Stars Fashion Group": "Global Logistics LLC",
    "Sunwater Capital": "Apex Financial",
    "China Fun Restaurants": "Local Retail Corp",
    "Colossus facility": "Cloud facility",
    "100,000+ NVIDIA H100 GPU": "10,000+ node",
    "Job Automation Suite": "Enterprise Automation Suite",
    "OpenClaw Agentic Suite": "AI Agentic Suite",
    "JEGA: Academic Test Facility": "Proctoring Platform",
    "Aaron": "John",
    "aaron_guo": "john_doe",
    "Guo": "Doe"
}

for old, new in replacements.items():
    content = content.replace(old, new)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Anonymization complete.")
