#!/usr/bin/env python3
"""
Cleanup script to remove Temporal-related files and directories
that are no longer needed after migration to direct API calls.
"""

import os
import shutil
from pathlib import Path

# Define the project root directory
ROOT_DIR = Path(__file__).parent.parent.absolute()

# Files and directories to remove
TO_REMOVE = [
    # Workflows and activities
    "app/workflows",
    "app/activities",
    "app/run_worker.py",
    
    # Temporal configuration
    "dynamicconfig",
    
    # Test files related to Temporal
    "tests/workflows",
    "tests/start_worker.py",
    "tests/cleanup_workflows.py",
    
    # Scripts that used Temporal
    "scripts/start_workflow.py",
]

def main():
    """Remove Temporal-related files and directories"""
    print("Cleaning up Temporal-related files...")
    
    for item in TO_REMOVE:
        path = ROOT_DIR / item
        
        if path.exists():
            if path.is_dir():
                print(f"Removing directory: {item}")
                shutil.rmtree(path)
            else:
                print(f"Removing file: {item}")
                path.unlink()
        else:
            print(f"Not found: {item}")
    
    print("\nCleanup complete!")
    print("Note: You may still need to manually update some references in tests or documentation.")

if __name__ == "__main__":
    main() 