# AIDEV-NOTE: Generic Gemini AI activities for Temporal workflows
import os
import google.generativeai as genai
from google.generativeai.types import GenerationConfig
from temporalio import activity
import logging
import mimetypes

from app.models.ai_models import AIRequest, AIResponse, GeminiActivities

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GeminiActivitiesImpl(GeminiActivities):
    """Implementation of Gemini AI activities"""
    
    def __init__(self):
        # Configure Gemini Client
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set.")
        
        genai.configure(api_key=api_key)
        
        # AIDEV-NOTE: Using latest Gemini model for best performance
        self.model = genai.GenerativeModel(
            model_name='gemini-1.5-pro',
            generation_config=GenerationConfig(
                temperature=0.7,
                top_p=0.95,
                top_k=40,
                max_output_tokens=4096,
            )
        )
        logger.info("Gemini Activities initialized")

    @activity.defn
    async def process_request(self, request: AIRequest) -> AIResponse:
        """Process a request using Google Gemini"""
        activity.logger.info(f"Processing Gemini request with prompt: {request.prompt[:100]}...")
        
        try:
            contents = [request.prompt]
            
            # If file is provided, include it in the request
            if request.file_path:
                with open(request.file_path, "rb") as f:
                    file_bytes = f.read()
                
                mime_type, _ = mimetypes.guess_type(request.file_path)
                if not mime_type:
                    mime_type = 'application/octet-stream'
                
                contents.append({
                    "mime_type": mime_type,
                    "data": file_bytes
                })
                activity.logger.info(f"Including file: {request.file_path} with mime type: {mime_type}")
            
            # Apply custom parameters if provided
            if request.parameters:
                gen_config = GenerationConfig(**request.parameters)
                model = genai.GenerativeModel(
                    model_name='gemini-1.5-pro',
                    generation_config=gen_config
                )
            else:
                model = self.model
            
            # Generate response
            response = await model.generate_content_async(contents)
            
            # AIDEV-NOTE: Handle safety ratings and blocked content
            if not response.text:
                activity.logger.warning("Gemini response was empty or blocked")
                return AIResponse(
                    content="Response was blocked due to safety filters",
                    model_used="gemini-1.5-pro",
                    metadata={"safety_ratings": str(response.prompt_feedback) if hasattr(response, 'prompt_feedback') else None}
                )
            
            return AIResponse(
                content=response.text,
                model_used="gemini-1.5-pro",
                tokens_used=None,  # Gemini doesn't provide token count in the same way
                metadata={
                    "finish_reason": response.candidates[0].finish_reason.name if response.candidates else None
                }
            )
            
        except Exception as e:
            activity.logger.error(f"Error processing Gemini request: {e}", exc_info=True)
            raise