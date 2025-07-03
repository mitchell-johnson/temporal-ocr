# Temporal AI Workflow Service - C# Implementation

This project provides a generic AI temporal workflow environment with dedicated workers for Google Gemini, OpenAI, and Anthropic Claude. It demonstrates how to build robust, distributed AI workflows using Temporal with .NET 8 and C#.

## Features

- **3 AI Workers**: Dedicated workers for Google Gemini, OpenAI, and Anthropic Claude
- **Generic AI Interface**: Each worker exposes a `ProcessRequestAsync` method for prompts and files
- **Example Workflows**: Three workflow patterns demonstrating AI provider combinations
- **Temporal Integration**: Reliable, fault-tolerant workflow execution with automatic retries
- **Multi-Provider Support**: Use different AI providers for their strengths
- **Docker Support**: Easy deployment with Docker Compose
- **Strong Typing**: Full C# type safety with records and interfaces

## Prerequisites

- Docker and Docker Compose
- .NET 8 SDK (for local development)
- API keys for:
  - Google Gemini API
  - OpenAI API
  - Anthropic Claude API

## Quick Start

1. **Setup environment variables**:
   ```bash
   # Copy the example environment file
   cp .env.example .env
   # Edit .env with your API keys
   ```

2. **Run with Docker**:
   ```bash
   # Using the helper script
   ./run.sh docker
   
   # Or directly with docker-compose
   docker-compose up -d
   ```

3. **Access Temporal UI**:
   - http://localhost:8088

## Local Development

```bash
# Restore dependencies
dotnet restore

# Run specific workers
./run.sh gemini      # Gemini worker
./run.sh openai      # OpenAI worker
./run.sh anthropic   # Anthropic worker
./run.sh workflow    # Workflow worker
./run.sh test        # Run tests
```

## Example Workflows

The project includes three example workflows:

1. **AI Consensus Workflow**: Sends the same prompt to all three AI providers and creates a consensus response
2. **AI Chain Workflow**: Sequential processing where each AI builds on the previous response
3. **AI Specialist Workflow**: Uses each AI provider for its strengths in parallel

## Project Structure

```
├── TemporalAI.csproj              # Project file
├── src/TemporalAI/
│   ├── Activities/                # AI provider implementations
│   ├── Models/                    # Data models
│   ├── Workers/                   # Worker hosts
│   └── Workflows/                 # Example workflows
├── docker-compose.yml             # Docker services
├── Dockerfile                     # .NET Docker image
└── run.sh                         # Helper script
```

## AI Providers

### Google Gemini
- Model: gemini-1.5-pro
- Supports: Text and image inputs
- Best for: Multimodal tasks, creative responses

### OpenAI
- Model: gpt-4-turbo-preview (gpt-4-vision-preview for images)
- Supports: Text and image inputs
- Best for: Code generation, technical analysis

### Anthropic Claude
- Model: claude-3-opus-20240229
- Supports: Text and image inputs
- Best for: Reasoning, analysis, strategic thinking

## Documentation

For complete documentation, see [AI_TEMPORAL_WORKFLOW_README.md](AI_TEMPORAL_WORKFLOW_README.md)

## License

MIT License 