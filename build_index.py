"""
Builds the index.json from the OSINT LIAR discovery plugins included in this directory.
"""
import datetime
import os
import json
import hashlib
from pathlib import Path


def calculate_sha256(fields_dict) -> str:
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
    files = list(Path(directory).rglob("*.json"))
    for file in files:
        if file.name == 'index.json':
            continue

        # Load JSON content
        with open(file, "r", encoding="utf-8") as f:
            try:
                content = json.load(f)
            except json.JSONDecodeError:
                print(f"Skipping invalid JSON file: {file}")
                continue

        # Extract required fields for use in the checksum and the package index
        file_name = Path(file).stem
        uuid = content.get("uuid")
        label = content.get("label")
        version = content.get("version")
        description = content.get("description")
        country = content.get("country", "us")
        script = content.get("script")
        field_mapping = content.get("fieldMapping", dict())
        headers = content.get("headers", dict())

        # Prepare fields dictionary for checksum calculation
        fields_dict = {
            "uuid": uuid,
            "label": label,
            "version": version,
            "description": description,
            "script": script,
            "fieldMapping": field_mapping,
            "headers": headers,
            "country": country,
        }

        sha256 = calculate_sha256(fields_dict)
        # Build URL with the specified base_url
        relative_path = os.path.relpath(file, directory).replace(os.sep, "/")
        url = f"{base_url}/{relative_path}"

        # Add to index
        # TODO compute type based on path of file
        index.append({
            "name": file_name,
            "uuid": uuid,
            "label": label,
            "version": version,
            "description": description,
            "updatedOn": datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            "sha256": sha256,
            "url": url,
            "type": "DiscoveryPlugin",
            "country": country
        })
    return index



def main():
    input_directory = "./"
    base_url = "https://raw.githubusercontent.com/osint-liar/public-packages/develop"

    # Process files and generate index
    index = process_json_files(input_directory, base_url)

    # Write to index.json
    output_file = os.path.join(input_directory, "index.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=4)

    print(f"Index file created at: {output_file}")

if __name__ == "__main__":
    main()
