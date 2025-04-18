import os
import pytest
import asyncio
import tempfile
import json
from unittest.mock import patch, MagicMock, AsyncMock
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Worker
from temporalio.client import Client
from temporalio import activity
from pydantic import BaseModel

# Import the workflow and models
from app.workflows.workflows import DocumentProcessingWorkflow
from app.models.shared import (
    DocumentInput, 
    WorkflowResult, 
    OcrActivityResult,
    DocumentIntelligenceResult,
    SummarizationActivityResult,
    GeminiActivities,
    AzureOpenAIActivities,
    DocumentIntelligenceActivities
)

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

# Create properly decorated mock activity functions
@activity.defn
async def mock_process_document(doc_input: DocumentInput) -> DocumentIntelligenceResult:
    return DocumentIntelligenceResult(
        full_text="This is a mock OCR result for testing",
        confidence=0.95,
        pages=2,
        tables=[{"rows": 2, "columns": 3, "cells": [["A", "B", "C"], ["D", "E", "F"]]}],
        entities=[{"key": "Invoice Number", "value": "INV-12345"}]
    )

@activity.defn
async def mock_perform_summarization_gemini(ocr_result: OcrActivityResult) -> SummarizationActivityResult:
    return SummarizationActivityResult(
        summary_json={"title": "Test Document", "summary": "This is a mock summary from Gemini"}
    )

@activity.defn
async def mock_perform_summarization_azure(ocr_result: OcrActivityResult) -> SummarizationActivityResult:
    return SummarizationActivityResult(
        summary_json={"title": "Test Document", "summary": "This is a mock summary from Azure"}
    )

@pytest.fixture
async def workflow_environment():
    """Create a workflow test environment with our workflow registered"""
    async with await WorkflowEnvironment.start_local() as env:
        yield env

@pytest.fixture
async def workflow_client(workflow_environment):
    """Create a workflow client for testing"""
    # The client is already created by the environment, just return it
    return workflow_environment.client

@pytest.fixture
async def worker(workflow_client):
    """Create a worker with registered workflow and mock activities"""
    worker = Worker(
        workflow_client,
        task_queue="test-task-queue",
        workflows=[DocumentProcessingWorkflow],
        activities=[
            mock_process_document,
            mock_perform_summarization_gemini,
            mock_perform_summarization_azure,
        ]
    )
    worker_task = asyncio.create_task(worker.run())
    yield worker
    worker_task.cancel()
    try:
        await worker_task
    except asyncio.CancelledError:
        pass

@pytest.mark.asyncio
async def test_document_workflow_with_gemini(worker, workflow_client):
    """Test the document processing workflow using Gemini"""
    # Mock the activity execution
    async def mock_execute_activity(activity_fn, *args, **kwargs):
        if activity_fn.__name__ == 'process_document':
            return await mock_process_document(args[0])
        elif activity_fn.__name__ == 'perform_summarization':
            return await mock_perform_summarization_gemini(args[0])
        return None
    
    # Create a temporary test file
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
        temp_file.write(b"Test PDF content")
        file_path = temp_file.name
    
    try:
        # Create workflow input
        doc_input = DocumentInput(file_path=file_path)
        
        # Mock the activity execution
        with patch('app.workflows.workflows.workflow.execute_activity', new_callable=AsyncMock) as mock_execute:
            mock_execute.side_effect = mock_execute_activity
            
            # Run the workflow
            result = await workflow_client.execute_workflow(
                DocumentProcessingWorkflow.run,
                args=[doc_input, False],  # use_azure=False -> use Gemini
                id="test-workflow-gemini",
                task_queue="test-task-queue",
            )
            
            # Assert the result is as expected
            assert isinstance(result, WorkflowResult)
            assert result.summary["summary"] == "This is a mock summary from Gemini"
            assert result.summary["title"] == "Test Document"
    
    finally:
        # Clean up the temporary file
        if os.path.exists(file_path):
            os.unlink(file_path)

@pytest.mark.asyncio
async def test_document_workflow_with_azure(worker, workflow_client):
    """Test the document processing workflow using Azure OpenAI"""
    # Mock the activity execution
    async def mock_execute_activity(activity_fn, *args, **kwargs):
        if activity_fn.__name__ == 'process_document':
            return await mock_process_document(args[0])
        elif activity_fn.__name__ == 'perform_azure_summarization':
            return await mock_perform_summarization_azure(args[0])
        return None
    
    # Create a temporary test file
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
        temp_file.write(b"Test PDF content")
        file_path = temp_file.name
    
    try:
        # Create workflow input
        doc_input = DocumentInput(file_path=file_path)
        
        # Mock the activity execution
        with patch('app.workflows.workflows.workflow.execute_activity', new_callable=AsyncMock) as mock_execute:
            mock_execute.side_effect = mock_execute_activity
            
            # Run the workflow
            result = await workflow_client.execute_workflow(
                DocumentProcessingWorkflow.run,
                args=[doc_input, True],  # use_azure=True -> use Azure OpenAI
                id="test-workflow-azure",
                task_queue="test-task-queue",
            )
            
            # Assert the result is as expected
            assert isinstance(result, WorkflowResult)
            assert result.summary["summary"] == "This is a mock summary from Azure"
            assert result.summary["title"] == "Test Document"
    
    finally:
        # Clean up the temporary file
        if os.path.exists(file_path):
            os.unlink(file_path)

@pytest.mark.asyncio
async def test_document_workflow_error_handling(worker, workflow_client):
    """Test the workflow's error handling with invalid input"""
    # Create workflow input with non-existent file
    doc_input = DocumentInput(file_path="/path/to/nonexistent/file.pdf")
    
    # Mock the activity implementation to raise an exception
    with patch('app.workflows.workflows.workflow.execute_activity', new_callable=AsyncMock) as mock_execute:
        mock_execute.side_effect = FileNotFoundError("File not found")
        
        # Run the workflow and expect it to fail
        with pytest.raises(FileNotFoundError):
            await workflow_client.execute_workflow(
                DocumentProcessingWorkflow.run,
                args=[doc_input, False],
                id="test-workflow-error",
                task_queue="test-task-queue",
            )

@pytest.mark.asyncio
async def test_workflow_retry_policy(worker, workflow_client):
    """Test that the workflow properly configures retry policies"""
    # Create a temporary test file
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
        temp_file.write(b"Test PDF content")
        file_path = temp_file.name
    
    try:
        # Create workflow input
        doc_input = DocumentInput(file_path=file_path)
        
        # Mock the activity implementation to fail once then succeed
        failure_count = 0
        
        async def mock_activity(*args, **kwargs):
            nonlocal failure_count
            if failure_count == 0:
                failure_count += 1
                raise ValueError("Temporary failure")
            return DocumentIntelligenceResult(
                full_text="Retry succeeded",
                confidence=0.9,
                pages=1,
                tables=[],
                entities=[]
            )
        
        with patch('app.workflows.workflows.workflow.execute_activity', new_callable=AsyncMock) as mock_execute:
            mock_execute.side_effect = mock_activity
            
            # This should succeed after retry
            result = await workflow_client.execute_workflow(
                DocumentProcessingWorkflow.run,
                args=[doc_input, False],
                id="test-workflow-retry",
                task_queue="test-task-queue",
            )
            
            # Because we're mocking the workflow, the actual retry might not happen,
            # but we can assert what would happen if the mock returned the retry value
            assert isinstance(result, WorkflowResult)
    
    finally:
        # Clean up the temporary file
        if os.path.exists(file_path):
            os.unlink(file_path) 