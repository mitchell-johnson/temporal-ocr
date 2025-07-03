// AIDEV-NOTE: Test program for AI temporal workflows
using System;
using System.Collections.Generic;
using System.IO;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Newtonsoft.Json;
using Temporalio.Client;
using TemporalAI.Models;
using TemporalAI.Workflows;

namespace TemporalAI
{
    /// <summary>
    /// Test program to demonstrate running the three AI workflow examples
    /// </summary>
    public class TestWorkflows
    {
        private static readonly string TemporalHost = Environment.GetEnvironmentVariable("TEMPORAL_HOST") ?? "localhost:7233";
        
        public static async Task RunTestsAsync()
        {
            using var loggerFactory = LoggerFactory.Create(builder => builder.AddConsole());
            var logger = loggerFactory.CreateLogger<TestWorkflows>();
            
            logger.LogInformation("Connecting to Temporal...");
            var client = await TemporalClient.ConnectAsync(new TemporalClientConnectOptions
            {
                TargetHost = TemporalHost
            });
            logger.LogInformation($"Connected to Temporal at: {TemporalHost}");
            
            try
            {
                // Test all three workflows
                var consensusResult = await TestConsensusWorkflow(client, logger);
                var chainResult = await TestChainWorkflow(client, logger);
                var specialistResult = await TestSpecialistWorkflow(client, logger);
                
                // Save results
                var results = new
                {
                    consensus_workflow = new
                    {
                        analysis = consensusResult.Analysis,
                        consensus = consensusResult.Consensus,
                        provider_count = consensusResult.Results.Count
                    },
                    chain_workflow = new
                    {
                        analysis = chainResult.Analysis,
                        final_result = chainResult.Consensus?.Substring(0, Math.Min(1000, chainResult.Consensus.Length))
                    },
                    specialist_workflow = new
                    {
                        analysis = specialistResult.Analysis,
                        synthesis = specialistResult.Consensus?.Substring(0, Math.Min(1000, specialistResult.Consensus.Length))
                    }
                };
                
                var json = JsonConvert.SerializeObject(results, Formatting.Indented);
                await File.WriteAllTextAsync("ai_workflow_test_results.json", json);
                
                logger.LogInformation(new string('=', 60));
                logger.LogInformation("All tests completed successfully!");
                logger.LogInformation("Results saved to: ai_workflow_test_results.json");
                logger.LogInformation(new string('=', 60));
            }
            catch (Exception ex)
            {
                logger.LogError(ex, "Error running workflows");
                throw;
            }
        }
        
        private static async Task<MultiAIWorkflowResult> TestConsensusWorkflow(TemporalClient client, ILogger logger)
        {
            logger.LogInformation("\n" + new string('=', 60));
            logger.LogInformation("Testing AI Consensus Workflow");
            logger.LogInformation(new string('=', 60));
            
            // Prepare input
            var workflowInput = new MultiAIWorkflowInput
            {
                InitialPrompt = "What are the key considerations when building a microservices architecture?",
                Providers = new List<string> { "gemini", "openai", "anthropic" }
            };
            
            // Start workflow
            var workflowId = $"consensus-workflow-{DateTime.Now:yyyyMMdd-HHmmss}";
            var handle = await client.StartWorkflowAsync(
                (AIConsensusWorkflow wf) => wf.RunAsync(workflowInput),
                new WorkflowOptions
                {
                    Id = workflowId,
                    TaskQueue = "ai-workflow-queue"
                }
            );
            
            logger.LogInformation($"Started workflow: {handle.Id}");
            
            // Wait for result
            var result = await handle.GetResultAsync();
            
            logger.LogInformation("Workflow completed!");
            logger.LogInformation($"Analysis: {result.Analysis}");
            logger.LogInformation("Individual responses:");
            foreach (var (provider, response) in result.Results)
            {
                logger.LogInformation($"\n{provider.ToUpper()}:");
                logger.LogInformation($"- Model: {response.ModelUsed}");
                logger.LogInformation($"- Response preview: {response.Content.Substring(0, Math.Min(200, response.Content.Length))}...");
            }
            
            logger.LogInformation($"\nConsensus:\n{result.Consensus?.Substring(0, Math.Min(500, result.Consensus.Length))}...");
            
            return result;
        }
        
        private static async Task<MultiAIWorkflowResult> TestChainWorkflow(TemporalClient client, ILogger logger)
        {
            logger.LogInformation("\n" + new string('=', 60));
            logger.LogInformation("Testing AI Chain Workflow");
            logger.LogInformation(new string('=', 60));
            
            // Prepare input with a sample file
            var workflowInput = new MultiAIWorkflowInput
            {
                InitialPrompt = "Analyze the architectural patterns and provide recommendations",
                FilePath = File.Exists("docs/fishinglicence.png") ? "docs/fishinglicence.png" : null
            };
            
            // Start workflow
            var workflowId = $"chain-workflow-{DateTime.Now:yyyyMMdd-HHmmss}";
            var handle = await client.StartWorkflowAsync(
                (AIChainWorkflow wf) => wf.RunAsync(workflowInput),
                new WorkflowOptions
                {
                    Id = workflowId,
                    TaskQueue = "ai-workflow-queue"
                }
            );
            
            logger.LogInformation($"Started workflow: {handle.Id}");
            
            // Wait for result
            var result = await handle.GetResultAsync();
            
            logger.LogInformation("Workflow completed!");
            logger.LogInformation($"Analysis: {result.Analysis}");
            logger.LogInformation("Processing chain:");
            logger.LogInformation($"1. Gemini (initial): {result.Results["gemini"].Content.Substring(0, Math.Min(200, result.Results["gemini"].Content.Length))}...");
            logger.LogInformation($"2. OpenAI (refined): {result.Results["openai"].Content.Substring(0, Math.Min(200, result.Results["openai"].Content.Length))}...");
            logger.LogInformation($"3. Anthropic (final): {result.Results["anthropic"].Content.Substring(0, Math.Min(200, result.Results["anthropic"].Content.Length))}...");
            
            return result;
        }
        
        private static async Task<MultiAIWorkflowResult> TestSpecialistWorkflow(TemporalClient client, ILogger logger)
        {
            logger.LogInformation("\n" + new string('=', 60));
            logger.LogInformation("Testing AI Specialist Workflow");
            logger.LogInformation(new string('=', 60));
            
            // Prepare input
            var workflowInput = new MultiAIWorkflowInput
            {
                InitialPrompt = "Design a real-time data processing system for IoT devices",
                Providers = new List<string> { "gemini", "openai", "anthropic" }
            };
            
            // Start workflow
            var workflowId = $"specialist-workflow-{DateTime.Now:yyyyMMdd-HHmmss}";
            var handle = await client.StartWorkflowAsync(
                (AISpecialistWorkflow wf) => wf.RunAsync(workflowInput),
                new WorkflowOptions
                {
                    Id = workflowId,
                    TaskQueue = "ai-workflow-queue"
                }
            );
            
            logger.LogInformation($"Started workflow: {handle.Id}");
            
            // Wait for result
            var result = await handle.GetResultAsync();
            
            logger.LogInformation("Workflow completed!");
            logger.LogInformation($"Analysis: {result.Analysis}");
            logger.LogInformation("Specialized analyses:");
            logger.LogInformation($"- Gemini (creative/visual): {result.Results["gemini"].Content.Substring(0, Math.Min(200, result.Results["gemini"].Content.Length))}...");
            logger.LogInformation($"- OpenAI (technical): {result.Results["openai"].Content.Substring(0, Math.Min(200, result.Results["openai"].Content.Length))}...");
            logger.LogInformation($"- Anthropic (analytical): {result.Results["anthropic"].Content.Substring(0, Math.Min(200, result.Results["anthropic"].Content.Length))}...");
            logger.LogInformation($"\nSynthesized result:\n{result.Consensus?.Substring(0, Math.Min(500, result.Consensus.Length))}...");
            
            return result;
        }
    }
}