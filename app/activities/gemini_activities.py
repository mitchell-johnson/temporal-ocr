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
from app.models.shared import DocumentInput, GeminiDocumentResult, GeminiActivities

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Activity Implementation ---
class GeminiActivitiesImpl(GeminiActivities):

    def __init__(self):
        # Configure Gemini Client (Ensure GEMINI_API_KEY is set in environment)
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set.")
        
        # Configure the Gemini API
        genai.configure(api_key=api_key)
        
        # Initialize model with specific configuration
        self.gemini_model = genai.GenerativeModel(
            model_name='gemini-2.5-pro-exp-03-25',
            generation_config=GenerationConfig(
                temperature=0.3,
                top_p=0.95,
                top_k=40,
            )
        )
        
        logger.info("Gemini Activities Initialized with configured model.")

    @activity.defn
    async def generate_markdown_and_summary(self, doc_input: DocumentInput) -> GeminiDocumentResult:
        """
        Reads a document file, generates markdown representation and summary using Gemini.
        """
        activity.logger.info(f"Starting markdown and summary generation for file: {doc_input.file_path}")

        try:
            # Read the document file
            with open(doc_input.file_path, "rb") as f:
                file_bytes = f.read()

            # Determine the file type and set appropriate mime type
            mime_type, _ = mimetypes.guess_type(doc_input.file_path)
            if not mime_type:
                mime_type = 'application/pdf'  # default to PDF if unknown

            # Prepare the request for Gemini for markdown generation
            markdown_prompt = """
            Convert this document to well-formatted markdown. 
            Preserve all text content, headings, lists, tables, and structure from the original document.
            Create appropriate markdown headings and formatting.
            Make sure the markdown is properly structured with clear heading hierarchy.
            """

            # Call Gemini API to generate markdown
            activity.logger.info("Sending request to Gemini for markdown generation...")
            markdown_response = await self.gemini_model.generate_content_async(
                [
                    markdown_prompt,
                    {
                        "mime_type": mime_type,
                        "data": file_bytes
                    }
                ]
            )

            # Extract markdown content
            if not markdown_response.text:
                activity.logger.warning("Gemini markdown generation response was empty.")
                markdown_content = "Failed to generate markdown content."
            else:
                markdown_content = markdown_response.text
                activity.logger.info(f"Markdown generated with {len(markdown_content)} characters.")

            # Now generate a summary of the important parts of the document
            summary_prompt = f"""
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

            # Call Gemini API for summarization
            activity.logger.info("Sending request to Gemini for summary generation...")
            summary_response = await self.gemini_model.generate_content_async(summary_prompt)
            
            if not summary_response.text:
                activity.logger.warning("Gemini summary generation response was empty.")
                summary = "Failed to generate summary."
            else:
                summary = summary_response.text
                activity.logger.info(f"Summary generated with {len(summary)} characters.")

            return GeminiDocumentResult(
                markdown_content=markdown_content,
                summary=summary
            )

        except FileNotFoundError:
            activity.logger.error(f"File not found: {doc_input.file_path}")
            raise
        except Exception as e:
            activity.logger.error(f"Error during markdown and summary generation: {e}", exc_info=True)
            raise