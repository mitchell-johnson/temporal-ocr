# AI Temporal Workflow Environment - C# Version

This is the C# implementation of the AI temporal workflow environment with dedicated workers for Google Gemini, OpenAI, and Anthropic Claude. It demonstrates building robust, distributed AI workflows using Temporal with .NET 8.

## Quick Start with Helper Script

A helper script `run.sh` is provided for easy execution:

```bash
# Run with Docker (recommended)
./run.sh docker

# Run individual workers locally
./run.sh gemini      # Run Gemini worker
./run.sh openai      # Run OpenAI worker
./run.sh anthropic   # Run Anthropic worker
./run.sh workflow    # Run workflow worker
./run.sh test        # Run workflow tests
```

## Architecture Overview

The system consists of:
- **3 Dedicated AI Workers**: Separate workers for Gemini, OpenAI, and Anthropic
- **Generic AI Activities**: Each worker exposes a `ProcessRequestAsync` method that accepts prompts and optional files
- **3 Example Workflows**: Demonstrating different patterns for combining AI providers
- **Docker-based deployment**: Easy setup with docker-compose
- **.NET 8 based**: Modern C# with async/await patterns throughout

## Prerequisites

- Docker and Docker Compose
- .NET 8 SDK (for local development)
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

2. **Start the services using the C# docker-compose**:
   ```bash
   docker-compose -f docker-compose.csharp.yml up -d
   ```

   This starts:
   - Temporal server (port 7233)
   - Temporal UI (port 8088)
   - 3 AI Workers (Gemini, OpenAI, Anthropic)
   - Workflow Worker

3. **Monitor services**:
   - Temporal UI: http://localhost:8088

## Local Development

### Building the Project

```bash
# Restore dependencies
dotnet restore

# Build the project
dotnet build

# Run a specific worker locally
dotnet run -- gemini      # Run Gemini worker
dotnet run -- openai      # Run OpenAI worker
dotnet run -- anthropic   # Run Anthropic worker
dotnet run -- workflow    # Run workflow worker
dotnet run -- all         # Run all workers (development only)
```

### Running Tests

```bash
# Add a test command to Program.cs or run the test workflow
dotnet run -- test
```

## AI Workers

### 1. Gemini Worker
- **Task Queue**: `gemini-ai-queue`
- **Implementation**: `src/TemporalAI/Activities/GeminiActivities.cs`
- **Uses**: Google Gemini API (REST)
- **Strengths**: Multimodal capabilities, vision tasks

### 2. OpenAI Worker  
- **Task Queue**: `openai-ai-queue`
- **Implementation**: `src/TemporalAI/Activities/OpenAIActivities.cs`
- **Uses**: Official OpenAI .NET SDK
- **Strengths**: Code generation, technical analysis

### 3. Anthropic Worker
- **Task Queue**: `anthropic-ai-queue`
- **Implementation**: `src/TemporalAI/Activities/AnthropicActivities.cs`
- **Uses**: HTTP client with Anthropic API
- **Strengths**: Reasoning, analysis, strategic thinking

## Generic AI Activity Interface

Each worker implements the same interface:

```csharp
public interface IGeminiActivities // (same for OpenAI and Anthropic)
{
    [Activity]
    Task<AIResponse> ProcessRequestAsync(AIRequest request);
}

public record AIRequest
{
    public required string Prompt { get; init; }
    public string? FilePath { get; init; }
    public Dictionary<string, object>? Parameters { get; init; }
}

public record AIResponse
{
    public required string Content { get; init; }
    public required string ModelUsed { get; init; }
    public int? TokensUsed { get; init; }
    public Dictionary<string, object>? Metadata { get; init; }
}
```

## Example Workflows

### 1. AI Consensus Workflow
```csharp
[Workflow("ai-consensus-workflow")]
public class AIConsensusWorkflow
{
    // Executes prompt on all providers in parallel
    // Creates consensus from all responses
}
```

### 2. AI Chain Workflow  
```csharp
[Workflow("ai-chain-workflow")]
public class AIChainWorkflow
{
    // Sequential: Gemini → OpenAI → Anthropic
    // Each builds on the previous response
}
```

### 3. AI Specialist Workflow
```csharp
[Workflow("ai-specialist-workflow")]
public class AISpecialistWorkflow
{
    // Uses each AI for its strengths in parallel
    // Synthesizes results into unified response
}
```

## Project Structure

```
.
├── TemporalAI.csproj              # Project file with dependencies
├── src/
│   └── TemporalAI/
│       ├── Program.cs             # Main entry point
│       ├── TestWorkflows.cs       # Test runner for workflows
│       ├── Models/
│       │   └── AIModels.cs        # Data models and interfaces
│       ├── Activities/
│       │   ├── GeminiActivities.cs    # Gemini implementation
│       │   ├── OpenAIActivities.cs    # OpenAI implementation
│       │   └── AnthropicActivities.cs # Anthropic implementation
│       ├── Workers/
│       │   ├── GeminiWorker.cs        # Gemini worker host
│       │   ├── OpenAIWorker.cs        # OpenAI worker host
│       │   ├── AnthropicWorker.cs     # Anthropic worker host
│       │   └── WorkflowWorker.cs      # Workflow worker host
│       └── Workflows/
│           └── AIExampleWorkflows.cs  # Example workflow implementations
├── Dockerfile.csharp              # .NET Docker image
└── docker-compose.csharp.yml      # Docker compose for C# version
```



## Extending the System

### Adding New AI Providers

1. Create the interface:
   ```csharp
   public interface INewAIActivities
   {
       [Activity]
       Task<AIResponse> ProcessRequestAsync(AIRequest request);
   }
   ```

2. Implement the activities:
   ```csharp
   public class NewAIActivities : INewAIActivities
   {
       public async Task<AIResponse> ProcessRequestAsync(AIRequest request)
       {
           // Implementation
       }
   }
   ```

3. Create the worker:
   ```csharp
   public class NewAIWorker
   {
       public static async Task RunAsync(string[] args)
       {
           // Worker setup and registration
       }
   }
   ```

4. Update Program.cs to handle the new worker type

### Creating Custom Workflows

```csharp
[Workflow("my-custom-workflow")]
public class MyCustomWorkflow
{
    [WorkflowRun]
    public async Task<MyResult> RunAsync(MyInput input)
    {
        // Use any combination of AI workers
        var result = await Workflow.ExecuteActivityAsync<IGeminiActivities, AIResponse>(
            a => a.ProcessRequestAsync(new AIRequest { Prompt = input.Prompt }),
            new ActivityOptions
            {
                TaskQueue = "gemini-ai-queue",
                StartToCloseTimeout = TimeSpan.FromMinutes(5)
            }
        );
        return new MyResult { Content = result.Content };
    }
}
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GEMINI_API_KEY` | Google Gemini API key | Yes |
| `OPENAI_API_KEY` | OpenAI API key | Yes |
| `ANTHROPIC_API_KEY` | Anthropic API key | Yes |
| `TEMPORAL_HOST` | Temporal server address | No (default: localhost:7233) |

## Troubleshooting

1. **Build errors**: Ensure you have .NET 8 SDK installed
2. **API errors**: Verify API keys are correct and have necessary permissions
3. **Docker issues**: Check that all containers are running with `docker ps`
4. **Worker not connecting**: Verify TEMPORAL_HOST is correct
5. **Package restore failures**: Clear NuGet cache with `dotnet nuget locals all --clear`

## Performance Considerations

- Workers support concurrent activity execution (default: 10)
- Use appropriate timeouts for AI operations (default: 5 minutes)
- Consider implementing circuit breakers for API failures
- Monitor memory usage, especially with large file processing

## License

MIT License - See LICENSE file for details