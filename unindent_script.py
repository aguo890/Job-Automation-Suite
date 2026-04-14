import os

file_path = "job-scraping-app/pages/2_🚀_Scraper.py"
with open(file_path, "r") as f:
    lines = f.readlines()

new_lines = []
for i, line in enumerate(lines):
    if 17 <= i <= 38: # lines 18 to 39 (0-indexed)
        continue
    
    if 39 <= i <= 109: # lines 40 to 110
        # remove exactly 4 spaces if it starts with 4 spaces
        if line.startswith("    "):
            new_lines.append(line[4:])
        else:
            new_lines.append(line)
        continue
        
    new_lines.append(line)

# Insert the new headers at the position of line 18
header = """st.title("🛠️ Scraper Controls")
st.caption("Trigger a manual scraping run across all configured companies.")
st.markdown("---")

"""
new_lines.insert(17, header)

with open(file_path, "w") as f:
    f.writelines(new_lines)

print("Done")
