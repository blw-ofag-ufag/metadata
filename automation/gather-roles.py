import os
import json

# Adjust these paths to fit your environment
DATASET_DIR = os.path.expanduser("data/raw/datasets")
OUTPUT_FILE = os.path.expanduser("data/processed/personRoleList.json")

def extract_person_roles(data):
    """
    Given a single JSON dataset object, return a list of dicts:
      [
        {
          "agent": "p-12345",
          "name": "Example Person",
          "role": "dataSteward",
          "datasetId": "...",
          "titles": { "de": "...", "fr": "...", "it": "...", "en": "..." }
        },
        ...
      ]
    """
    results = []
    
    # Basic dataset info
    dataset_id = data.get("dct:identifier")
    
    # The 'dct:title' might be a string or an object with multiple languages.
    # We'll handle both cases gracefully.
    dataset_title = data.get("dct:title", {})
    if isinstance(dataset_title, str):
        # If it's just a single string, store that under e.g. "en"
        dataset_title = {"en": dataset_title}
    
    # If 'prov:qualifiedAttribution' is not present or not a list, skip
    attributions = data.get("prov:qualifiedAttribution", [])
    if not isinstance(attributions, list):
        return results
    
    for attrib in attributions:
        agent_id = attrib.get("prov:agent")
        role = attrib.get("dcat:hadRole")
        person_name = attrib.get("schema:name")  # optional, may not exist
        
        if agent_id and role in ("dataOwner", "dataSteward", "dataCustodian"):
            # Build a record that indicates this person has that role
            # for the current dataset.
            record = {
                "agent": agent_id,
                "name": person_name,
                "role": role,
                "datasetId": dataset_id,
                "titles": {
                    # We'll extract each possible language key if present
                    "de": dataset_title.get("de"),
                    "fr": dataset_title.get("fr"),
                    "it": dataset_title.get("it"),
                    "en": dataset_title.get("en"),
                }
            }
            results.append(record)

    return results

def process_all_files():
    # We'll build an internal data structure keyed by agent ID.
    # Example:
    # {
    #   "p-12345": {
    #       "name": "Alice Example",
    #       "roles": {
    #           "dataOwner": [
    #               { "dct:identifier": "XYZ", "dct:title": {...} }
    #           ],
    #           "dataSteward": [...],
    #           "dataCustodian": [...]
    #       }
    #   },
    #   ...
    # }
    persons_dict = {}

    # Loop over all JSON files in the dataset directory
    for filename in os.listdir(DATASET_DIR):
        if filename.endswith(".json"):
            file_path = os.path.join(DATASET_DIR, filename)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception as e:
                print(f"Error reading {file_path}: {e}")
                continue
            
            # Extract roles from this JSON object
            person_records = extract_person_roles(data)
            
            # Merge each record into our persons_dict
            for rec in person_records:
                agent_id = rec["agent"]
                role = rec["role"]
                dataset_id = rec["datasetId"]
                titles = rec["titles"]
                
                # Initialize person if not present
                if agent_id not in persons_dict:
                    persons_dict[agent_id] = {
                        "name": rec["name"],
                        "roles": {
                            "dataOwner": [],
                            "dataSteward": [],
                            "dataCustodian": []
                        }
                    }
                
                # Overwrite name if present (in case some files have "schema:name" while others do not)
                if rec["name"]:
                    persons_dict[agent_id]["name"] = rec["name"]
                
                # Append the dataset to the correct role list
                persons_dict[agent_id]["roles"][role].append({
                    "dct:identifier": dataset_id,
                    "dct:title": {
                        "de": titles["de"],
                        "fr": titles["fr"],
                        "it": titles["it"],
                        "en": titles["en"]
                    }
                })
    
    # Convert our dictionary into the final array structure
    final_list = []
    for agent_id, info in persons_dict.items():
        # Build each role object, but only include the role if it has datasets
        roles_array = []
        for rkey, datasets in info["roles"].items():
            if datasets:  # Only add the role if the list of datasets is not empty
                roles_array.append({
                    "role": rkey,
                    "datasets": datasets
                })
        
        final_list.append({
            "personId": agent_id,
            "name": info["name"],  # might be None if no name found
            "roles": roles_array
        })
    
    # Write the final structure to output
    with open(OUTPUT_FILE, "w", encoding="utf-8") as out_f:
        json.dump(final_list, out_f, ensure_ascii=False, indent=4)
    
    print("All person-role data has been written to:", OUTPUT_FILE)

if __name__ == "__main__":
    process_all_files()
    print("Processing complete.")
