import os
import uuid
import asyncio
from temporalio.client import Client
import json
from pydantic import BaseModel

# Import the workflow interface and input object
from app.workflows.workflows import DocumentProcessingWorkflow
from app.models.shared import DocumentInput, WorkflowResult

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

async def start_document_workflow(file_path, client=None, workflow_id=None) -> WorkflowResult:
    """
    Initiates the document processing workflow with Temporal
    
    Args:
        file_path: Path to the file to process
        client: Optional pre-existing temporal client (for testing)
        workflow_id: Optional workflow ID (for testing)
        
    Returns:
        WorkflowResult: The result containing markdown, summary, and validation
    """
    # Connect to Temporal server if client is not provided
    if client is None:
        # Use default JSON-based converter instead of pydantic_data_converter
        client = await Client.connect(TEMPORAL_HOST)

    # Define the input for the workflow
    doc_input = DocumentInput(file_path=file_path)

    # Create a unique workflow ID if not provided
    if workflow_id is None:
        workflow_id = f"doc-processing-{os.path.basename(file_path)}-{uuid.uuid4()}"
    
    # Start the workflow execution
    handle = await client.start_workflow(
        DocumentProcessingWorkflow.run,
        args=[doc_input],
        id=workflow_id,
        task_queue=TASK_QUEUE, # Must match the worker's task queue
    )

    # Wait for the workflow to complete and get the result
    return await handle.result() 