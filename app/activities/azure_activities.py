# azure_activities.py
import os
import base64
import json
import logging
import mimetypes
from openai import AsyncAzureOpenAI
from temporalio import activity
from pydantic import BaseModel, Field

# Import shared objects
from app.models.shared import DocumentInput, OcrActivityResult, SummarizationActivityResult, AzureOpenAIActivities

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Pydantic Model for Expected JSON Summary ---
class SummarySchema(BaseModel):
    summary: str = Field(description="A concise summary of the provided text.")
    keywords: list[str] = Field(description="A list of 3-5 main keywords from the text.", default_factory=list)

# --- Activity Implementation ---
class AzureOpenAIActivitiesImpl(AzureOpenAIActivities):

    def __init__(self):
        # Configure Azure OpenAI Client
        api_key = os.getenv("AZURE_OPENAI_API_KEY")
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        model_name = os.getenv("AZURE_OPENAI_MODEL_NAME")
        
        if not all([api_key, endpoint, model_name]):
            raise ValueError("Azure OpenAI configuration missing. Please set AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, and AZURE_OPENAI_MODEL_NAME environment variables.")
        
        self.client = AsyncAzureOpenAI(
            api_key=api_key,
            api_version="2024-02-15-preview",  # Latest version supporting vision
            azure_endpoint=endpoint
        )
        # Log configuration details (with sensitive info masked)
        logger.info(f"Azure OpenAI Endpoint: {endpoint}")
        logger.info(f"Azure OpenAI Model: {model_name}")
        logger.info(f"Azure OpenAI API Key: {'*' * 8}{api_key[-4:]}")  # Only show last 4 chars
        
        self.model_name = model_name
        logger.info("Azure OpenAI Activities Initialized.")

    @activity.defn
    async def perform_azure_ocr(self, doc_input: DocumentInput) -> OcrActivityResult:
        """
        Reads an image file, sends it to Azure OpenAI for text extraction.
        """
        activity.logger.info(f"Starting Azure OpenAI OCR for file: {doc_input.file_path}")

        try:
            # Read the image file bytes
            with open(doc_input.file_path, "rb") as f:
                image_bytes = f.read()

            # Convert image to base64
            base64_image = base64.b64encode(image_bytes).decode('utf-8')

            # Determine the file type and set appropriate mime type
            mime_type, _ = mimetypes.guess_type(doc_input.file_path)
            if not mime_type:
                mime_type = 'image/jpeg'  # default to jpeg if unknown

            # Prepare the request for Azure OpenAI
            prompt = """
            Extract all text content from this image. 
            Preserve the exact formatting, spacing, and structure of the text as it appears in the image.
            Include all numbers, punctuation, and special characters exactly as they appear.
            """

            # Call Azure OpenAI API
            activity.logger.info("Sending request to Azure OpenAI for OCR...")
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{mime_type};base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_completion_tokens=4096
            )

            # Extract text from response
            if not response.choices or not response.choices[0].message.content:
                activity.logger.warning("Azure OpenAI OCR response was empty.")
                return OcrActivityResult(full_text="")

            extracted_text = response.choices[0].message.content
            activity.logger.info(f"OCR completed. Extracted {len(extracted_text)} characters.")
            return OcrActivityResult(full_text=extracted_text)

        except FileNotFoundError:
            activity.logger.error(f"File not found: {doc_input.file_path}")
            raise
        except Exception as e:
            activity.logger.error(f"Error during OCR: {e}", exc_info=True)
            raise

    @activity.defn
    async def perform_azure_summarization(self, ocr_result: OcrActivityResult) -> SummarizationActivityResult:
        """
        Takes extracted text and asks Azure OpenAI for a summary in JSON format.
        """
        activity.logger.info(f"Starting Azure OpenAI summarization for text length: {len(ocr_result.full_text)}")

        if not ocr_result.full_text:
            activity.logger.warning("Skipping summarization due to empty OCR text.")
            return SummarizationActivityResult(summary_json={"summary": "No text extracted.", "keywords": []})

        try:
            prompt = f"""
            Analyze the following text and provide a summary and keywords.
            Format your response as a JSON object with two fields:
            - "summary": A concise summary of the main points
            - "keywords": A list of 3-5 main keywords or key phrases

            Text to analyze:
            {ocr_result.full_text}
            """

            # Call Azure OpenAI API for summarization
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                response_format={"type": "json_object"},
                max_completion_tokens=1000
            )

            if not response.choices or not response.choices[0].message.content:
                activity.logger.warning("Azure OpenAI summarization response was empty.")
                return SummarizationActivityResult(
                    summary_json={"summary": "Summarization failed.", "keywords": []}
                )

            raw_response_content = response.choices[0].message.content
            activity.logger.info(f"Raw Azure OpenAI Summarization Response Content: {raw_response_content}")

            # Parse the JSON response
            try:
                summary_json = json.loads(raw_response_content)
                # Validate the response structure
                if not isinstance(summary_json, dict) or "summary" not in summary_json or "keywords" not in summary_json:
                    activity.logger.warning(f"Unexpected JSON structure received: {summary_json}")
                    # Attempt to handle potential nesting (basic example)
                    if isinstance(summary_json.get('summary'), str):
                        try:
                            # Check if the summary string itself is JSON
                            nested_json = json.loads(summary_json['summary'])
                            if isinstance(nested_json, dict) and "summary" in nested_json and "keywords" in nested_json:
                                activity.logger.info("Corrected nested JSON structure.")
                                summary_json = nested_json # Use the nested structure if valid
                            else:
                                raise ValueError("Nested JSON structure is also invalid.")
                        except (json.JSONDecodeError, TypeError):
                             # If summary is not valid JSON, or nested structure is bad, raise the original error
                             raise ValueError("Invalid response structure, and summary is not valid nested JSON.") 
                    else:    
                         raise ValueError("Invalid response structure")
                
                return SummarizationActivityResult(summary_json=summary_json)
            except json.JSONDecodeError as e:
                activity.logger.error(f"Failed to parse summarization response as JSON: {e}")
                # Fallback for unparseable response
                return SummarizationActivityResult(
                    summary_json={
                        "summary": raw_response_content[:500],  # Use raw content as fallback summary
                        "keywords": []
                    }
                )
            except ValueError as e:
                 activity.logger.error(f"JSON structure validation failed: {e}")
                 # Fallback for invalid structure
                 return SummarizationActivityResult(
                     summary_json={
                        "summary": str(summary_json) if 'summary_json' in locals() else raw_response_content[:500],
                        "keywords": []
                     }
                 )

        except Exception as e:
            activity.logger.error(f"Error during summarization: {e}", exc_info=True)
            raise 