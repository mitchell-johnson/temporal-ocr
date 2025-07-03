# AIDEV-NOTE: Workflow worker that handles AI workflow orchestration
import asyncio
import os
from temporalio.client import Client
from temporalio.worker import Worker
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

# Import all workflows
from app.workflows.ai_example_workflows import (
    AIConsensusWorkflow,
    AIChainWorkflow,
    AISpecialistWorkflow
)

# Configuration
TEMPORAL_HOST = os.getenv('TEMPORAL_HOST', 'localhost:7233')
TASK_QUEUE = 'ai-workflow-queue'

async def main():
    """Run the workflow worker"""
    # Connect to Temporal server
    client = await Client.connect(TEMPORAL_HOST)
    
    # Create and run worker with all workflows
    worker = Worker(
        client,
        task_queue=TASK_QUEUE,
        workflows=[
            AIConsensusWorkflow,
            AIChainWorkflow,
            AISpecialistWorkflow
        ],
    )
    
    print(f"Workflow Worker started, listening on task queue '{TASK_QUEUE}'...")
    print(f"Connected to Temporal at: {TEMPORAL_HOST}")
    print("\nRegistered workflows:")
    print("- ai-consensus-workflow")
    print("- ai-chain-workflow") 
    print("- ai-specialist-workflow")
    await worker.run()

if __name__ == "__main__":
    asyncio.run(main())