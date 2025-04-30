# OCR Web Service

This project provides a web-based document processing service that uses AI services (Google Gemini or Azure OpenAI) to perform OCR and text summarization on images and PDFs.

## Features

- **Web UI**: Upload documents through a user-friendly interface
- **OCR Processing**: Extract text from images using either Google's Gemini or Azure OpenAI
- **Text Summarization**: Generate concise summaries and keywords from extracted text
- **Direct API Integration**: Simple and direct calls to AI APIs from the backend
- **Multi-Provider Support**: Choose between Gemini or Azure OpenAI for document processing, with ability to use different models for different functions
- **Docker Support**: Easy deployment with Docker Compose or to Google Cloud Run

## Prerequisites

- Python 3.9+
- Docker and Docker Compose for local development
- API keys for:
  - Google Gemini API
  - Azure OpenAI (with vision capabilities)

## Local Development Setup

1. **Clone the repository**:
   ```bash
   git clone git@github.com:mitchell-johnson/ocr.git
   cd ocr
   ```

2. **Configure environment variables**:
   Create a `.env` file in the project root with your API credentials:

   ```
   GEMINI_API_KEY=your_gemini_api_key
   AZURE_OPENAI_API_KEY=your_azure_api_key
   AZURE_OPENAI_ENDPOINT=your_azure_endpoint
   AZURE_OPENAI_MODEL_NAME=your_model_name
   FLASK_SECRET_KEY=your_secret_key
   # Optional - specify different models for different functions
   AZURE_OPENAI_OCR_MODEL=your_vision_model
   AZURE_OPENAI_SUMMARY_MODEL=your_gpt4_model
   AZURE_OPENAI_VALIDATION_MODEL=your_gpt35_model
   ```

3. **Start the service with Docker Compose**:
   ```bash
   docker-compose up
   ```

   This will start the web application.

4. **Access the application**:
   - Web UI: http://localhost:8000

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

3. **Start the Web Application**:
   ```bash
   python app.py
   ```

## Deployment to Google Cloud Run

This application is ready to deploy to Google Cloud Run with minimal configuration.

1. **Build and push the Docker image**:
   ```bash
   gcloud builds submit --tag gcr.io/[YOUR_PROJECT_ID]/ocr
   ```

2. **Deploy to Cloud Run**:
   ```bash
   gcloud run deploy ocr \
     --image gcr.io/[YOUR_PROJECT_ID]/ocr \
     --platform managed \
     --region [REGION] \
     --allow-unauthenticated \
     --set-env-vars="GEMINI_API_KEY=your-key,FLASK_SECRET_KEY=your-key,AZURE_OPENAI_API_KEY=your-key,AZURE_OPENAI_ENDPOINT=your-endpoint,AZURE_OPENAI_MODEL_NAME=your-model"
   ```

## Project Structure

- `/app`: Main application package
  - `/api`: Web API and Flask application
  - `/services`: Implementation of AI services
  - `/models`: Shared data models and interfaces
  - `/web`: Web UI components (templates and static files)
  - `/uploads`: Temporary storage for uploaded files
- `/scripts`: Utility scripts
- `/data`: Data files (gitignored)
- `/docs`: Documentation and example files
  - `fishinglicence.png`: Sample image for testing
  - `result_screenshot.png`: Screenshot of the application
- `/deploy`: Deployment configuration
- `app.py`: Application entry point
- `Dockerfile`: Container configuration for deployment
- `docker-compose.yml`: Local development environment setup

## License

MIT License 