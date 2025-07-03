#!/bin/bash
# AIDEV-NOTE: Script to run workflow tests against Docker-hosted Temporal

# Check if .NET is installed
if ! command -v dotnet &> /dev/null; then
    echo "Error: .NET SDK is not installed. Please install .NET 8 SDK to run tests."
    exit 1
fi

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
else
    echo "Error: .env file not found."
    exit 1
fi

# Set Temporal host to connect to Docker container
export TEMPORAL_HOST=localhost:7233

echo "Running AI Workflow Tests..."
echo "Connecting to Temporal at: $TEMPORAL_HOST"
echo ""

# Run the test program
dotnet run -- test 