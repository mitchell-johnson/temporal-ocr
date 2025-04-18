# azure_activities.py
import os
import base64
import json
import logging
import mimetypes
from openai import AsyncAzureOpenAI
from temporalio import activity
from typing import List

# Import shared objects
from app.models.shared import DocumentInput, AzureValidationResult, AzureOpenAIActivities

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    async def validate_summary(self, doc_input: DocumentInput, summary: str) -> AzureValidationResult:
        """
        Takes a document and its summary, and validates if the summary is accurate.
        Also suggests improvements to the summary if needed.
        """
        activity.logger.info(f"Starting Azure OpenAI summary validation for document: {doc_input.file_path}")

        try:
            # For PDF files, we can only use the summary-only validation approach
            # since we can't directly send PDFs to the Azure OpenAI API
            activity.logger.info("Using summary-only validation approach without document.")
            content = self._get_validation_prompt_without_document(summary)
            
            # Call Azure OpenAI API for validation without the document
            activity.logger.info("Sending request to Azure OpenAI for summary validation...")
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "user",
                        "content": content
                    }
                ],
                response_format={"type": "json_object"},
                max_completion_tokens=2000
            )

            if not response.choices or not response.choices[0].message.content:
                activity.logger.warning("Azure OpenAI validation response was empty.")
                return AzureValidationResult(
                    is_accurate=False,
                    suggested_improvements=["Could not validate the summary."]
                )

            raw_response_content = response.choices[0].message.content
            activity.logger.info(f"Raw Azure OpenAI Validation Response Content: {raw_response_content}")

            # Parse the JSON response
            try:
                validation_json = json.loads(raw_response_content)
                
                # Extract validation information
                is_accurate = validation_json.get("is_accurate", False)
                suggested_improvements = validation_json.get("suggested_improvements", [])
                improved_summary = validation_json.get("improved_summary", None)
                
                return AzureValidationResult(
                    is_accurate=is_accurate,
                    suggested_improvements=suggested_improvements,
                    improved_summary=improved_summary
                )
                
            except json.JSONDecodeError as e:
                activity.logger.error(f"Failed to parse validation response as JSON: {e}")
                # Return a default response when JSON parsing fails
                return AzureValidationResult(
                    is_accurate=False,
                    suggested_improvements=["Error parsing validation response."]
                )

        except FileNotFoundError:
            activity.logger.error(f"File not found: {doc_input.file_path}")
            raise
        except Exception as e:
            activity.logger.error(f"Error during summary validation: {e}", exc_info=True)
            raise

    def _get_validation_prompt_without_document(self, summary: str) -> str:
        """Helper to create the validation prompt without document reference"""
        return f"""
        You are evaluating the quality of a document summary. The summary should be comprehensive, accurate, and capture the key points.
        
        Your task is to:
        1. Evaluate if the summary appears to be comprehensive and well-structured
        2. Suggest specific improvements to make the summary more effective
        3. If necessary, provide an improved version of the summary
        
        The summary to evaluate is:
        
        {summary}
        
        Please provide your evaluation in JSON format with these fields:
        - "is_accurate": Boolean indicating if the summary appears to be of good quality (true/false)
        - "suggested_improvements": Array of specific improvements (empty array if none)
        - "improved_summary": Optional improved version of the summary (only if significant improvements are needed)
        """ 