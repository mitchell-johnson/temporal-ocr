// AIDEV-NOTE: Main entry point for TemporalAI workers
using System;
using System.Threading.Tasks;
using TemporalAI.Workers;

namespace TemporalAI
{
    /// <summary>
    /// Main program entry point that launches different workers based on command line arguments
    /// </summary>
    class Program
    {
        static async Task<int> Main(string[] args)
        {
            if (args.Length == 0)
            {
                PrintUsage();
                return 1;
            }

            var workerType = args[0].ToLower();

            try
            {
                switch (workerType)
                {
                    case "gemini":
                        await GeminiWorker.RunAsync(args);
                        break;
                    case "openai":
                        await OpenAIWorker.RunAsync(args);
                        break;
                    case "anthropic":
                        await AnthropicWorker.RunAsync(args);
                        break;
                    case "workflow":
                        await WorkflowWorker.RunAsync(args);
                        break;
                    case "all":
                        await RunAllWorkers();
                        break;
                    case "test":
                        await TestWorkflows.RunTestsAsync();
                        break;
                    default:
                        Console.WriteLine($"Unknown worker type: {workerType}");
                        PrintUsage();
                        return 1;
                }

                return 0;
            }
            catch (Exception ex)
            {
                Console.Error.WriteLine($"Fatal error: {ex.Message}");
                Console.Error.WriteLine(ex.StackTrace);
                return 1;
            }
        }

        private static void PrintUsage()
        {
            Console.WriteLine("Usage: dotnet run <worker-type>");
            Console.WriteLine();
            Console.WriteLine("Available worker types:");
            Console.WriteLine("  gemini    - Run the Gemini AI worker");
            Console.WriteLine("  openai    - Run the OpenAI worker");
            Console.WriteLine("  anthropic - Run the Anthropic worker");
            Console.WriteLine("  workflow  - Run the workflow worker");
            Console.WriteLine("  all       - Run all workers (for development)");
            Console.WriteLine("  test      - Run workflow tests");
            Console.WriteLine();
            Console.WriteLine("Environment variables:");
            Console.WriteLine("  TEMPORAL_HOST     - Temporal server address (default: localhost:7233)");
            Console.WriteLine("  GEMINI_API_KEY    - Google Gemini API key (required for Gemini worker)");
            Console.WriteLine("  OPENAI_API_KEY    - OpenAI API key (required for OpenAI worker)");
            Console.WriteLine("  ANTHROPIC_API_KEY - Anthropic API key (required for Anthropic worker)");
        }

        private static async Task RunAllWorkers()
        {
            // In production, each worker should run in its own process
            // This is just for development convenience
            var tasks = new[]
            {
                Task.Run(() => GeminiWorker.RunAsync(Array.Empty<string>())),
                Task.Run(() => OpenAIWorker.RunAsync(Array.Empty<string>())),
                Task.Run(() => AnthropicWorker.RunAsync(Array.Empty<string>())),
                Task.Run(() => WorkflowWorker.RunAsync(Array.Empty<string>()))
            };

            Console.WriteLine("Running all workers. Press Ctrl+C to stop...");
            await Task.WhenAll(tasks);
        }
    }
}