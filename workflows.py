# workflows.py
from temporalio import workflow
from temporalio.common import RetryPolicy
from datetime import timedelta

# Import shared objects and activity interfaces
from shared import DocumentInput, WorkflowResult, GeminiActivities, AzureOpenAIActivities

with workflow.unsafe.imports_passed_through():
    # Import implementations
    from gemini_activities import GeminiActivitiesImpl
    from azure_activities import AzureOpenAIActivitiesImpl

@workflow.defn
class DocumentProcessingWorkflow:
    @workflow.run
    async def run(self, doc_input: DocumentInput, use_azure: bool = False) -> WorkflowResult:
        workflow.logger.info(f"Starting workflow for document: {doc_input.file_path} using {'Azure OpenAI' if use_azure else 'Gemini'}")

        # Configure retries for activities (adjust as needed)
        ocr_retry_policy = RetryPolicy(
            maximum_attempts=3,
            initial_interval=timedelta(seconds=10),
            maximum_interval=timedelta(minutes=1),
            non_retryable_error_types=["FileNotFoundError", "ValueError"], # Don't retry if file missing or bad config
        )
        summary_retry_policy = RetryPolicy(
            maximum_attempts=3,
            initial_interval=timedelta(seconds=15),
            maximum_interval=timedelta(minutes=2),
             non_retryable_error_types=["ValueError"], # Don't retry if config wrong
        )

        # Choose which activity interface to use
        activity_interface = AzureOpenAIActivities if use_azure else GeminiActivities

        # --- Step 1: Execute OCR Activity ---
        ocr_result = await workflow.execute_activity_method(
            activity_interface.perform_azure_ocr if use_azure else activity_interface.perform_ocr, # Use correct method based on provider
            doc_input,
            start_to_close_timeout=timedelta(minutes=5), # Adjust timeout based on expected OCR time
            retry_policy=ocr_retry_policy,
        )
        workflow.logger.info("OCR Activity completed.")

        # --- Step 2: Execute Summarization Activity ---
        # The output 'ocr_result' from the first activity is passed as input here
        summarization_result = await workflow.execute_activity_method(
            activity_interface.perform_azure_summarization if use_azure else activity_interface.perform_summarization, # Use correct method based on provider
            ocr_result, # Pass the result from the OCR step
            start_to_close_timeout=timedelta(minutes=3), # Adjust timeout
            retry_policy=summary_retry_policy,
        )
        workflow.logger.info("Summarization Activity completed.")

        # --- Step 3: Return Combined Result ---
        workflow.logger.info("Workflow finished successfully.")
        return WorkflowResult(
            ocr_text=ocr_result.full_text,
            summary=summarization_result.summary_json
        )