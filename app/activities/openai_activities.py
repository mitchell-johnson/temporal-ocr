# AIDEV-NOTE: Generic OpenAI activities for Temporal workflows
import os
import base64
import logging
from openai import AsyncOpenAI
from temporalio import activity
import mimetypes

from app.models.ai_models import AIRequest, AIResponse, OpenAIActivities

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OpenAIActivitiesImpl(OpenAIActivities):
    """Implementation of OpenAI activities"""
    
    def __init__(self):
        # Configure OpenAI Client
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set.")
        
        self.client = AsyncOpenAI(api_key=api_key)
        self.default_model = "gpt-4-turbo-preview"
        logger.info("OpenAI Activities initialized")

    @activity.defn
    async def process_request(self, request: AIRequest) -> AIResponse:
        """Process a request using OpenAI"""
        activity.logger.info(f"Processing OpenAI request with prompt: {request.prompt[:100]}...")
        
        try:
            messages = []
            
            # Handle file input if provided
            if request.file_path:
                with open(request.file_path, "rb") as f:
                    file_bytes = f.read()
                
                mime_type, _ = mimetypes.guess_type(request.file_path)
                
                # AIDEV-NOTE: OpenAI supports image files for vision models
                if mime_type and mime_type.startswith('image/'):
                    base64_image = base64.b64encode(file_bytes).decode('utf-8')
                    messages.append({
                        "role": "user",
                        "content": [
                            {"type": "text", "text": request.prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{mime_type};base64,{base64_image}"
                                }
                            }
                        ]
                    })
                    model = "gpt-4-vision-preview"  # Use vision model for images
                else:
                    # For non-image files, include content as text if possible
                    try:
                        file_content = file_bytes.decode('utf-8')
                        messages.append({
                            "role": "user",
                            "content": f"{request.prompt}\n\nFile content:\n{file_content}"
                        })
                    except:
                        messages.append({
                            "role": "user",
                            "content": f"{request.prompt}\n\n[Binary file provided: {request.file_path}]"
                        })
                    model = self.default_model
            else:
                messages.append({"role": "user", "content": request.prompt})
                model = self.default_model
            
            # Apply custom parameters
            params = {
                "model": model,
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 4096,
            }
            
            if request.parameters:
                params.update(request.parameters)
                if "model" in request.parameters:
                    model = request.parameters["model"]
            
            # Make API call
            response = await self.client.chat.completions.create(**params)
            
            return AIResponse(
                content=response.choices[0].message.content,
                model_used=model,
                tokens_used=response.usage.total_tokens if response.usage else None,
                metadata={
                    "finish_reason": response.choices[0].finish_reason,
                    "prompt_tokens": response.usage.prompt_tokens if response.usage else None,
                    "completion_tokens": response.usage.completion_tokens if response.usage else None,
                }
            )
            
        except Exception as e:
            activity.logger.error(f"Error processing OpenAI request: {e}", exc_info=True)
            raise