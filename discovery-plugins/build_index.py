"""
Builds the index.json from the OSINT LIAR discovery plugins included in this directory.
"""

import os
import json
import hashlib
from pathlib import Path


def calculate_sha256(file_path, fields_dict) -> str:
    """Calculate SHA256 checksum of a file using specific fields from a dictionary."""
    sha256_hash = hashlib.sha256()

    # Sort the keys for consistency and build a string of field values
    sorted_keys = sorted(fields_dict.keys())
    for key in sorted_keys:
        value = fields_dict.get(key, "")
        sha256_hash.update(str(value).encode('utf-8'))

    return sha256_hash.hexdigest()


def process_json_files(directory, base_url):
    """Recursively find JSON files in a directory and generate index.json."""
    index = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".json"):
                file_path = os.path.join(root, file)

                # Load JSON content
                with open(file_path, "r", encoding="utf-8") as f:
                    try:
                        content = json.load(f)
                    except json.JSONDecodeError:
                        print(f"Skipping invalid JSON file: {file_path}")
                        continue

                # Extract required fields for use in the checksum and the package index
                file_name = Path(file).stem
                uuid = content[0].get("Uuid")
                label = content[0].get("Label")
                version = content[0].get("Version")
                description = content[0].get("Description")
                updated_on = content[0].get("UpdatedOn")

                script = content[0].get("Script")
                field_mapping = content[0].get("FieldMapping")
                headers = content[0].get("Headers")

                # Prepare fields dictionary for checksum calculation
                fields_dict = {
                    "Uuid": uuid,
                    "Label": label,
                    "Version": version,
                    "Description": description,
                    "UpdatedOn": updated_on,
                    "Script": script,
                    "FieldMapping": field_mapping,
                    "Headers": headers
                }

                sha256 = calculate_sha256(file_path, fields_dict)
                # Build URL with the specified base_url
                relative_path = os.path.relpath(file_path, directory).replace(os.sep, "/")
                url = f"{base_url}/{relative_path}"

                # Add to index
                # TODO compute type based on path of file
                index.append({
                    "Name": file_name,
                    "Uuid": uuid,
                    "Label": label,
                    "Version": version,
                    "Description": description,
                    "UpdatedOn": updated_on,
                    "Sha256": sha256,
                    "Url": url,
                    "Type": "DiscoveryPlugin"
                })

    return index


def main():
    input_directory = "./"
    base_url = "https://osintliar.com/"

    # Process files and generate index
    index = process_json_files(input_directory, base_url)

    # Write to index.json
    output_file = os.path.join(input_directory, "index.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=4)

    print(f"Index file created at: {output_file}")


if __name__ == "__main__":
    main()
