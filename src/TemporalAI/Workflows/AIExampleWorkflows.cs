// AIDEV-NOTE: Example workflows demonstrating multi-AI provider patterns
using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Temporalio.Activities;
using Temporalio.Workflows;
using TemporalAI.Models;

namespace TemporalAI.Workflows
{
    /// <summary>
    /// Workflow that sends the same prompt to all three AI providers
    /// and creates a consensus response
    /// </summary>
    [Workflow("ai-consensus-workflow")]
    public class AIConsensusWorkflow
    {
        [WorkflowRun]
        public async Task<MultiAIWorkflowResult> RunAsync(MultiAIWorkflowInput input)
        {
            // AIDEV-NOTE: Execute activities in parallel for better performance
            var tasks = new List<Task<AIResponse>>();
            
            if (input.Providers.Contains("gemini"))
            {
                var geminiRequest = new AIRequest 
                { 
                    Prompt = input.InitialPrompt, 
                    FilePath = input.FilePath 
                };
                tasks.Add(Workflow.ExecuteActivityAsync<IGeminiActivities, AIResponse>(
                    a => a.ProcessRequestAsync(geminiRequest),
                    new ActivityOptions
                    {
                        TaskQueue = "gemini-ai-queue",
                        StartToCloseTimeout = TimeSpan.FromMinutes(5)
                    }
                ));
            }
            
            if (input.Providers.Contains("openai"))
            {
                var openaiRequest = new AIRequest 
                { 
                    Prompt = input.InitialPrompt, 
                    FilePath = input.FilePath 
                };
                tasks.Add(Workflow.ExecuteActivityAsync<IOpenAIActivities, AIResponse>(
                    a => a.ProcessRequestAsync(openaiRequest),
                    new ActivityOptions
                    {
                        TaskQueue = "openai-ai-queue",
                        StartToCloseTimeout = TimeSpan.FromMinutes(5)
                    }
                ));
            }
            
            if (input.Providers.Contains("anthropic"))
            {
                var anthropicRequest = new AIRequest 
                { 
                    Prompt = input.InitialPrompt, 
                    FilePath = input.FilePath 
                };
                tasks.Add(Workflow.ExecuteActivityAsync<IAnthropicActivities, AIResponse>(
                    a => a.ProcessRequestAsync(anthropicRequest),
                    new ActivityOptions
                    {
                        TaskQueue = "anthropic-ai-queue",
                        StartToCloseTimeout = TimeSpan.FromMinutes(5)
                    }
                ));
            }
            
            // Wait for all responses
            var responses = await Task.WhenAll(tasks);
            
            // Build results dictionary
            var results = new Dictionary<string, AIResponse>();
            for (int i = 0; i < input.Providers.Count; i++)
            {
                results[input.Providers[i]] = responses[i];
            }
            
            // Generate consensus using Anthropic (could be any provider)
            var consensusPrompt = "Based on these AI responses, create a consensus summary:\n\n";
            foreach (var (provider, response) in results)
            {
                consensusPrompt += $"**{provider.ToUpper()} Response:**\n{response.Content}\n\n";
            }
            consensusPrompt += "Create a balanced consensus that incorporates the best insights from all responses.";
            
            var consensusResponse = await Workflow.ExecuteActivityAsync<IAnthropicActivities, AIResponse>(
                a => a.ProcessRequestAsync(new AIRequest { Prompt = consensusPrompt }),
                new ActivityOptions
                {
                    TaskQueue = "anthropic-ai-queue",
                    StartToCloseTimeout = TimeSpan.FromMinutes(5)
                }
            );
            
            return new MultiAIWorkflowResult
            {
                Results = results,
                Consensus = consensusResponse.Content,
                Analysis = $"Processed with {input.Providers.Count} AI providers"
            };
        }
    }

    /// <summary>
    /// Workflow that chains AI providers: 
    /// Gemini analyzes -> OpenAI refines -> Anthropic validates
    /// </summary>
    [Workflow("ai-chain-workflow")]
    public class AIChainWorkflow
    {
        [WorkflowRun]
        public async Task<MultiAIWorkflowResult> RunAsync(MultiAIWorkflowInput input)
        {
            var results = new Dictionary<string, AIResponse>();
            
            // Step 1: Initial analysis with Gemini
            var geminiResponse = await Workflow.ExecuteActivityAsync<IGeminiActivities, AIResponse>(
                a => a.ProcessRequestAsync(new AIRequest
                {
                    Prompt = $"Analyze this request and provide initial insights: {input.InitialPrompt}",
                    FilePath = input.FilePath
                }),
                new ActivityOptions
                {
                    TaskQueue = "gemini-ai-queue",
                    StartToCloseTimeout = TimeSpan.FromMinutes(5)
                }
            );
            results["gemini"] = geminiResponse;
            
            // Step 2: Refinement with OpenAI
            var refinePrompt = $@"
Original request: {input.InitialPrompt}

Initial analysis from another AI:
{geminiResponse.Content}

Please refine and enhance this analysis with additional insights and improvements.";
            
            var openaiResponse = await Workflow.ExecuteActivityAsync<IOpenAIActivities, AIResponse>(
                a => a.ProcessRequestAsync(new AIRequest 
                { 
                    Prompt = refinePrompt, 
                    FilePath = input.FilePath 
                }),
                new ActivityOptions
                {
                    TaskQueue = "openai-ai-queue",
                    StartToCloseTimeout = TimeSpan.FromMinutes(5)
                }
            );
            results["openai"] = openaiResponse;
            
            // Step 3: Validation and final polish with Anthropic
            var validatePrompt = $@"
Original request: {input.InitialPrompt}

Analysis progression:
1. Initial: {geminiResponse.Content}
2. Refined: {openaiResponse.Content}

Please validate the analysis, correct any errors, and provide a final polished response.";
            
            var anthropicResponse = await Workflow.ExecuteActivityAsync<IAnthropicActivities, AIResponse>(
                a => a.ProcessRequestAsync(new AIRequest { Prompt = validatePrompt }),
                new ActivityOptions
                {
                    TaskQueue = "anthropic-ai-queue",
                    StartToCloseTimeout = TimeSpan.FromMinutes(5)
                }
            );
            results["anthropic"] = anthropicResponse;
            
            return new MultiAIWorkflowResult
            {
                Results = results,
                Consensus = anthropicResponse.Content,
                Analysis = "Sequential processing: Gemini → OpenAI → Anthropic"
            };
        }
    }

    /// <summary>
    /// Workflow that uses different AI providers for their strengths:
    /// - Gemini for vision/multimodal tasks
    /// - OpenAI for code generation
    /// - Anthropic for analysis and reasoning
    /// </summary>
    [Workflow("ai-specialist-workflow")]
    public class AISpecialistWorkflow
    {
        [WorkflowRun]
        public async Task<MultiAIWorkflowResult> RunAsync(MultiAIWorkflowInput input)
        {
            var results = new Dictionary<string, AIResponse>();
            var tasks = new List<Task<AIResponse>>();
            
            // AIDEV-NOTE: Specialized prompts for each provider based on strengths
            
            // Gemini: Best for multimodal/vision tasks
            string geminiPrompt;
            if (!string.IsNullOrEmpty(input.FilePath) && 
                (input.FilePath.EndsWith(".png", StringComparison.OrdinalIgnoreCase) ||
                 input.FilePath.EndsWith(".jpg", StringComparison.OrdinalIgnoreCase) ||
                 input.FilePath.EndsWith(".jpeg", StringComparison.OrdinalIgnoreCase) ||
                 input.FilePath.EndsWith(".gif", StringComparison.OrdinalIgnoreCase)))
            {
                geminiPrompt = $"Analyze this image in detail and {input.InitialPrompt}";
            }
            else
            {
                geminiPrompt = $"Provide a creative and comprehensive response to: {input.InitialPrompt}";
            }
            
            tasks.Add(Workflow.ExecuteActivityAsync<IGeminiActivities, AIResponse>(
                a => a.ProcessRequestAsync(new AIRequest 
                { 
                    Prompt = geminiPrompt, 
                    FilePath = input.FilePath 
                }),
                new ActivityOptions
                {
                    TaskQueue = "gemini-ai-queue",
                    StartToCloseTimeout = TimeSpan.FromMinutes(5)
                }
            ));
            
            // OpenAI: Best for code and technical tasks
            var openaiPrompt = $@"
Technical analysis requested: {input.InitialPrompt}

Please provide:
1. Technical implementation details
2. Code examples if applicable
3. Best practices and considerations";
            
            tasks.Add(Workflow.ExecuteActivityAsync<IOpenAIActivities, AIResponse>(
                a => a.ProcessRequestAsync(new AIRequest 
                { 
                    Prompt = openaiPrompt, 
                    FilePath = input.FilePath 
                }),
                new ActivityOptions
                {
                    TaskQueue = "openai-ai-queue",
                    StartToCloseTimeout = TimeSpan.FromMinutes(5)
                }
            ));
            
            // Anthropic: Best for reasoning and analysis
            var anthropicPrompt = $@"
Analytical task: {input.InitialPrompt}

Please provide:
1. Logical analysis and reasoning
2. Potential challenges and solutions
3. Strategic recommendations";
            
            tasks.Add(Workflow.ExecuteActivityAsync<IAnthropicActivities, AIResponse>(
                a => a.ProcessRequestAsync(new AIRequest 
                { 
                    Prompt = anthropicPrompt, 
                    FilePath = input.FilePath 
                }),
                new ActivityOptions
                {
                    TaskQueue = "anthropic-ai-queue",
                    StartToCloseTimeout = TimeSpan.FromMinutes(5)
                }
            ));
            
            // Execute all tasks in parallel
            var responses = await Task.WhenAll(tasks);
            
            results["gemini"] = responses[0];
            results["openai"] = responses[1];
            results["anthropic"] = responses[2];
            
            // Synthesize results
            var synthesisPrompt = $@"
Synthesize these specialized analyses into a comprehensive response:

Visual/Creative Analysis (Gemini):
{responses[0].Content}

Technical Analysis (OpenAI):
{responses[1].Content}

Strategic Analysis (Anthropic):
{responses[2].Content}

Create a unified response that leverages the strengths of each analysis.";
            
            var finalResponse = await Workflow.ExecuteActivityAsync<IAnthropicActivities, AIResponse>(
                a => a.ProcessRequestAsync(new AIRequest { Prompt = synthesisPrompt }),
                new ActivityOptions
                {
                    TaskQueue = "anthropic-ai-queue",
                    StartToCloseTimeout = TimeSpan.FromMinutes(5)
                }
            );
            
            return new MultiAIWorkflowResult
            {
                Results = results,
                Consensus = finalResponse.Content,
                Analysis = "Specialized processing: Gemini (vision/creative) + OpenAI (technical) + Anthropic (analytical)"
            };
        }
    }
}