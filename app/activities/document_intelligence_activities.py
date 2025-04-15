# document_intelligence_activities.py
import os
import logging
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from temporalio import activity

# Import shared objects
from app.models.shared import DocumentInput, DocumentIntelligenceResult, DocumentIntelligenceActivities

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DocumentIntelligenceActivitiesImpl(DocumentIntelligenceActivities):
    def __init__(self):
        # Configure Document Intelligence Client
        api_key = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_KEY")
        endpoint = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT")
        
        if not all([api_key, endpoint]):
            raise ValueError("Azure Document Intelligence configuration missing. Please set AZURE_DOCUMENT_INTELLIGENCE_KEY and AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT environment variables.")
        
        # Initialize the synchronous client (more reliable than async in this case)
        self.client = DocumentIntelligenceClient(
            endpoint=endpoint,
            credential=AzureKeyCredential(api_key)
        )
        
        # Log configuration details (with sensitive info masked)
        logger.info(f"Azure Document Intelligence Endpoint: {endpoint}")
        logger.info(f"Azure Document Intelligence Key: {'*' * 8}{api_key[-4:]}")  # Only show last 4 chars
        
        logger.info("Document Intelligence Activities Initialized.")
    
    @activity.defn
    async def process_document(self, doc_input: DocumentInput) -> DocumentIntelligenceResult:
        """
        Processes a document with Azure Document Intelligence (Read model)
        """
        activity.logger.info(f"Starting Document Intelligence processing for file: {doc_input.file_path}")
        
        try:
            # Read the document file
            with open(doc_input.file_path, "rb") as f:
                document_bytes = f.read()
            
            # Call the Read model (general document)
            activity.logger.info("Sending document to Azure Document Intelligence...")
            
            # Use synchronous begin_analyze_document for reliability
            poller = self.client.begin_analyze_document(
                "prebuilt-read",  # Using the prebuilt read model
                document_bytes
            )
            
            # Wait for the operation to complete
            result = poller.result()
            
            # Extract text
            full_text = result.content if result.content else ""
            
            # Calculate average confidence
            confidences = []
            if hasattr(result, "pages"):
                for page in result.pages:
                    if hasattr(page, "lines"):
                        for line in page.lines:
                            if hasattr(line, "appearance") and hasattr(line.appearance, "confidence"):
                                confidences.append(line.appearance.confidence)
            
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            # Extract any tables if present
            tables = []
            if hasattr(result, "tables") and result.tables:
                for table in result.tables:
                    table_data = {
                        "rows": table.row_count,
                        "columns": table.column_count,
                        "cells": [[cell.content for cell in row] for row in table.cells] if hasattr(table, "cells") else []
                    }
                    tables.append(table_data)
            
            # Get key-value pairs if any (treating as entities)
            entities = []
            if hasattr(result, "key_value_pairs") and result.key_value_pairs:
                for kvp in result.key_value_pairs:
                    if kvp.key and kvp.value:
                        entities.append({
                            "key": kvp.key.content,
                            "value": kvp.value.content
                        })
            
            # Get page count
            page_count = len(result.pages) if hasattr(result, "pages") else 0
            
            activity.logger.info(f"Document Intelligence completed. Extracted {len(full_text)} characters from {page_count} pages.")
            
            return DocumentIntelligenceResult(
                full_text=full_text,
                confidence=avg_confidence,
                pages=page_count,
                tables=tables,
                entities=entities
            )
                
        except FileNotFoundError:
            activity.logger.error(f"File not found: {doc_input.file_path}")
            raise
        except Exception as e:
            activity.logger.error(f"Error during Document Intelligence processing: {e}", exc_info=True)
            raise 