# AI Temporal Workflow Environment

This project provides a generic AI temporal workflow environment with dedicated workers for Google Gemini, OpenAI, and Anthropic Claude. It demonstrates how to build robust, distributed AI workflows using Temporal.

## Architecture Overview

The system consists of:
- **3 Dedicated AI Workers**: Separate workers for Gemini, OpenAI, and Anthropic
- **Generic AI Activities**: Each worker exposes a `process_request` function that accepts prompts and optional files
- **3 Example Workflows**: Demonstrating different patterns for combining AI providers
- **Docker-based deployment**: Easy setup with docker-compose

## Prerequisites

- Docker and Docker Compose
- API Keys for:
  - Google Gemini (`GEMINI_API_KEY`)
  - OpenAI (`OPENAI_API_KEY`)
  - Anthropic Claude (`ANTHROPIC_API_KEY`)

## Quick Start

1. **Clone and setup environment variables**:
   ```bash
   # Create .env file with your API keys
   cat > .env << EOF
   GEMINI_API_KEY=your_gemini_key
   OPENAI_API_KEY=your_openai_key
   ANTHROPIC_API_KEY=your_anthropic_key
   EOF
   ```

2. **Start the services**:
   ```bash
   docker-compose up -d
   ```

   This starts:
   - Temporal server (port 7233)
   - Temporal UI (port 8088)
   - 3 AI Workers (Gemini, OpenAI, Anthropic)
   - Web application (port 8000)

3. **Monitor services**:
   - Temporal UI: http://localhost:8088
   - Web App: http://localhost:8000

## AI Workers

### 1. Gemini Worker
- **Task Queue**: `gemini-ai-queue`
- **Strengths**: Multimodal capabilities, vision tasks, creative responses
- **Models**: Uses Gemini 1.5 Pro

### 2. OpenAI Worker  
- **Task Queue**: `openai-ai-queue`
- **Strengths**: Code generation, technical analysis
- **Models**: GPT-4 Turbo (with vision support)

### 3. Anthropic Worker
- **Task Queue**: `anthropic-ai-queue`
- **Strengths**: Reasoning, analysis, strategic thinking
- **Models**: Claude 3 Opus

## Generic AI Activity Interface

Each worker implements the same interface:

```python
async def process_request(request: AIRequest) -> AIResponse:
    """
    Process an AI request
    
    Args:
        request: AIRequest containing:
            - prompt: str - The prompt to process
            - file_path: Optional[str] - Path to file (images, documents)
            - parameters: Optional[Dict] - Model parameters (temperature, etc.)
    
    Returns:
        AIResponse containing:
            - content: str - The AI response
            - model_used: str - Model that processed the request
            - tokens_used: Optional[int] - Token usage
            - metadata: Optional[Dict] - Additional metadata
    """
```

## Example Workflows

### 1. AI Consensus Workflow
Sends the same prompt to all three providers and creates a consensus response.

**Use Case**: When you need multiple perspectives or want to validate responses across models.

```python
@workflow.defn(name="ai-consensus-workflow")
class AIConsensusWorkflow:
    # Executes prompt on all providers in parallel
    # Creates consensus from all responses
```

### 2. AI Chain Workflow  
Sequential processing: Gemini → OpenAI → Anthropic

**Use Case**: When you want each AI to build upon the previous response.

```python
@workflow.defn(name="ai-chain-workflow")
class AIChainWorkflow:
    # Gemini: Initial analysis
    # OpenAI: Refines and enhances
    # Anthropic: Validates and polishes
```

### 3. AI Specialist Workflow
Uses each AI provider for its strengths in parallel, then synthesizes results.

**Use Case**: Complex tasks requiring different types of analysis.

```python
@workflow.defn(name="ai-specialist-workflow")
class AISpecialistWorkflow:
    # Gemini: Visual/creative analysis
    # OpenAI: Technical implementation
    # Anthropic: Strategic analysis
    # Synthesis: Combined insights
```

## Testing the Workflows

Run the test script to see all workflows in action:

```bash
# Using Docker
docker-compose exec webapp python scripts/test_ai_workflows.py

# Or locally (with dependencies installed)
python scripts/test_ai_workflows.py
```

## Extending the System

### Adding New AI Providers

1. Create a new activity implementation:
   ```python
   # app/activities/newai_activities.py
   class NewAIActivitiesImpl(NewAIActivities):
       async def process_request(self, request: AIRequest) -> AIResponse:
           # Implementation
   ```

2. Create a worker script:
   ```python
   # app/run_newai_worker.py
   worker = Worker(
       client,
       task_queue="newai-queue",
       activities=[newai_activities.process_request],
   )
   ```

3. Add to docker-compose:
   ```yaml
   newai-worker:
     container_name: newai-worker
     build: .
     command: python -m app.run_newai_worker
     environment:
       - NEWAI_API_KEY=${NEWAI_API_KEY}
   ```

### Creating Custom Workflows

```python
from temporalio import workflow
from app.models.ai_models import AIRequest, GeminiActivities

@workflow.defn(name="my-custom-workflow")
class MyCustomWorkflow:
    @workflow.run
    async def run(self, prompt: str):
        # Use any combination of AI workers
        result = await workflow.execute_activity(
            GeminiActivities.process_request,
            AIRequest(prompt=prompt),
            task_queue="gemini-ai-queue",
            start_to_close_timeout=timedelta(minutes=5),
        )
        return result
```

## File Support

All workers support file inputs:
- **Images**: Analyzed by vision-capable models
- **Text files**: Content included in prompts
- **Binary files**: Handled gracefully with metadata

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GEMINI_API_KEY` | Google Gemini API key | Yes |
| `OPENAI_API_KEY` | OpenAI API key | Yes |
| `ANTHROPIC_API_KEY` | Anthropic API key | Yes |
| `TEMPORAL_HOST` | Temporal server address | No (default: localhost:7233) |

## Monitoring and Debugging

1. **Temporal UI**: View workflows, activities, and worker status at http://localhost:8088

2. **Worker Logs**: 
   ```bash
   docker-compose logs -f gemini-worker
   docker-compose logs -f openai-worker
   docker-compose logs -f anthropic-worker
   ```

3. **Workflow History**: Each workflow execution is fully recorded in Temporal

## Best Practices

1. **Error Handling**: Workers automatically retry failed activities
2. **Timeouts**: Set appropriate timeouts for AI operations (default: 5 minutes)
3. **Rate Limiting**: Consider implementing rate limits for API calls
4. **File Cleanup**: Temporary files should be cleaned up after processing
5. **Security**: Never commit API keys; use environment variables

## Troubleshooting

1. **Worker not connecting**: Check TEMPORAL_HOST environment variable
2. **API errors**: Verify API keys are correct and have necessary permissions
3. **File not found**: Ensure file paths are relative to the worker's context
4. **Memory issues**: Large files may need streaming approaches

## License

MIT License - See LICENSE file for details