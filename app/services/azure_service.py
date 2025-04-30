import os
import json
import logging
from openai import AsyncAzureOpenAI
from typing import Dict, List, Optional, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AzureService:
    """Service for direct interaction with Azure OpenAI API"""

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
        logger.info("Azure OpenAI Service Initialized.")

    async def validate_summary(self, summary: str) -> Dict[str, Any]:
        """
        Validates a document summary and suggests improvements.
        
        Args:
            summary: The document summary to validate
            
        Returns:
            Dict containing validation results with keys:
                - is_accurate: bool
                - suggested_improvements: List[str]
                - improved_summary: Optional[str]
        """
        logger.info("Starting Azure OpenAI summary validation")

        try:
            # Create validation prompt
            validation_prompt = self._get_validation_prompt(summary)
            
            # Call Azure OpenAI API for validation
            logger.info("Sending request to Azure OpenAI for summary validation...")
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "user",
                        "content": validation_prompt
                    }
                ],
                response_format={"type": "json_object"},
                max_completion_tokens=2000
            )

            if not response.choices or not response.choices[0].message.content:
                logger.warning("Azure OpenAI validation response was empty.")
                return {
                    "is_accurate": False,
                    "suggested_improvements": ["Could not validate the summary."],
                    "improved_summary": None
                }

            raw_response_content = response.choices[0].message.content
            logger.info(f"Raw Azure OpenAI Validation Response Content: {raw_response_content}")

            # Parse the JSON response
            try:
                validation_json = json.loads(raw_response_content)
                
                # Extract validation information
                is_accurate = validation_json.get("is_accurate", False)
                suggested_improvements = validation_json.get("suggested_improvements", [])
                improved_summary = validation_json.get("improved_summary", None)
                
                return {
                    "is_accurate": is_accurate,
                    "suggested_improvements": suggested_improvements,
                    "improved_summary": improved_summary
                }
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse validation response as JSON: {e}")
                # Return a default response when JSON parsing fails
                return {
                    "is_accurate": False,
                    "suggested_improvements": ["Error parsing validation response."],
                    "improved_summary": None
                }

        except Exception as e:
            logger.error(f"Error during summary validation: {e}", exc_info=True)
            raise

    def _get_validation_prompt(self, summary: str) -> str:
        """Helper to create the validation prompt"""
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