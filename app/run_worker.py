import asyncio
import os
from temporalio.client import Client
from temporalio.worker import Worker
from temporalio.contrib.pydantic import pydantic_data_converter
from dotenv import load_dotenv

# Load environment variables from .env file, overriding existing ones
load_dotenv(override=True)

# Import the workflow and activities
from app.workflows.workflows import DocumentProcessingWorkflow
from app.activities.gemini_activities import GeminiActivitiesImpl
from app.activities.azure_activities import AzureOpenAIActivitiesImpl
from app.models.shared import GeminiActivities, AzureOpenAIActivities

# Configuration for Temporal
TEMPORAL_HOST = os.getenv('TEMPORAL_HOST', 'localhost:7233')
TASK_QUEUE = 'document-processing-queue'

async def main():
    # Connect to Temporal server
    client = await Client.connect(
        TEMPORAL_HOST,
        data_converter=pydantic_data_converter, # Use Pydantic data converter
    )

    # Instantiate activity implementations
    gemini_activities = GeminiActivitiesImpl()
    azure_activities = AzureOpenAIActivitiesImpl()

    # Run the worker with both sets of activities
    worker = Worker(
        client,
        task_queue=TASK_QUEUE,
        workflows=[DocumentProcessingWorkflow],
        activities=[
            # Gemini activities
            gemini_activities.perform_ocr,
            gemini_activities.perform_summarization,
            # Azure OpenAI activities
            azure_activities.perform_azure_ocr,
            azure_activities.perform_azure_summarization,
        ],
    )
    print(f"Worker started, listening on task queue '{TASK_QUEUE}'...")
    await worker.run()

if __name__ == "__main__":
    asyncio.run(main()) 