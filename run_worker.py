# run_worker.py
import asyncio
from temporalio.client import Client
from temporalio.worker import Worker
from temporalio.contrib.pydantic import pydantic_data_converter
from dotenv import load_dotenv

# Load environment variables from .env file, overriding existing ones
load_dotenv(override=True)

# Import the workflow and activities
from workflows import DocumentProcessingWorkflow
from gemini_activities import GeminiActivitiesImpl
from azure_activities import AzureOpenAIActivitiesImpl
from shared import GeminiActivities, AzureOpenAIActivities

async def main():
    # Connect to Temporal server (defaults to localhost:7233)
    client = await Client.connect(
        "localhost:7233",
        data_converter=pydantic_data_converter, # Use Pydantic data converter
    )

    # Instantiate activity implementations
    gemini_activities = GeminiActivitiesImpl()
    azure_activities = AzureOpenAIActivitiesImpl()

    # Run the worker with both sets of activities
    worker = Worker(
        client,
        task_queue="document-processing-queue", # Name your task queue
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
    print("Worker started, listening on task queue 'document-processing-queue'...")
    await worker.run()

if __name__ == "__main__":
    asyncio.run(main())