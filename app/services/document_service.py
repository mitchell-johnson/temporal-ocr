import os
import logging
from typing import Dict, Any

from app.services.gemini_service import GeminiService
from app.services.azure_service import AzureService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DocumentService:
    """Service for document processing with AI APIs"""

    def __init__(self):
        self.gemini_service = GeminiService()
        self.azure_service = AzureService()
        logger.info("Document Service Initialized")

    async def process_document(self, file_path: str) -> Dict[str, Any]:
        """
        Process a document using AI services.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            Dict containing processing results with keys:
                - markdown_content: str
                - summary: str
                - validation_result: Dict
        """
        logger.info(f"Processing document: {file_path}")
        
        try:
            # Step 1: Get markdown and summary from Gemini
            markdown_content, summary = await self.gemini_service.process_document(file_path)
            
            # Step 2: Validate summary with Azure
            validation_result = await self.azure_service.validate_summary(summary)
            
            # Return combined result
            return {
                "markdown_content": markdown_content,
                "summary": summary,
                "validation_result": validation_result
            }
            
        except Exception as e:
            logger.error(f"Error processing document: {e}", exc_info=True)
            raise 