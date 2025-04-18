#!/usr/bin/env python
import asyncio
import os
import sys
import json
from dotenv import load_dotenv
import uuid

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Import the workflow runner
from app.workflows.workflow_runner import start_document_workflow

# Load environment variables from .env file
load_dotenv()

async def run_test():
    """Run a test of the document workflow with a sample document"""
    # Select a sample document (PDF) from the uploads directory
    test_document = "app/uploads/9c5c7d7a-85e8-4dbf-b2fe-bb30c979e637_FishingLicence_192589.pdf"
    
    # Ensure the test document exists
    if not os.path.exists(test_document):
        print(f"Error: Test document not found: {test_document}")
        print("Available files in uploads directory:")
        for file in os.listdir("app/uploads"):
            if file.endswith(".pdf") or file.endswith(".png"):
                print(f"  - app/uploads/{file}")
        return
    
    print(f"Starting workflow with document: {test_document}")
    
    try:
        # Create the workflow ID here to make error messages more helpful
        workflow_id = f"doc-processing-{os.path.basename(test_document)}-{uuid.uuid4()}"
        print(f"Using workflow ID: {workflow_id}")
        
        # Run the workflow
        print("Starting workflow execution...")
        result = await start_document_workflow(test_document, workflow_id=workflow_id)
        
        # Display the results
        print("\n----- WORKFLOW RESULTS -----\n")
        
        # Display summary
        print("=== SUMMARY ===")
        print(result.summary)
        print()
        
        # Display validation results
        print("=== VALIDATION ===")
        print(f"Is accurate: {result.validation_result.is_accurate}")
        
        # Display suggested improvements
        if result.validation_result.suggested_improvements:
            print("\nSuggested improvements:")
            for idx, improvement in enumerate(result.validation_result.suggested_improvements, 1):
                print(f"{idx}. {improvement}")
        
        # Display improved summary if available
        if result.validation_result.improved_summary:
            print("\nImproved summary:")
            print(result.validation_result.improved_summary)
        
        # Display markdown (truncated for readability)
        print("\n=== MARKDOWN (first 500 characters) ===")
        print(result.markdown_content[:500] + "...")
        
        # Save the output to a file
        output_file = "workflow_result.json"
        with open(output_file, "w") as f:
            # Convert the Pydantic model to a dictionary
            result_dict = {
                "markdown_content": result.markdown_content,
                "summary": result.summary,
                "validation_result": {
                    "is_accurate": result.validation_result.is_accurate,
                    "suggested_improvements": result.validation_result.suggested_improvements,
                    "improved_summary": result.validation_result.improved_summary
                }
            }
            json.dump(result_dict, f, indent=2)
        
        print(f"\nFull results saved to {output_file}")
        
    except Exception as e:
        print(f"Error running workflow: {e}")
        print("\nDetailed error information:")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run_test()) 