import json
import os
from pathlib import Path

# --- Configuration ---
# Targeting the specific directory where your datasets live
DATASETS_DIR = Path("data/raw/datasets")

OLD_ROLE = "businessDataOwner"
NEW_ROLE = "dataOwner"

def migrate_file(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"⚠️  Error reading {file_path.name}: {e}")
        return False

    changed = False
    
    # 1. Check if the qualified attribution list exists
    if "prov:qualifiedAttribution" in data and isinstance(data["prov:qualifiedAttribution"], list):
        
        # 2. Iterate through the attribution objects
        for attribution in data["prov:qualifiedAttribution"]:
            current_role = attribution.get("dcat:hadRole")
            
            # 3. Targeted Replacement
            if current_role == OLD_ROLE:
                attribution["dcat:hadRole"] = NEW_ROLE
                changed = True

    # 4. Save only if changes were made
    if changed:
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            print(f"✅ Updated: {file_path.name}")
            return True
        except Exception as e:
            print(f"❌ Error writing {file_path.name}: {e}")
            return False
    
    return False

def main():
    if not DATASETS_DIR.exists():
        print(f"❌ Directory not found: {DATASETS_DIR}")
        return

    print(f"--- Starting Migration: {OLD_ROLE} -> {NEW_ROLE} ---")
    
    files_processed = 0
    files_changed = 0

    # Loop over all json files in the directory
    for file_path in DATASETS_DIR.glob("*.json"):
        files_processed += 1
        if migrate_file(file_path):
            files_changed += 1

    print("\n--- Migration Complete ---")
    print(f"Scanned: {files_processed} files")
    print(f"Updated: {files_changed} files")

if __name__ == "__main__":
    main()