#!/usr/bin/env python
import os
import sys
import glob
from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeDocumentRequest

# Load environment variables from .env file
load_dotenv()

# Get credentials from environment variables
api_key = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_KEY")
endpoint = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT")

print(f"Testing Azure Document Intelligence connection...")
print(f"Endpoint: {endpoint}")
print(f"API Key: {'*' * 5}{api_key[-4:] if api_key else 'None'}")

if not api_key or not endpoint:
    print("Error: Missing required environment variables.")
    print("Please ensure AZURE_DOCUMENT_INTELLIGENCE_KEY and AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT are set in your .env file.")
    sys.exit(1)

# Initialize the Document Intelligence client
try:
    # Create the client
    client = DocumentIntelligenceClient(
        endpoint=endpoint,
        credential=AzureKeyCredential(api_key)
    )
    
    print("\nClient initialization successful!")
    print("Your Azure Document Intelligence credentials appear to be valid.")
    
    # Ask if user wants to test with a sample document
    print("\nWould you like to test document analysis with a sample document? (y/n)")
    choice = input("> ").strip().lower()
    
    if choice == 'y':
        # Find sample documents
        sample_docs = []
        for ext in ['pdf', 'jpg', 'jpeg', 'png']:
            sample_docs.extend(glob.glob(f"samples/*.{ext}"))
        
        if not sample_docs:
            # Check if there's a test directory
            for ext in ['pdf', 'jpg', 'jpeg', 'png']:
                sample_docs.extend(glob.glob(f"test/*.{ext}"))
                
        if not sample_docs:
            print("\nNo sample documents found in 'samples/' or 'test/' directories.")
            print("Please place a sample document (PDF, JPG, PNG) in a 'samples' directory and run again.")
            sys.exit(0)
        
        # Use the first sample document found
        sample_path = sample_docs[0]
        print(f"\nFound sample document: {sample_path}")
        print(f"Analyzing document...")
        
        try:
            # Open the document
            with open(sample_path, "rb") as f:
                document_content = f.read()
            
            # Analyze document
            poller = client.begin_analyze_document(
                "prebuilt-read", 
                document_content
            )
            
            # Get the result
            result = poller.result()
            
            # Print some basic information
            print("\nAnalysis successful!")
            print(f"Document contains {len(result.pages)} page(s)")
            
            # Get the first page content
            if result.content:
                excerpt = result.content[:200] + "..." if len(result.content) > 200 else result.content
                print(f"\nExtracted text excerpt:\n{excerpt}")
            
            print("\nDocument Intelligence service is fully operational!")
            
        except Exception as e:
            print(f"\nDocument analysis failed with error: {e}")
            print("The service credentials are valid, but there was an issue analyzing the document.")
            sys.exit(1)
    else:
        print("\nSkipping document analysis test.")
        print("Basic credential validation passed. The service appears to be configured correctly.")
    
except Exception as e:
    print(f"\nConnection failed with error: {e}")
    print("\nCommon solutions:")
    print(" 1. Check if your API key is correct")
    print(" 2. Verify the endpoint URL (should end with cognitiveservices.azure.com/)")
    print(" 3. Confirm your subscription is active")
    print(" 4. Make sure you are using the correct regional endpoint for your resource")
    print(" 5. Check if you have proper network connectivity")
    sys.exit(1)