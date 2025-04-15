# workflows.py
from temporalio import workflow
from temporalio.common import RetryPolicy
from datetime import timedelta

# Import shared objects and activity interfaces
from app.models.shared import DocumentInput, WorkflowResult, GeminiActivities, AzureOpenAIActivities, DocumentIntelligenceActivities, OcrActivityResult

with workflow.unsafe.imports_passed_through():
    # Import implementations
    from app.activities.gemini_activities import GeminiActivitiesImpl
    from app.activities.azure_activities import AzureOpenAIActivitiesImpl
    from app.activities.document_intelligence_activities import DocumentIntelligenceActivitiesImpl

@workflow.defn
class DocumentProcessingWorkflow:
    @workflow.run
    async def run(self, doc_input: DocumentInput, use_azure: bool = False) -> WorkflowResult:
        workflow.logger.info(f"Starting workflow for document: {doc_input.file_path} using {'Azure OpenAI' if use_azure else 'Gemini'}")
        
        # Configure retries for activities
        doc_intelligence_retry_policy = RetryPolicy(
            maximum_attempts=3,
            initial_interval=timedelta(seconds=5),
            maximum_interval=timedelta(seconds=30),
            non_retryable_error_types=["FileNotFoundError", "ValueError"],
        )
        
        summary_retry_policy = RetryPolicy(
            maximum_attempts=3,
            initial_interval=timedelta(seconds=15),
            maximum_interval=timedelta(minutes=2),
            non_retryable_error_types=["ValueError"],
        )

        # Choose which activity interface to use for LLM processing
        activity_interface = AzureOpenAIActivities if use_azure else GeminiActivities

        # Step 1: Document Intelligence OCR
        workflow.logger.info("Starting Document Intelligence processing")
        doc_intelligence_result = await workflow.execute_activity(
            DocumentIntelligenceActivitiesImpl.process_document,
            doc_input,
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=doc_intelligence_retry_policy,
        )
        workflow.logger.info(f"Document Intelligence completed with confidence: {doc_intelligence_result.confidence:.2f}")
        
        # Create an OCR result from Document Intelligence result to pass to the LLM
        ocr_result = OcrActivityResult(full_text=doc_intelligence_result.full_text)
        
        # Add metadata about the document to the text if there are tables or entities
        if doc_intelligence_result.tables or doc_intelligence_result.entities:
            workflow.logger.info(f"Document has {len(doc_intelligence_result.tables)} tables and {len(doc_intelligence_result.entities)} entities")
            
            # Optional: We could enrich the OCR text with structured metadata from Document Intelligence
            # This would help the LLM better understand the document structure
        
        workflow.logger.info("OCR step completed.")

        # Step 2: Execute Summarization Activity with the OCR result
        summarization_result = await workflow.execute_activity_method(
            activity_interface.perform_azure_summarization if use_azure else activity_interface.perform_summarization,
            ocr_result,
            start_to_close_timeout=timedelta(minutes=3),
            retry_policy=summary_retry_policy,
        )
        workflow.logger.info("Summarization Activity completed.")

        # Step 3: Return Combined Result
        workflow.logger.info("Workflow finished successfully.")
        return WorkflowResult(
            ocr_text=ocr_result.full_text,
            summary=summarization_result.summary_json
        )