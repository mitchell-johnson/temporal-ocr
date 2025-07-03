# AIDEV-NOTE: Dedicated Gemini worker for Temporal workflows
import asyncio
import os
from temporalio.client import Client
from temporalio.worker import Worker
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

# Import Gemini activities
from app.activities.gemini_ai_activities import GeminiActivitiesImpl

# Configuration
TEMPORAL_HOST = os.getenv('TEMPORAL_HOST', 'localhost:7233')
TASK_QUEUE = 'gemini-ai-queue'

async def main():
    """Run the Gemini worker"""
    # Connect to Temporal server
    client = await Client.connect(TEMPORAL_HOST)
    
    # Instantiate Gemini activities
    gemini_activities = GeminiActivitiesImpl()
    
    # Create and run worker
    worker = Worker(
        client,
        task_queue=TASK_QUEUE,
        activities=[gemini_activities.process_request],
    )
    
    print(f"Gemini Worker started, listening on task queue '{TASK_QUEUE}'...")
    print(f"Connected to Temporal at: {TEMPORAL_HOST}")
    await worker.run()

if __name__ == "__main__":
    asyncio.run(main())