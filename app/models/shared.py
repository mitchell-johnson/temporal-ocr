# shared.py
from pydantic import BaseModel
from temporalio import activity
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

class WorkflowResult(BaseModel):
    markdown_content: str
    summary: str
    validation_result: AzureValidationResult

# Define Gemini Activity interface
class GeminiActivities:
    @activity.defn
    async def generate_markdown_and_summary(self, doc_input: DocumentInput) -> GeminiDocumentResult:
        """
        Generate markdown representation and a summary of the document using Gemini
        """
        ...

# Define Azure OpenAI Activity interface
class AzureOpenAIActivities:
    @activity.defn
    async def validate_summary(self, doc_input: DocumentInput, summary: str) -> AzureValidationResult:
        """
        Validate if the summary accurately represents the document and suggest improvements
        """
        ...