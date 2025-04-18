import os
import pytest

# This file contains pytest configuration hooks and fixtures

# Set test environment variables
@pytest.fixture(autouse=True)
def setup_test_env():
    """Setup test environment variables"""
    # Set environment variables for testing
    os.environ["AZURE_DOCUMENT_INTELLIGENCE_KEY"] = "test_key"
    os.environ["AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT"] = "https://test.cognitiveservices.azure.com/"
    os.environ["AZURE_OPENAI_KEY"] = "test_azure_openai_key"
    os.environ["AZURE_OPENAI_ENDPOINT"] = "https://test.openai.azure.com/"
    os.environ["GEMINI_API_KEY"] = "test_gemini_key"
    os.environ["TEMPORAL_HOST"] = "localhost:7233"
    
    yield
    
    # Clean up (if needed)
    # This runs after each test 