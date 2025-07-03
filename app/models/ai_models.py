# AIDEV-NOTE: Generic AI models for Temporal workflows with Gemini, OpenAI, and Anthropic
from pydantic import BaseModel
from temporalio import activity
from typing import Optional, List, Dict, Any

# Generic AI request/response models
class AIRequest(BaseModel):
    """Generic request model for AI activities"""
    prompt: str
    file_path: Optional[str] = None  # Optional file input
    parameters: Optional[Dict[str, Any]] = None  # Additional parameters like temperature, max_tokens, etc.

class AIResponse(BaseModel):
    """Generic response model from AI activities"""
    content: str
    model_used: str
    tokens_used: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None

# Activity interfaces for each AI provider
class GeminiActivities:
    @activity.defn
    async def process_request(self, request: AIRequest) -> AIResponse:
        """Process a request using Google Gemini"""
        ...

class OpenAIActivities:
    @activity.defn
    async def process_request(self, request: AIRequest) -> AIResponse:
        """Process a request using OpenAI"""
        ...

class AnthropicActivities:
    @activity.defn
    async def process_request(self, request: AIRequest) -> AIResponse:
        """Process a request using Anthropic Claude"""
        ...

# Workflow-specific models
class MultiAIWorkflowInput(BaseModel):
    """Input for workflows that use multiple AI providers"""
    initial_prompt: str
    file_path: Optional[str] = None
    providers: List[str] = ["gemini", "openai", "anthropic"]

class MultiAIWorkflowResult(BaseModel):
    """Result from workflows using multiple AI providers"""
    results: Dict[str, AIResponse]
    consensus: Optional[str] = None
    analysis: Optional[str] = None