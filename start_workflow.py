# start_workflow.py
import asyncio
import os
import uuid
from temporalio.client import Client
from temporalio.contrib.pydantic import pydantic_data_converter
from dotenv import load_dotenv

# Load environment variables from .env file, overriding existing ones
load_dotenv(override=True)

# Import the workflow interface and input object
from workflows import DocumentProcessingWorkflow
from shared import DocumentInput

async def main(use_azure: bool = False):
    # Connect to Temporal server
    client = await Client.connect(
        "localhost:7233",
        data_converter=pydantic_data_converter, # Use Pydantic data converter
    )

    # Define the input for the workflow
    pdf_file_to_process = "fishinglicence.png"
    doc_input = DocumentInput(file_path=pdf_file_to_process)

    # Start the workflow execution
    print(f"Starting DocumentProcessingWorkflow for {pdf_file_to_process} using {'Azure OpenAI' if use_azure else 'Gemini'}...")
    handle = await client.start_workflow(
        DocumentProcessingWorkflow.run,
        args=[doc_input, use_azure],  # Pass arguments as a list
        id=f"doc-processing-{os.path.basename(pdf_file_to_process)}-{uuid.uuid4()}", # Unique workflow ID
        task_queue="document-processing-queue", # Must match the worker's task queue
    )

    print(f"Workflow started with ID: {handle.id}")

    # Wait for the workflow to complete and get the result
    print("Waiting for workflow to complete...")
    result = await handle.result()

    print("\n--- Workflow Result ---")
    print(f"OCR Text Length: {len(result.ocr_text)}")
    # Limit printing very long OCR text
    print(f"OCR Text (first 500 chars): {result.ocr_text[:500]}...")
    print("\nSummary JSON:")
    import json
    print(json.dumps(result.summary, indent=2))
    print("----------------------")

if __name__ == "__main__":
    import argparse
    
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Start a document processing workflow')
    parser.add_argument('--azure', action='store_true', help='Use Azure OpenAI instead of Gemini')
    args = parser.parse_args()
    
    asyncio.run(main(args.azure))