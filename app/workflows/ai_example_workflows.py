# AIDEV-NOTE: Example workflows demonstrating multi-AI provider patterns
import asyncio
from temporalio import workflow
from temporalio.workflow import execute_activity
from datetime import timedelta

from app.models.ai_models import (
    AIRequest, AIResponse, MultiAIWorkflowInput, MultiAIWorkflowResult,
    GeminiActivities, OpenAIActivities, AnthropicActivities
)


@workflow.defn(name="ai-consensus-workflow")
class AIConsensusWorkflow:
    """
    Workflow that sends the same prompt to all three AI providers
    and creates a consensus response
    """
    
    @workflow.run
    async def run(self, input: MultiAIWorkflowInput) -> MultiAIWorkflowResult:
        # AIDEV-NOTE: Execute activities in parallel for better performance
        tasks = []
        
        if "gemini" in input.providers:
            gemini_request = AIRequest(prompt=input.initial_prompt, file_path=input.file_path)
            tasks.append(
                execute_activity(
                    GeminiActivities.process_request,
                    gemini_request,
                    task_queue="gemini-ai-queue",
                    start_to_close_timeout=timedelta(minutes=5),
                )
            )
        
        if "openai" in input.providers:
            openai_request = AIRequest(prompt=input.initial_prompt, file_path=input.file_path)
            tasks.append(
                execute_activity(
                    OpenAIActivities.process_request,
                    openai_request,
                    task_queue="openai-ai-queue",
                    start_to_close_timeout=timedelta(minutes=5),
                )
            )
        
        if "anthropic" in input.providers:
            anthropic_request = AIRequest(prompt=input.initial_prompt, file_path=input.file_path)
            tasks.append(
                execute_activity(
                    AnthropicActivities.process_request,
                    anthropic_request,
                    task_queue="anthropic-ai-queue",
                    start_to_close_timeout=timedelta(minutes=5),
                )
            )
        
        # Wait for all responses
        responses = await asyncio.gather(*tasks)
        
        # Build results dictionary
        results = {}
        for i, provider in enumerate(input.providers):
            results[provider] = responses[i]
        
        # Generate consensus using Anthropic (could be any provider)
        consensus_prompt = "Based on these AI responses, create a consensus summary:\n\n"
        for provider, response in results.items():
            consensus_prompt += f"**{provider.upper()} Response:**\n{response.content}\n\n"
        consensus_prompt += "Create a balanced consensus that incorporates the best insights from all responses."
        
        consensus_response = await execute_activity(
            AnthropicActivities.process_request,
            AIRequest(prompt=consensus_prompt),
            task_queue="anthropic-ai-queue",
            start_to_close_timeout=timedelta(minutes=5),
        )
        
        return MultiAIWorkflowResult(
            results=results,
            consensus=consensus_response.content,
            analysis=f"Processed with {len(input.providers)} AI providers"
        )


@workflow.defn(name="ai-chain-workflow")
class AIChainWorkflow:
    """
    Workflow that chains AI providers: 
    Gemini analyzes -> OpenAI refines -> Anthropic validates
    """
    
    @workflow.run
    async def run(self, input: MultiAIWorkflowInput) -> MultiAIWorkflowResult:
        results = {}
        
        # Step 1: Initial analysis with Gemini
        gemini_response = await execute_activity(
            GeminiActivities.process_request,
            AIRequest(
                prompt=f"Analyze this request and provide initial insights: {input.initial_prompt}",
                file_path=input.file_path
            ),
            task_queue="gemini-ai-queue",
            start_to_close_timeout=timedelta(minutes=5),
        )
        results["gemini"] = gemini_response
        
        # Step 2: Refinement with OpenAI
        refine_prompt = f"""
        Original request: {input.initial_prompt}
        
        Initial analysis from another AI:
        {gemini_response.content}
        
        Please refine and enhance this analysis with additional insights and improvements.
        """
        
        openai_response = await execute_activity(
            OpenAIActivities.process_request,
            AIRequest(prompt=refine_prompt, file_path=input.file_path),
            task_queue="openai-ai-queue",
            start_to_close_timeout=timedelta(minutes=5),
        )
        results["openai"] = openai_response
        
        # Step 3: Validation and final polish with Anthropic
        validate_prompt = f"""
        Original request: {input.initial_prompt}
        
        Analysis progression:
        1. Initial: {gemini_response.content}
        2. Refined: {openai_response.content}
        
        Please validate the analysis, correct any errors, and provide a final polished response.
        """
        
        anthropic_response = await execute_activity(
            AnthropicActivities.process_request,
            AIRequest(prompt=validate_prompt),
            task_queue="anthropic-ai-queue",
            start_to_close_timeout=timedelta(minutes=5),
        )
        results["anthropic"] = anthropic_response
        
        return MultiAIWorkflowResult(
            results=results,
            consensus=anthropic_response.content,
            analysis="Sequential processing: Gemini → OpenAI → Anthropic"
        )


@workflow.defn(name="ai-specialist-workflow")
class AISpecialistWorkflow:
    """
    Workflow that uses different AI providers for their strengths:
    - Gemini for vision/multimodal tasks
    - OpenAI for code generation
    - Anthropic for analysis and reasoning
    """
    
    @workflow.run
    async def run(self, input: MultiAIWorkflowInput) -> MultiAIWorkflowResult:
        results = {}
        tasks = []
        
        # AIDEV-NOTE: Specialized prompts for each provider based on strengths
        
        # Gemini: Best for multimodal/vision tasks
        if input.file_path and input.file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
            gemini_prompt = f"Analyze this image in detail and {input.initial_prompt}"
        else:
            gemini_prompt = f"Provide a creative and comprehensive response to: {input.initial_prompt}"
        
        tasks.append(
            execute_activity(
                GeminiActivities.process_request,
                AIRequest(prompt=gemini_prompt, file_path=input.file_path),
                task_queue="gemini-ai-queue",
                start_to_close_timeout=timedelta(minutes=5),
            )
        )
        
        # OpenAI: Best for code and technical tasks
        openai_prompt = f"""
        Technical analysis requested: {input.initial_prompt}
        
        Please provide:
        1. Technical implementation details
        2. Code examples if applicable
        3. Best practices and considerations
        """
        
        tasks.append(
            execute_activity(
                OpenAIActivities.process_request,
                AIRequest(prompt=openai_prompt, file_path=input.file_path),
                task_queue="openai-ai-queue",
                start_to_close_timeout=timedelta(minutes=5),
            )
        )
        
        # Anthropic: Best for reasoning and analysis
        anthropic_prompt = f"""
        Analytical task: {input.initial_prompt}
        
        Please provide:
        1. Logical analysis and reasoning
        2. Potential challenges and solutions
        3. Strategic recommendations
        """
        
        tasks.append(
            execute_activity(
                AnthropicActivities.process_request,
                AIRequest(prompt=anthropic_prompt, file_path=input.file_path),
                task_queue="anthropic-ai-queue",
                start_to_close_timeout=timedelta(minutes=5),
            )
        )
        
        # Execute all tasks in parallel
        responses = await asyncio.gather(*tasks)
        
        results["gemini"] = responses[0]
        results["openai"] = responses[1]
        results["anthropic"] = responses[2]
        
        # Synthesize results
        synthesis_prompt = f"""
        Synthesize these specialized analyses into a comprehensive response:
        
        Visual/Creative Analysis (Gemini):
        {responses[0].content}
        
        Technical Analysis (OpenAI):
        {responses[1].content}
        
        Strategic Analysis (Anthropic):
        {responses[2].content}
        
        Create a unified response that leverages the strengths of each analysis.
        """
        
        final_response = await execute_activity(
            AnthropicActivities.process_request,
            AIRequest(prompt=synthesis_prompt),
            task_queue="anthropic-ai-queue",
            start_to_close_timeout=timedelta(minutes=5),
        )
        
        return MultiAIWorkflowResult(
            results=results,
            consensus=final_response.content,
            analysis="Specialized processing: Gemini (vision/creative) + OpenAI (technical) + Anthropic (analytical)"
        )