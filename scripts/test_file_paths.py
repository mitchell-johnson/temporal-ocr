#!/usr/bin/env python
import os
import sys

def check_path(path):
    exists = os.path.exists(path)
    is_file = os.path.isfile(path)
    is_dir = os.path.isdir(path)
    status = f"exists: {exists}, is_file: {is_file}, is_dir: {is_dir}"
    return status

def main():
    # Check important paths
    paths_to_check = [
        "/app/docs/fishinglicence.png",
        "/app/app/uploads",
        "/app/app/activities/gemini_activities.py",
        "/app/app/activities/azure_activities.py",
        "/app/app/models/shared.py",
        "/app/app/workflows/workflows.py",
    ]
    
    print("Checking paths in container...")
    for path in paths_to_check:
        status = check_path(path)
        print(f"{path}: {status}")
    
    print("\nCurrent directory structure:")
    for root, dirs, files in os.walk("/app", topdown=True, followlinks=False):
        level = root.replace("/app", "").count(os.sep)
        indent = " " * 4 * level
        print(f"{indent}{os.path.basename(root)}/")
        sub_indent = " " * 4 * (level + 1)
        for f in files:
            print(f"{sub_indent}{f}")

if __name__ == "__main__":
    main() 