#!/usr/bin/env python
import asyncio
import os
import sys
from dotenv import load_dotenv

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Import temporalio client
from temporalio.client import Client

# Load environment variables from .env file
load_dotenv()

# Configuration for Temporal
TEMPORAL_HOST = os.getenv('TEMPORAL_HOST', 'localhost:7233')

async def cleanup_workflows():
    """Clean up any running workflows in Temporal"""
    print(f"Connecting to Temporal at {TEMPORAL_HOST}...")
    
    try:
        # Connect to Temporal server
        client = await Client.connect(TEMPORAL_HOST)
        
        # Get list of workflows
        print("Listing workflows...")
        handles = []
        
        async for workflow in client.list_workflows():
            if "doc-processing" in workflow.id:
                print(f"Found workflow: {workflow.id}")
                handle = client.get_workflow_handle(workflow.id)
                handles.append(handle)
        
        # Terminate all found workflows
        print(f"Found {len(handles)} workflows to terminate.")
        for handle in handles:
            try:
                print(f"Terminating workflow: {handle.id}")
                await handle.terminate("Cleaning up for new implementation")
                print(f"Successfully terminated workflow: {handle.id}")
            except Exception as e:
                print(f"Error terminating workflow {handle.id}: {e}")
        
        print("Cleanup complete.")
        
    except Exception as e:
        print(f"Error during workflow cleanup: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(cleanup_workflows()) 