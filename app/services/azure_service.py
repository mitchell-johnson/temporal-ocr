import os
import json
import base64
import logging
import mimetypes
from openai import AsyncAzureOpenAI
from typing import Dict, List, Optional, Any, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AzureService:
    """Service for direct interaction with Azure OpenAI API"""

    def __init__(self):
        # Configure Azure OpenAI Client
        api_key = os.getenv("AZURE_OPENAI_API_KEY")
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        
        # Default model settings
        self.default_model = os.getenv("AZURE_OPENAI_MODEL_NAME")
        self.ocr_model = os.getenv("AZURE_OPENAI_OCR_MODEL", self.default_model)
        self.summary_model = os.getenv("AZURE_OPENAI_SUMMARY_MODEL", self.default_model)
        self.validation_model = os.getenv("AZURE_OPENAI_VALIDATION_MODEL", self.default_model)
        
        if not all([api_key, endpoint, self.default_model]):
            raise ValueError("Azure OpenAI configuration missing. Please set AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, and AZURE_OPENAI_MODEL_NAME environment variables.")
        
        self.client = AsyncAzureOpenAI(
            api_key=api_key,
            api_version="2024-02-15-preview",  # Latest version supporting vision
            azure_endpoint=endpoint
        )
        
        # Log configuration details (with sensitive info masked)
        logger.info(f"Azure OpenAI Endpoint: {endpoint}")
        logger.info(f"Azure OpenAI Default Model: {self.default_model}")
        logger.info(f"Azure OpenAI OCR Model: {self.ocr_model}")
        logger.info(f"Azure OpenAI Summary Model: {self.summary_model}")
        logger.info(f"Azure OpenAI Validation Model: {self.validation_model}")
        logger.info(f"Azure OpenAI API Key: {'*' * 8}{api_key[-4:]}")  # Only show last 4 chars
        
        logger.info("Azure OpenAI Service Initialized.")

    async def process_document(self, file_path: str) -> Tuple[str, str]:
        """
        Processes a document file using Azure OpenAI and returns the markdown content and summary.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            Tuple[str, str]: (markdown_content, summary)
        """
        logger.info(f"Starting Azure markdown and summary generation for file: {file_path}")

        try:
            # Read the document file
            with open(file_path, "rb") as f:
                file_bytes = f.read()

            # Determine the file type and set appropriate mime type
            mime_type, _ = mimetypes.guess_type(file_path)
            if not mime_type:
                mime_type = 'application/pdf'  # default to PDF if unknown

            # Step 1: Extract text and convert to markdown using Azure OpenAI
            markdown_content = await self._generate_markdown(file_bytes, mime_type)
            
            # Step 2: Generate summary from markdown content
            summary = await self._generate_summary(markdown_content)
            
            return markdown_content, summary

        except FileNotFoundError:
            logger.error(f"File not found: {file_path}")
            raise
        except Exception as e:
            logger.error(f"Error during Azure markdown and summary generation: {e}", exc_info=True)
            raise

    async def _generate_markdown(self, file_bytes: bytes, mime_type: str) -> str:
        """Generate markdown representation of a document using Azure OpenAI"""
        # Convert binary data to base64
        base64_data = base64.b64encode(file_bytes).decode('ascii')
        
        # Create the message with the file attachment
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Convert this document to well-formatted markdown. Preserve all text content, headings, lists, tables, and structure from the original document. Create appropriate markdown headings and formatting. Make sure the markdown is properly structured with clear heading hierarchy."
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime_type};base64,{base64_data}"
                        }
                    }
                ]
            }
        ]
        
        # Call Azure OpenAI API for markdown generation
        logger.info("Sending request to Azure OpenAI for markdown generation...")
        response = await self.client.chat.completions.create(
            model=self.ocr_model,
            messages=messages,
            max_tokens=4000
        )
        
        if not response.choices or not response.choices[0].message.content:
            logger.warning("Azure OpenAI markdown generation response was empty.")
            return "Failed to generate markdown content."
        
        markdown_content = response.choices[0].message.content
        logger.info(f"Markdown generated with {len(markdown_content)} characters.")
        
        return markdown_content

    async def _generate_summary(self, markdown_content: str) -> str:
        """Generate a summary from markdown content using Azure OpenAI"""
        # Create the prompt for summarization
        summarization_prompt = f"""
        Create a comprehensive summary of the following markdown document. 
        Format your summary as well-structured markdown with:
        - A clear hierarchical structure using headings (## for main sections, ### for subsections)
        - Bullet points for key findings or important facts
        - Bold and italic formatting for emphasis on important terms
        - Lists for sequential information when appropriate
        - Brief tables for summarizing structured data if present
        
        Focus on the most important information, key findings, main points, and significant details.
        Make sure the summary captures the essence of the document and is easy to understand.
        
        Markdown document:
        {markdown_content}
        """
        
        # Call Azure OpenAI API for summarization
        logger.info("Sending request to Azure OpenAI for summary generation...")
        response = await self.client.chat.completions.create(
            model=self.summary_model,
            messages=[{"role": "user", "content": summarization_prompt}],
            max_tokens=2000
        )
        
        if not response.choices or not response.choices[0].message.content:
            logger.warning("Azure OpenAI summary generation response was empty.")
            return "Failed to generate summary."
        
        summary = response.choices[0].message.content
        logger.info(f"Summary generated with {len(summary)} characters.")
        
        return summary

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
                model=self.validation_model,
                messages=[
                    {
                        "role": "user",
                        "content": validation_prompt
                    }
                ],
                response_format={"type": "json_object"},
                max_tokens=2000
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