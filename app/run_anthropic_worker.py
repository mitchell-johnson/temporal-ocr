# AIDEV-NOTE: Dedicated Anthropic worker for Temporal workflows
import asyncio
import os
from temporalio.client import Client
from temporalio.worker import Worker
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

# Import Anthropic activities
from app.activities.anthropic_activities import AnthropicActivitiesImpl

# Configuration
TEMPORAL_HOST = os.getenv('TEMPORAL_HOST', 'localhost:7233')
TASK_QUEUE = 'anthropic-ai-queue'

async def main():
    """Run the Anthropic worker"""
    # Connect to Temporal server
    client = await Client.connect(TEMPORAL_HOST)
    
    # Instantiate Anthropic activities
    anthropic_activities = AnthropicActivitiesImpl()
    
    # Create and run worker
    worker = Worker(
        client,
        task_queue=TASK_QUEUE,
        activities=[anthropic_activities.process_request],
    )
    
    print(f"Anthropic Worker started, listening on task queue '{TASK_QUEUE}'...")
    print(f"Connected to Temporal at: {TEMPORAL_HOST}")
    await worker.run()

if __name__ == "__main__":
    asyncio.run(main())