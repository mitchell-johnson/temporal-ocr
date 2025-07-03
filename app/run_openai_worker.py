# AIDEV-NOTE: Dedicated OpenAI worker for Temporal workflows
import asyncio
import os
from temporalio.client import Client
from temporalio.worker import Worker
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

# Import OpenAI activities
from app.activities.openai_activities import OpenAIActivitiesImpl

# Configuration
TEMPORAL_HOST = os.getenv('TEMPORAL_HOST', 'localhost:7233')
TASK_QUEUE = 'openai-ai-queue'

async def main():
    """Run the OpenAI worker"""
    # Connect to Temporal server
    client = await Client.connect(TEMPORAL_HOST)
    
    # Instantiate OpenAI activities
    openai_activities = OpenAIActivitiesImpl()
    
    # Create and run worker
    worker = Worker(
        client,
        task_queue=TASK_QUEUE,
        activities=[openai_activities.process_request],
    )
    
    print(f"OpenAI Worker started, listening on task queue '{TASK_QUEUE}'...")
    print(f"Connected to Temporal at: {TEMPORAL_HOST}")
    await worker.run()

if __name__ == "__main__":
    asyncio.run(main())