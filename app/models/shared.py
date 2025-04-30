# shared.py
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

# Using Pydantic for clearer data structures
class DocumentInput(BaseModel):
    file_path: str # Path to the document file

class GeminiDocumentResult(BaseModel):
    markdown_content: str
    summary: str

class AzureValidationResult(BaseModel):
    is_accurate: bool
    suggested_improvements: List[str]
    improved_summary: Optional[str] = None

class DocumentProcessingResult(BaseModel):
    markdown_content: str
    summary: str
    validation_result: AzureValidationResult