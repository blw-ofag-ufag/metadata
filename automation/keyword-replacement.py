import os
import json

# Configuration
input_directory = "data/raw/datasets/"
target_keyword = "main crops"
replacement_keywords = ["main-crops"]

# Loop over each file in the specified directory
for filename in os.listdir(input_directory):
    if filename.endswith(".json"):
        file_path = os.path.join(input_directory, filename)
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"Error reading {file_path}: {e}")
            continue

        # Process the 'dcat:keyword' array if it exists
        if "dcat:keyword" in data and isinstance(data["dcat:keyword"], list):
            new_keywords = []
            for keyword in data["dcat:keyword"]:
                # Replace target_keyword with all replacement_keywords
                if keyword == target_keyword:
                    new_keywords.extend(replacement_keywords)
                else:
                    new_keywords.append(keyword)
            data["dcat:keyword"] = new_keywords

            # Write the updated JSON back to the file (overwriting the original)
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"Processed file: {file_path}")
        else:
            print(f"Skipped file (no 'dcat:keyword' list found): {file_path}")
