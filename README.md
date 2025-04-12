# Temporal OCR Document Processing

This project demonstrates a document processing workflow using Temporal and AI services (Gemini or Azure OpenAI) to perform OCR and text summarization on images.

## Features

- **OCR Processing**: Extract text from images using either Google's Gemini or Azure OpenAI
- **Text Summarization**: Generate concise summaries and keywords from extracted text
- **Temporal Workflow**: Reliable, fault-tolerant processing with automatic retries
- **Multi-Provider Support**: Switch between Gemini and Azure OpenAI with a simple flag

## Prerequisites

- Python 3.9+
- Docker and Docker Compose
- API keys for either:
  - Google Gemini API
  - Azure OpenAI (with vision capabilities)

## Setup

1. **Clone the repository**:
   ```bash
   git clone git@github.com:mitchell-johnson/temporal-ocr.git
   cd temporal-ocr
   ```

2. **Create and activate a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**:
   Create a `.env` file in the project root with your API credentials:

   For Gemini:
   ```
   GEMINI_API_KEY=your_gemini_api_key
   ```

   For Azure OpenAI:
   ```
   AZURE_OPENAI_API_KEY=your_azure_api_key
   AZURE_OPENAI_ENDPOINT=your_azure_endpoint
   AZURE_OPENAI_MODEL_NAME=your_deployment_name
   ```

5. **Start Temporal Server**:
   First, download the Temporal server Docker Compose file:
   ```bash
   curl -L https://temporal.io/docker-compose.yml -o docker-compose.yml
   ```

   Then start the server:
   ```bash
   docker compose up -d
   ```

   This will start the Temporal server in development mode with:
   - Web UI at http://localhost:8233
   - gRPC endpoint at localhost:7233
   - PostgreSQL for persistence
   - Elasticsearch for visibility (optional)

   You can verify the server is running with:
   ```bash
   docker compose ps
   ```

   To stop the server:
   ```bash
   docker compose down
   ```
## Usage

1. **Start the Worker**:
   In one terminal, run:
   ```bash
   python run_worker.py
   ```

2. **Process a Document**:
   In another terminal, run:
   ```bash
   python start_workflow.py --azure  # Use Azure OpenAI
   # or
   python start_workflow.py  # Use Gemini (default)
   ```

   The workflow will:
   - Extract text from the image using OCR
   - Generate a summary and keywords
   - Return the results

## Project Structure

- `workflows.py`: Defines the Temporal workflow
- `gemini_activities.py`: Implementation of Gemini-based activities
- `azure_activities.py`: Implementation of Azure OpenAI-based activities
- `shared.py`: Shared data models and interfaces
- `run_worker.py`: Worker process that executes workflows and activities
- `start_workflow.py`: Client that starts the workflow

## Troubleshooting

- Ensure the Temporal server is running (`docker compose ps`)
- Check your API keys are correctly set in `.env`
- Verify the worker is connected to the correct task queue
- Check logs for specific error messages

## License

MIT License 