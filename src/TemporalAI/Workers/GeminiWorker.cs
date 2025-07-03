// AIDEV-NOTE: Dedicated Gemini worker for Temporal workflows
using System;
using System.Threading.Tasks;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Temporalio.Client;
using Temporalio.Worker;
using TemporalAI.Activities;
using TemporalAI.Models;

namespace TemporalAI.Workers
{
    /// <summary>
    /// Worker responsible for handling Gemini AI activities
    /// </summary>
    public class GeminiWorker
    {
        private static readonly string TaskQueue = "gemini-ai-queue";
        
        public static async Task RunAsync(string[] args)
        {
            // Set up dependency injection
            var services = new ServiceCollection();
            services.AddLogging(builder => builder.AddConsole());
            services.AddSingleton<GeminiActivities>();
            
            var serviceProvider = services.BuildServiceProvider();
            var logger = serviceProvider.GetRequiredService<ILogger<GeminiWorker>>();
            
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
                
                // Create activity implementation
                var activities = serviceProvider.GetRequiredService<GeminiActivities>();
                
                // Create worker
                using var worker = new TemporalWorker(
                    client,
                    new TemporalWorkerOptions(TaskQueue)
                    {
                        MaxConcurrentActivityExecutions = 10
                    }
                );
                
                // Register activities
                worker.RegisterActivity(activities.ProcessRequestAsync);
                
                logger.LogInformation("Gemini Worker started, listening on task queue '{TaskQueue}'", TaskQueue);
                logger.LogInformation("Connected to Temporal at: {Host}", temporalHost);
                
                // Run the worker
                await worker.ExecuteAsync();
            }
            catch (Exception ex)
            {
                logger.LogError(ex, "Error running Gemini worker");
                throw;
            }
        }
    }
}