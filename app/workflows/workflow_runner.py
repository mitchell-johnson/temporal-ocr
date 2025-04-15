import os
import uuid
import asyncio
from temporalio.client import Client
from temporalio.contrib.pydantic import pydantic_data_converter

# Import the workflow interface and input object
from app.workflows.workflows import DocumentProcessingWorkflow
from app.models.shared import DocumentInput, WorkflowResult

# Configuration for Temporal
TEMPORAL_HOST = os.getenv('TEMPORAL_HOST', 'localhost:7233')
TASK_QUEUE = 'document-processing-queue'

async def start_document_workflow(file_path, use_azure=False) -> WorkflowResult:
    """
    Initiates the document processing workflow with Temporal
    
    Args:
        file_path: Path to the file to process
        use_azure: Whether to use Azure OpenAI (True) or Gemini (False)
        
    Returns:
        WorkflowResult: The result containing OCR text and summary
    """
    # Connect to Temporal server
    client = await Client.connect(
        TEMPORAL_HOST,
        data_converter=pydantic_data_converter, # Use Pydantic data converter
    )

    # Define the input for the workflow
    doc_input = DocumentInput(file_path=file_path)

    # Create a unique workflow ID
    workflow_id = f"doc-processing-{os.path.basename(file_path)}-{uuid.uuid4()}"
    
    # Start the workflow execution
    handle = await client.start_workflow(
        DocumentProcessingWorkflow.run,
        args=[doc_input, use_azure],  # Always use Document Intelligence 
        id=workflow_id,
        task_queue=TASK_QUEUE, # Must match the worker's task queue
    )

    # Wait for the workflow to complete and get the result
    return await handle.result() 