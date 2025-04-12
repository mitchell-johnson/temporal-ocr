# activities.py
import os
import google.generativeai as genai
from google.generativeai.types import GenerationConfig
from temporalio import activity
from pydantic import BaseModel, Field
import json
import logging
import mimetypes
import re

# Import shared objects
from shared import DocumentInput, OcrActivityResult, SummarizationActivityResult, GeminiActivities

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Pydantic Model for Expected JSON Summary ---
# Define the structure you expect Gemini to return for the summary
class SummarySchema(BaseModel):
    summary: str = Field(description="A concise summary of the provided text.")
    keywords: list[str] = Field(description="A list of 3-5 main keywords from the text.", default_factory=list)

# --- Activity Implementation ---
class GeminiActivitiesImpl(GeminiActivities):

    def __init__(self):
        # Configure Gemini Client (Ensure GEMINI_API_KEY is set in environment)
        api_key = "AIzaSyCjL31Uwy_DI3jDMw5d4T7KEMeLggW4HEU"
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set.")
        
        # Configure the Gemini API
        genai.configure(api_key=api_key)
        
        # Initialize models with specific configurations
        self.ocr_model = genai.GenerativeModel(
            model_name='gemini-2.5-pro-preview-03-25',
            generation_config=GenerationConfig(
                temperature=0.1,  # Lower temperature for more focused responses
                top_p=0.95,
                top_k=40,
            )
        )
        
        self.summarize_model = genai.GenerativeModel(
            model_name='gemini-2.5-pro-preview-03-25',
            generation_config=GenerationConfig(
                temperature=0.3,  # Slightly higher for summarization
                top_p=0.95,
                top_k=40,
            )
        )
        
        logger.info("Gemini Activities Initialized with configured models.")

    @activity.defn
    async def perform_ocr(self, doc_input: DocumentInput) -> OcrActivityResult:
        """
        Reads an image file, sends it to Gemini for text extraction.
        """
        activity.logger.info(f"Starting OCR for file: {doc_input.file_path}")

        try:
            # Read the image file bytes
            with open(doc_input.file_path, "rb") as f:
                image_bytes = f.read()

            # Determine the file type and set appropriate mime type
            mime_type, _ = mimetypes.guess_type(doc_input.file_path)
            if not mime_type:
                mime_type = 'image/jpeg'  # default to jpeg if unknown

            # Prepare the request for Gemini
            prompt = """
            Extract all text content from this image. 
            Preserve the exact formatting, spacing, and structure of the text as it appears in the image.
            Include all numbers, punctuation, and special characters exactly as they appear.
            """

            # Call Gemini API with structured content
            activity.logger.info("Sending request to Gemini for OCR...")
            response = await self.ocr_model.generate_content_async(
                [
                    prompt,
                    {
                        "mime_type": mime_type,
                        "data": image_bytes
                    }
                ]
            )

            # Extract text - Handle potential errors or empty responses
            if not response.text:
                activity.logger.warning("Gemini OCR response was empty.")
                return OcrActivityResult(full_text="")

            activity.logger.info(f"OCR completed. Extracted {len(response.text)} characters.")
            return OcrActivityResult(full_text=response.text)

        except FileNotFoundError:
            activity.logger.error(f"File not found: {doc_input.file_path}")
            raise
        except Exception as e:
            activity.logger.error(f"Error during OCR: {e}", exc_info=True)
            raise

    @activity.defn
    async def perform_summarization(self, ocr_result: OcrActivityResult) -> SummarizationActivityResult:
        """
        Takes extracted text and asks Gemini for a summary in JSON format.
        """
        activity.logger.info(f"Starting summarization for text length: {len(ocr_result.full_text)}")

        if not ocr_result.full_text:
            activity.logger.warning("Skipping summarization due to empty OCR text.")
            return SummarizationActivityResult(summary_json={"summary": "No text extracted.", "keywords": []})

        try:
            prompt = f"""
            Analyze the following text and provide a summary and keywords.
            Format your response *strictly* as a JSON object with ONLY two top-level fields:
            - "summary": A concise summary of the main points.
            - "keywords": A list of 3-5 main keywords or key phrases.
            Do not include any text before or after the JSON object itself.

            Text to analyze:
            {ocr_result.full_text}
            """

            # Call Gemini API for summarization
            response = await self.summarize_model.generate_content_async(prompt)
            
            if not response.text:
                activity.logger.warning("Gemini summarization response was empty.")
                return SummarizationActivityResult(
                    summary_json={"summary": "Summarization failed.", "keywords": []}
                )

            raw_response_content = response.text
            activity.logger.info(f"Raw Gemini Summarization Response Content: {raw_response_content}")

            # Attempt to find JSON within the response text if it's not pure JSON
            json_string = None
            try:
                # Check if the whole response is JSON
                json.loads(raw_response_content)
                json_string = raw_response_content
            except json.JSONDecodeError:
                # Try to extract JSON block if surrounded by text or markdown backticks
                match = re.search(r"```(?:json)?\s*({.*?})\s*```", raw_response_content, re.DOTALL)
                if match:
                    json_string = match.group(1)
                    activity.logger.info("Extracted JSON block from Markdown.")
                else:
                    # Fallback: Look for the first '{' and last '}'
                    start = raw_response_content.find('{')
                    end = raw_response_content.rfind('}')
                    if start != -1 and end != -1 and start < end:
                         json_string = raw_response_content[start:end+1]
                         activity.logger.info("Attempting to parse substring between first '{' and last '}'.")
            
            if not json_string:
                activity.logger.error("Could not find or extract a valid JSON string from the response.")
                # Use the raw response as fallback summary if no JSON found
                return SummarizationActivityResult(
                    summary_json={
                        "summary": raw_response_content[:500],
                        "keywords": []
                    }
                 )
            
            # Parse the extracted/found JSON string
            try:
                summary_json = json.loads(json_string)
                
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
                activity.logger.error(f"Failed to parse extracted JSON string: {json_string}. Error: {e}")
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