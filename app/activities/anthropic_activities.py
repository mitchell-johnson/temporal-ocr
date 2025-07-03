# AIDEV-NOTE: Generic Anthropic Claude activities for Temporal workflows
import os
import base64
import logging
from anthropic import AsyncAnthropic
from temporalio import activity
import mimetypes

from app.models.ai_models import AIRequest, AIResponse, AnthropicActivities

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AnthropicActivitiesImpl(AnthropicActivities):
    """Implementation of Anthropic Claude activities"""
    
    def __init__(self):
        # Configure Anthropic Client
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set.")
        
        self.client = AsyncAnthropic(api_key=api_key)
        self.default_model = "claude-3-opus-20240229"
        logger.info("Anthropic Activities initialized")

    @activity.defn
    async def process_request(self, request: AIRequest) -> AIResponse:
        """Process a request using Anthropic Claude"""
        activity.logger.info(f"Processing Anthropic request with prompt: {request.prompt[:100]}...")
        
        try:
            messages = []
            
            # Handle file input if provided
            if request.file_path:
                with open(request.file_path, "rb") as f:
                    file_bytes = f.read()
                
                mime_type, _ = mimetypes.guess_type(request.file_path)
                
                # AIDEV-NOTE: Claude supports image analysis
                if mime_type and mime_type.startswith('image/'):
                    base64_image = base64.b64encode(file_bytes).decode('utf-8')
                    messages.append({
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": request.prompt
                            },
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": mime_type,
                                    "data": base64_image
                                }
                            }
                        ]
                    })
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
            else:
                messages.append({
                    "role": "user",
                    "content": request.prompt
                })
            
            # Apply custom parameters
            params = {
                "model": self.default_model,
                "messages": messages,
                "max_tokens": 4096,
                "temperature": 0.7,
            }
            
            if request.parameters:
                params.update(request.parameters)
            
            # Make API call
            response = await self.client.messages.create(**params)
            
            # Calculate total tokens (Anthropic provides input and output tokens)
            total_tokens = None
            if hasattr(response, 'usage'):
                total_tokens = response.usage.input_tokens + response.usage.output_tokens
            
            return AIResponse(
                content=response.content[0].text if response.content else "",
                model_used=params["model"],
                tokens_used=total_tokens,
                metadata={
                    "stop_reason": response.stop_reason if hasattr(response, 'stop_reason') else None,
                    "input_tokens": response.usage.input_tokens if hasattr(response, 'usage') else None,
                    "output_tokens": response.usage.output_tokens if hasattr(response, 'usage') else None,
                }
            )
            
        except Exception as e:
            activity.logger.error(f"Error processing Anthropic request: {e}", exc_info=True)
            raise