#!/usr/bin/env python
import os
import sys
import pytest

def main():
    """Run all tests or specific test modules if provided"""
    # Add the project root to the Python path
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, project_root)
    
    # Default arguments
    args = [
        "-v",  # verbose output
        "--asyncio-mode=auto",  # Auto-detect asyncio mode
    ]
    
    # Add any command-line arguments
    args.extend(sys.argv[1:] or ["tests/"])
    
    # Run pytest
    exit_code = pytest.main(args)
    sys.exit(exit_code)

if __name__ == "__main__":
    main() 