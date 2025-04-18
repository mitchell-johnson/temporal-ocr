#!/usr/bin/env python
import os
import sys
import asyncio

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Import the worker setup
from app.run_worker import main

if __name__ == "__main__":
    print("Starting document processing worker...")
    print("Make sure Temporal server is running (e.g., via temporalite start).")
    print("Press Ctrl+C to stop the worker.")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nWorker stopped by user.")
    except Exception as e:
        print(f"Error running worker: {e}")
        import traceback
        traceback.print_exc() 