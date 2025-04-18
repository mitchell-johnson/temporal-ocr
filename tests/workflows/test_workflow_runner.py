import os
import pytest
import asyncio
from unittest.mock import patch, AsyncMock, MagicMock
from temporalio.client import Client

from app.workflows.workflow_runner import start_document_workflow
from app.models.shared import WorkflowResult


@pytest.mark.asyncio
async def test_start_document_workflow():
    """Test the start_document_workflow function with mocked Temporal client"""
    # Create mock client and handle
    mock_client = AsyncMock(spec=Client)
    mock_handle = AsyncMock()
    
    # Set up the mock result
    mock_result = WorkflowResult(
        ocr_text="Test OCR text",
        summary={"title": "Test Document", "summary": "This is a test summary"}
    )
    mock_handle.result.return_value = mock_result
    mock_client.start_workflow.return_value = mock_handle
    
    # Mock the Client.connect function
    with patch('app.workflows.workflow_runner.Client.connect', return_value=mock_client):
        # Test with Gemini (default)
        result = await start_document_workflow("test_file.pdf")
        
        # Verify client was created with correct parameters
        mock_client.start_workflow.assert_called_once()
        
        # Check the arguments to start_workflow
        args, kwargs = mock_client.start_workflow.call_args
        assert "document-processing-queue" == kwargs["task_queue"]
        assert kwargs["id"].startswith("doc-processing-test_file.pdf")
        
        # Check the workflow input arguments
        workflow_args = kwargs["args"]
        assert len(workflow_args) == 2
        assert "test_file.pdf" == workflow_args[0].file_path
        assert workflow_args[1] is False  # use_azure should be False
        
        # Check the result
        assert result == mock_result
        assert "Test OCR text" == result.ocr_text
        assert "This is a test summary" == result.summary["summary"]
        
        # Reset the mock
        mock_client.reset_mock()
        
        # Test with Azure
        result = await start_document_workflow("test_file.pdf", use_azure=True)
        
        # Check that use_azure is True this time
        workflow_args = mock_client.start_workflow.call_args[1]["args"]
        assert workflow_args[1] is True


@pytest.mark.asyncio
async def test_start_document_workflow_error_handling():
    """Test error handling in start_document_workflow"""
    # Mock Client.connect to raise an exception
    with patch('app.workflows.workflow_runner.Client.connect', side_effect=ConnectionError("Failed to connect")):
        with pytest.raises(ConnectionError):
            await start_document_workflow("test_file.pdf")
    
    # Mock successful connection but workflow execution failure
    mock_client = AsyncMock(spec=Client)
    mock_handle = AsyncMock()
    mock_handle.result.side_effect = ValueError("Workflow execution failed")
    mock_client.start_workflow.return_value = mock_handle
    
    with patch('app.workflows.workflow_runner.Client.connect', return_value=mock_client):
        with pytest.raises(ValueError, match="Workflow execution failed"):
            await start_document_workflow("test_file.pdf") 