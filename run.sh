#!/bin/bash
# AIDEV-NOTE: Helper script to run the C# Temporal AI workers

# Check for command line arguments
if [ $# -eq 0 ]; then
    echo "Usage: ./run.sh <worker-type>"
    echo ""
    echo "Available worker types:"
    echo "  gemini    - Run the Gemini AI worker"
    echo "  openai    - Run the OpenAI worker"
    echo "  anthropic - Run the Anthropic worker"
    echo "  workflow  - Run the workflow worker"
    echo "  all       - Run all workers (development only)"
    echo "  test      - Run workflow tests"
    echo "  docker    - Run with docker-compose"
    exit 1
fi

WORKER_TYPE=$1

# Handle docker command specially
if [ "$WORKER_TYPE" == "docker" ]; then
    echo "Starting services with Docker Compose..."
    docker-compose up -d
    echo ""
    echo "Services started!"
    echo "- Temporal UI: http://localhost:8088"
    echo "- Temporal Server: localhost:7233"
    echo ""
    echo "To view logs: docker-compose logs -f"
    echo "To stop: docker-compose down"
    exit 0
fi

# Check if .NET is installed for non-docker commands
if ! command -v dotnet &> /dev/null; then
    echo "Error: .NET SDK is not installed. Please install .NET 8 SDK."
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Warning: .env file not found. Creating from .env.example..."
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "Please edit .env file with your API keys before running."
        exit 1
    else
        echo "Error: .env.example not found. Please create .env file with required API keys."
        exit 1
    fi
fi

# Load environment variables
export $(cat .env | grep -v '^#' | xargs)

# Run the appropriate worker
echo "Running $WORKER_TYPE worker..."
dotnet run -- $WORKER_TYPE