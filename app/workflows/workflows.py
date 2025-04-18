# workflows.py
from temporalio import workflow
from temporalio.common import RetryPolicy
from datetime import timedelta

# Import shared objects and activity interfaces
from app.models.shared import (
    DocumentInput, 
    WorkflowResult, 
    GeminiDocumentResult,
    AzureValidationResult,
    GeminiActivities, 
    AzureOpenAIActivities
)

with workflow.unsafe.imports_passed_through():
    # Import implementations - only for type hinting, not for direct use
    from app.activities.gemini_activities import GeminiActivitiesImpl
    from app.activities.azure_activities import AzureOpenAIActivitiesImpl

@workflow.defn
class DocumentProcessingWorkflow:
    @workflow.run
    async def run(self, doc_input: DocumentInput) -> WorkflowResult:
        workflow.logger.info(f"Starting workflow for document: {doc_input.file_path}")
        
        # Configure retries for activities
        activity_retry_policy = RetryPolicy(
            maximum_attempts=3,
            initial_interval=timedelta(seconds=10),
            maximum_interval=timedelta(seconds=30),
            non_retryable_error_types=["FileNotFoundError", "ValueError"],
        )

        # Step 1: Gemini - Generate markdown and summary
        workflow.logger.info("Starting Gemini processing to generate markdown and summary")
        gemini_result = await self._execute_gemini_processing(
            doc_input, 
            activity_retry_policy
        )
        workflow.logger.info(f"Gemini processing completed. Generated markdown with {len(gemini_result.markdown_content)} characters and summary with {len(gemini_result.summary)} characters")
        
        # Step 2: Azure - Validate the summary
        workflow.logger.info("Starting Azure validation of the summary")
        validation_result = await self._execute_azure_validation(
            doc_input,
            gemini_result.summary,
            activity_retry_policy
        )
        workflow.logger.info(f"Azure validation completed. Summary is {'accurate' if validation_result.is_accurate else 'not accurate'} with {len(validation_result.suggested_improvements)} improvement suggestions")
        
        # Step 3: Return combined result
        workflow.logger.info("Workflow finished successfully")
        return WorkflowResult(
            markdown_content=gemini_result.markdown_content,
            summary=gemini_result.summary,
            validation_result=validation_result
        )
        
    async def _execute_gemini_processing(self, doc_input: DocumentInput, retry_policy: RetryPolicy) -> GeminiDocumentResult:
        """Helper method to execute Gemini processing activity"""
        return await workflow.execute_activity(
            GeminiActivities.generate_markdown_and_summary,
            doc_input,
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=retry_policy,
        )
    
    async def _execute_azure_validation(self, doc_input: DocumentInput, summary: str, retry_policy: RetryPolicy) -> AzureValidationResult:
        """Helper method to execute Azure validation activity"""
        return await workflow.execute_activity(
            AzureOpenAIActivities.validate_summary,
            args=[doc_input, summary],
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=retry_policy,
        )