# Temporal OCR Web Service

This project provides a web-based document processing service that uses Temporal and AI services (Google Gemini or Azure OpenAI) to perform OCR and text summarization on images and PDFs.

## Features

- **Web UI**: Upload documents through a user-friendly interface
- **OCR Processing**: Extract text from images using either Google's Gemini or Azure OpenAI
- **Text Summarization**: Generate concise summaries and keywords from extracted text
- **Temporal Workflow**: Reliable, fault-tolerant processing with automatic retries
- **Multi-Provider Support**: Switch between Gemini and Azure OpenAI with a checkbox
- **Docker Support**: Easy deployment with Docker Compose or to Google Cloud Run

## Prerequisites

- Python 3.9+
- Docker and Docker Compose for local development
- API keys for either:
  - Google Gemini API
  - Azure OpenAI (with vision capabilities)

## Local Development Setup

1. **Clone the repository**:
   ```bash
   git clone git@github.com:mitchell-johnson/temporal-ocr.git
   cd temporal-ocr
   ```

2. **Configure environment variables**:
   Create a `.env` file in the project root with your API credentials:

   ```
   GEMINI_API_KEY=your_gemini_api_key
   AZURE_OPENAI_API_KEY=your_azure_api_key
   AZURE_OPENAI_ENDPOINT=your_azure_endpoint
   AZURE_OPENAI_MODEL_NAME=your_model_name
   FLASK_SECRET_KEY=your_secret_key
   ```

3. **Start the services with Docker Compose**:
   ```bash
   docker-compose up
   ```

   This will start:
   - Temporal server and UI
   - The web application
   - The worker process
   - Supporting services (Cassandra)

4. **Access the application**:
   - Web UI: http://localhost:8000
   - Temporal UI: http://localhost:8080

## Manual Setup (Without Docker)

1. **Create and activate a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Start Temporal Server**:
   Follow the [Temporal documentation](https://docs.temporal.io/clusters/quick-install/) to install and start the Temporal server.

4. **Start the Worker**:
   ```bash
   python -m app.run_worker
   ```

5. **Start the Web Application**:
   ```bash
   python app.py
   ```

## Deployment to Google Cloud Run

This application is ready to deploy to Google Cloud Run with minimal configuration.

1. **Build and push the Docker image**:
   ```bash
   gcloud builds submit --tag gcr.io/[YOUR_PROJECT_ID]/temporal-ocr
   ```

2. **Deploy to Cloud Run**:
   ```bash
   gcloud run deploy temporal-ocr \
     --image gcr.io/[YOUR_PROJECT_ID]/temporal-ocr \
     --platform managed \
     --region [REGION] \
     --allow-unauthenticated \
     --set-env-vars="TEMPORAL_HOST=your-temporal-host,GEMINI_API_KEY=your-key,FLASK_SECRET_KEY=your-key"
   ```

3. **Note on Temporal**: For production use, you'll need to set up a Temporal server or use Temporal Cloud.

## Project Structure

- `/app`: Main application package
  - `/api`: Web API and Flask application
  - `/activities`: Implementation of OCR and summarization activities
  - `/models`: Shared data models and interfaces
  - `/workflows`: Temporal workflow definitions
  - `/web`: Web UI components (templates and static files)
  - `/uploads`: Temporary storage for uploaded files
  - `run_worker.py`: Worker process implementation
- `/scripts`: Utility scripts
  - `list_gemini_models.py`: Script to list available Gemini models
  - `start_workflow.py`: Script to manually start a workflow
- `/data`: Data files (gitignored)
- `/docs`: Documentation and example files
  - `fishinglicence.png`: Sample image for testing
  - `result_screenshot.png`: Screenshot of the application
- `/deploy`: Deployment configuration
- `/dynamicconfig`: Temporal server configuration
- `app.py`: Application entry point
- `Dockerfile`: Container configuration for deployment
- `docker-compose.yml`: Local development environment setup

## License

MIT License 