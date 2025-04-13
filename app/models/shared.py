# shared.py
from pydantic import BaseModel
from temporalio import activity

# Using Pydantic for clearer data structures
class DocumentInput(BaseModel):
    file_path: str # Path to the document file

class OcrActivityResult(BaseModel):
    full_text: str

class SummarizationActivityResult(BaseModel):
    # Both Gemini and Azure OpenAI will return a JSON string, we'll parse it into a dict
    summary_json: dict

class WorkflowResult(BaseModel):
    ocr_text: str
    summary: dict

# Define Gemini Activity interface
class GeminiActivities:
    @activity.defn
    async def perform_ocr(self, doc_input: DocumentInput) -> OcrActivityResult:
        ...

    @activity.defn
    async def perform_summarization(self, ocr_result: OcrActivityResult) -> SummarizationActivityResult:
        ...

# Define Azure OpenAI Activity interface
class AzureOpenAIActivities:
    @activity.defn
    async def perform_azure_ocr(self, doc_input: DocumentInput) -> OcrActivityResult:
        ...

    @activity.defn
    async def perform_azure_summarization(self, ocr_result: OcrActivityResult) -> SummarizationActivityResult:
        ...