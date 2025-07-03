// AIDEV-NOTE: Workflow worker that handles AI workflow orchestration
using System;
using System.Threading.Tasks;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Temporalio.Client;
using Temporalio.Worker;
using TemporalAI.Workflows;

namespace TemporalAI.Workers
{
    /// <summary>
    /// Worker responsible for handling workflow execution
    /// </summary>
    public class WorkflowWorker
    {
        private static readonly string TaskQueue = "ai-workflow-queue";
        
        public static async Task RunAsync(string[] args)
        {
            // Set up dependency injection
            var services = new ServiceCollection();
            services.AddLogging(builder => builder.AddConsole());
            
            var serviceProvider = services.BuildServiceProvider();
            var logger = serviceProvider.GetRequiredService<ILogger<WorkflowWorker>>();
            
            // Get Temporal host from environment
            var temporalHost = Environment.GetEnvironmentVariable("TEMPORAL_HOST") ?? "localhost:7233";
            
            try
            {
                // Connect to Temporal server
                logger.LogInformation("Connecting to Temporal at {Host}...", temporalHost);
                var client = await TemporalClient.ConnectAsync(new TemporalClientConnectOptions
                {
                    TargetHost = temporalHost
                });
                
                // Create worker with options
                var options = new TemporalWorkerOptions(TaskQueue)
                    .AddWorkflow<AIConsensusWorkflow>()
                    .AddWorkflow<AIChainWorkflow>()
                    .AddWorkflow<AISpecialistWorkflow>();
                
                using var worker = new TemporalWorker(client, options);
                
                logger.LogInformation("Workflow Worker started, listening on task queue '{TaskQueue}'", TaskQueue);
                logger.LogInformation("Connected to Temporal at: {Host}", temporalHost);
                logger.LogInformation("Registered workflows:");
                logger.LogInformation("- ai-consensus-workflow");
                logger.LogInformation("- ai-chain-workflow");
                logger.LogInformation("- ai-specialist-workflow");
                
                // Run the worker with cancellation token
                var cts = new System.Threading.CancellationTokenSource();
                Console.CancelKeyPress += (_, e) =>
                {
                    e.Cancel = true;
                    cts.Cancel();
                };
                
                await worker.ExecuteAsync(cts.Token);
            }
            catch (Exception ex)
            {
                logger.LogError(ex, "Error running workflow worker");
                throw;
            }
        }
    }
}