import json
import os
import shutil

with open("country_code_to_name.json") as file:
    country_code_to_name = json.load(file)

with open("country.json") as file:
    metadata = json.load(file)

if not os.path.exists("processed_flags"):
    os.makedirs("processed_flags")

for flag in metadata:
    if flag["code"] not in country_code_to_name:
        raise ValueError(
            f"Country code {flag['code']} not found in country_code_to_name.json"
        )
    for name in country_code_to_name[flag["code"]]:
        slug = name.replace(" ", "_")
        shutil.copy(flag["flag_4x3"], f"processed_flags/{slug}.svg")

with open("processed_flags/Non-representing.svg", "w") as file:
    file.write(
        """<svg width="400" height="300" xmlns="http://www.w3.org/2000/svg">
  <rect width="100%" height="100%" fill="grey" />
</svg>"""
    )

with open("processed_flags/Russia.svg", "w") as file:
    file.write(
        """<svg width="600" height="400" xmlns="http://www.w3.org/2000/svg">
  <rect width="600" height="133.33" y="0" fill="white" />
  <rect width="600" height="133.33" y="133.33" fill="#0084d7" />
  <rect width="600" height="133.33" y="266.66" fill="white" />
</svg>
"""
    )

print("Done")
