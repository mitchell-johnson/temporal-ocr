import os
import uuid
import asyncio
import logging
from flask import Flask, request, render_template, jsonify, redirect, url_for, flash, session
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from temporalio.client import Client
from temporalio.contrib.pydantic import pydantic_data_converter

# Load environment variables
load_dotenv(override=True)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import the workflow interface and input object
from app.workflows.workflow_runner import start_document_workflow
from app.models.shared import DocumentInput

# Initialize Flask app
app = Flask(__name__, 
            template_folder='../web/templates',
            static_folder='../web/static')
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key')

# Configure upload folder
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    # Check if a file was submitted
    if 'file' not in request.files:
        flash('No file part', 'error')
        return redirect(request.url)
    
    file = request.files['file']
    
    # If the user does not select a file, the browser submits an empty file
    if file.filename == '':
        flash('No selected file', 'error')
        return redirect(request.url)
    
    if file and allowed_file(file.filename):
        # Secure filename and save file
        filename = secure_filename(file.filename)
        unique_filename = f"{str(uuid.uuid4())}_{filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(file_path)
        
        # Store path in session for processing
        session['uploaded_file_path'] = file_path
        session['original_filename'] = filename
        
        # Determine which model to use
        use_azure = 'use_azure' in request.form and request.form['use_azure'] == 'on'
        session['use_azure'] = use_azure
        
        # Redirect to processing route
        return redirect(url_for('process_file'))
    
    flash('Invalid file type. Allowed types: PNG, JPG, JPEG, GIF, PDF', 'error')
    return redirect(url_for('index'))

@app.route('/process')
def process_file():
    # Get file path from session
    file_path = session.get('uploaded_file_path')
    if not file_path:
        flash('No file uploaded', 'error')
        return redirect(url_for('index'))
    
    use_azure = session.get('use_azure', False)
    
    # Call the async function to start the workflow
    try:
        # Create an event loop in the context of this request
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Run the async workflow
        result = loop.run_until_complete(start_document_workflow(file_path, use_azure))
        
        # Close the loop
        loop.close()
        
        # Store result in session
        session['result'] = {
            'ocr_text': result.ocr_text[:5000],  # Truncate for session storage
            'summary': result.summary,
            'original_filename': session.get('original_filename', 'unknown')
        }
        
        # Clean up the file if needed
        # os.remove(file_path)
        
        return redirect(url_for('show_result'))
        
    except Exception as e:
        logger.error(f"Error processing file: {e}", exc_info=True)
        flash(f"Error processing file: {str(e)}", 'error')
        return redirect(url_for('index'))

@app.route('/result')
def show_result():
    result = session.get('result')
    if not result:
        flash('No results to display', 'error')
        return redirect(url_for('index'))
    
    return render_template('result.html', result=result)

@app.route('/health')
def health_check():
    """Health check endpoint for Cloud Run"""
    return jsonify({"status": "healthy"})

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=True) 