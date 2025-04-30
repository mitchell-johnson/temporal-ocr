FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Copy requirements.txt
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Create directory for uploads if it doesn't exist
RUN mkdir -p app/uploads

# Environment variables
ENV PORT=8080
ENV PYTHONUNBUFFERED=1
ENV FLASK_SECRET_KEY="production-secret-key-replace-this"

# Expose the port
EXPOSE $PORT

# Start the service using gunicorn
CMD exec gunicorn --bind :$PORT --workers 2 --threads 8 --timeout 0 'app.api.app:app' 