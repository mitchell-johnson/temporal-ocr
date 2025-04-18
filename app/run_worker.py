import asyncio
import os
import inspect
from temporalio.client import Client
from temporalio.worker import Worker
import json
from pydantic import BaseModel
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

# Define a custom data converter for Pydantic objects
class PydanticDataConverter:
    @staticmethod
    def to_payload(value: any) -> bytes:
        if isinstance(value, BaseModel):
            return json.dumps(value.dict()).encode('utf-8')
        return json.dumps(value).encode('utf-8')
    
    @staticmethod
    def from_payload(payload_bytes: bytes, type_hint: type) -> any:
        data = json.loads(payload_bytes.decode('utf-8'))
        if issubclass(type_hint, BaseModel):
            return type_hint.parse_obj(data)
        return data

async def main():
    # Connect to Temporal server
    client = await Client.connect(TEMPORAL_HOST)

    # Instantiate activity implementations
    gemini_activities = GeminiActivitiesImpl()
    azure_activities = AzureOpenAIActivitiesImpl()

    # Print out information about the class and method
    print("\nGemini Activities Implementation:")
    print(f"Class: {gemini_activities.__class__.__name__}")
    print(f"Method: {gemini_activities.generate_markdown_and_summary.__name__}")
    print(f"Is method: {inspect.ismethod(gemini_activities.generate_markdown_and_summary)}")
    print(f"Is function: {inspect.isfunction(gemini_activities.generate_markdown_and_summary)}")
    
    print("\nAzure Activities Implementation:")
    print(f"Class: {azure_activities.__class__.__name__}")
    print(f"Method: {azure_activities.validate_summary.__name__}")
    print(f"Is method: {inspect.ismethod(azure_activities.validate_summary)}")
    print(f"Is function: {inspect.isfunction(azure_activities.validate_summary)}")

    print("\nActivity Names:")
    print(f"Gemini activity name: {getattr(gemini_activities.generate_markdown_and_summary, '__name__', 'unknown')}")
    print(f"Azure activity name: {getattr(azure_activities.validate_summary, '__name__', 'unknown')}")

    # List all methods in the implementation classes
    print("\nAll Gemini Activities:")
    for name, method in inspect.getmembers(gemini_activities, predicate=inspect.ismethod):
        if not name.startswith('_'):
            print(f" - {name}")
    
    print("\nAll Azure Activities:")
    for name, method in inspect.getmembers(azure_activities, predicate=inspect.ismethod):
        if not name.startswith('_'):
            print(f" - {name}")

    # Run the worker with both sets of activities
    activities_to_register = [
        # Gemini activities
        gemini_activities.generate_markdown_and_summary,
        # Azure OpenAI activities
        azure_activities.validate_summary,
    ]
    
    # Print information about registered activities
    print("\nRegistering the following activities:")
    for activity in activities_to_register:
        print(f" - {getattr(activity, '__name__', str(activity))}")
    
    worker = Worker(
        client,
        task_queue=TASK_QUEUE,
        workflows=[DocumentProcessingWorkflow],
        activities=activities_to_register,
    )
    
    print(f"\nWorker started, listening on task queue '{TASK_QUEUE}'...")
    await worker.run()

if __name__ == "__main__":
    asyncio.run(main()) 