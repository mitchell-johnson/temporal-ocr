import os
import pytest
import tempfile
from unittest.mock import patch, MagicMock

from app.activities.document_intelligence_activities import DocumentIntelligenceActivitiesImpl
from app.models.shared import DocumentInput, DocumentIntelligenceResult


@pytest.fixture
def setup_document_intelligence():
    """Set up test environment for document intelligence activities"""
    # Create a temp directory for test files
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a test PDF file
        pdf_path = os.path.join(temp_dir, "test.pdf")
        with open(pdf_path, "wb") as f:
            f.write(b"%PDF-1.7\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R >>\nendobj\n4 0 obj\n<< /Length 44 >>\nstream\nBT\n/F1 12 Tf\n100 700 Td\n(Test PDF) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f\n0000000010 00000 n\n0000000059 00000 n\n0000000118 00000 n\n0000000217 00000 n\ntrailer\n<< /Size 5 /Root 1 0 R >>\nstartxref\n307\n%%EOF")
            
        yield pdf_path


@patch('app.activities.document_intelligence_activities.DocumentIntelligenceClient')
def test_document_intelligence_init(mock_client_class):
    """Test initialization of document intelligence activities"""
    # Set up environment variables
    with patch.dict(os.environ, {
        "AZURE_DOCUMENT_INTELLIGENCE_KEY": "test_key",
        "AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT": "https://test.example.com/"
    }):
        activities = DocumentIntelligenceActivitiesImpl()
        
        # Verify client was created with correct parameters
        mock_client_class.assert_called_once()
        args, kwargs = mock_client_class.call_args
        assert "https://test.example.com/" == kwargs["endpoint"]
        assert "test_key" == kwargs["credential"].key


@patch('app.activities.document_intelligence_activities.DocumentIntelligenceClient')
@pytest.mark.asyncio
async def test_process_document(mock_client_class, setup_document_intelligence):
    """Test processing a document"""
    # Get the test PDF path
    pdf_path = setup_document_intelligence
    
    # Create a mock result
    mock_poller = MagicMock()
    mock_result = MagicMock()
    mock_result.content = "This is a test document."
    
    # Mock pages with lines
    mock_page = MagicMock()
    mock_line = MagicMock()
    mock_line.appearance.confidence = 0.95
    mock_page.lines = [mock_line]
    mock_result.pages = [mock_page]
    
    # Mock table
    mock_table = MagicMock()
    mock_table.row_count = 2
    mock_table.column_count = 3
    mock_cell = MagicMock()
    mock_cell.content = "Cell content"
    mock_table.cells = [[mock_cell, mock_cell, mock_cell], [mock_cell, mock_cell, mock_cell]]
    mock_result.tables = [mock_table]
    
    # Mock key-value pairs
    mock_kvp = MagicMock()
    mock_kvp.key = MagicMock()
    mock_kvp.key.content = "Invoice Number"
    mock_kvp.value = MagicMock()
    mock_kvp.value.content = "INV-12345"
    mock_result.key_value_pairs = [mock_kvp]
    
    # Set up the mock poller
    mock_poller.result.return_value = mock_result
    
    # Set up the mock client
    mock_client = MagicMock()
    mock_client.begin_analyze_document.return_value = mock_poller
    mock_client_class.return_value = mock_client
    
    # Set up environment variables
    with patch.dict(os.environ, {
        "AZURE_DOCUMENT_INTELLIGENCE_KEY": "test_key",
        "AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT": "https://test.example.com/"
    }):
        # Create activities implementation
        activities = DocumentIntelligenceActivitiesImpl()
        
        # Process document
        doc_input = DocumentInput(file_path=pdf_path)
        result = await activities.process_document(doc_input)
        
        # Verify result
        assert isinstance(result, DocumentIntelligenceResult)
        assert "This is a test document." == result.full_text
        assert 0.95 == result.confidence
        assert 1 == result.pages
        assert 1 == len(result.tables)
        assert 2 == result.tables[0]["rows"]
        assert 3 == result.tables[0]["columns"]
        assert 1 == len(result.entities)
        assert "Invoice Number" == result.entities[0]["key"]
        assert "INV-12345" == result.entities[0]["value"]


@patch('app.activities.document_intelligence_activities.DocumentIntelligenceClient')
@pytest.mark.asyncio
async def test_process_document_file_not_found(mock_client_class):
    """Test processing a non-existent document"""
    # Set up environment variables
    with patch.dict(os.environ, {
        "AZURE_DOCUMENT_INTELLIGENCE_KEY": "test_key",
        "AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT": "https://test.example.com/"
    }):
        # Create activities implementation
        activities = DocumentIntelligenceActivitiesImpl()
        
        # Process non-existent document
        doc_input = DocumentInput(file_path="/non/existent/file.pdf")
        with pytest.raises(FileNotFoundError):
            await activities.process_document(doc_input)


def test_missing_environment_variables():
    """Test initialization with missing environment variables"""
    # Set up environment with missing variables
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ValueError, match="Azure Document Intelligence configuration missing"):
            DocumentIntelligenceActivitiesImpl() 