import os
import json
import config

def ensure_directory_exists(directory_path):
    """Ensure that a directory exists, create it if it doesn't"""
    os.makedirs(directory_path, exist_ok=True)
    return directory_path

def save_json_to_file(data, file_path):
    """Save JSON data to a file, ensuring the directory exists"""
    try:
        # Make sure the directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Write the data to the file
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        
        return True
    except Exception as e:
        print(f"[ERROR] Failed to save JSON to {file_path}: {str(e)}")
        return False

def load_json_from_file(file_path):
    """Load JSON data from a file, returning None if file doesn't exist or is invalid"""
    try:
        if not os.path.exists(file_path):
            print(f"[WARNING] File does not exist: {file_path}")
            return None
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return data
    except Exception as e:
        print(f"[ERROR] Failed to load JSON from {file_path}: {str(e)}")
        return None

def save_text_to_file(text, file_path):
    """Save text data to a file"""
    ensure_directory_exists(os.path.dirname(file_path))
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(text)
    return file_path

def load_text_from_file(file_path):
    """Load text data from a file"""
    if not os.path.exists(file_path):
        return None
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()
