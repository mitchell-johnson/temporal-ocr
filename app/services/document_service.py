import os
import logging
from typing import Dict, Any, Literal

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

    async def process_document(self, file_path: str, provider: Literal["gemini", "azure"] = None) -> Dict[str, Any]:
        """
        Process a document using AI services.
        
        Args:
            file_path: Path to the document file
            provider: AI provider to use for document processing ("gemini" or "azure")
                     If None, will use the default provider (Gemini)
            
        Returns:
            Dict containing processing results with keys:
                - markdown_content: str
                - summary: str
                - validation_result: Dict
        """
        logger.info(f"Processing document: {file_path}")
        
        # Determine which provider to use
        if provider is None:
            # Default to Gemini
            provider = "gemini"
        
        try:
            # Step 1: Get markdown and summary from the selected provider
            logger.info(f"Using {provider} for document processing")
            
            if provider == "azure":
                markdown_content, summary = await self.azure_service.process_document(file_path)
            else:  # default to gemini
                markdown_content, summary = await self.gemini_service.process_document(file_path)
            
            # Step 2: Validate summary with Azure
            validation_result = await self.azure_service.validate_summary(summary)
            
            # Return combined result
            return {
                "markdown_content": markdown_content,
                "summary": summary,
                "validation_result": validation_result,
                "provider_used": provider
            }
            
        except Exception as e:
            logger.error(f"Error processing document: {e}", exc_info=True)
            raise 