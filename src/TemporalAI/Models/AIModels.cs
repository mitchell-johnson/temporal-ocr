// AIDEV-NOTE: Generic AI models for Temporal workflows with Gemini, OpenAI, and Anthropic
using System;
using System.Collections.Generic;
using Temporalio.Activities;

namespace TemporalAI.Models
{
    /// <summary>
    /// Generic request model for AI activities
    /// </summary>
    public record AIRequest
    {
        public required string Prompt { get; init; }
        public string? FilePath { get; init; }
        public Dictionary<string, object>? Parameters { get; init; }
    }

    /// <summary>
    /// Generic response model from AI activities
    /// </summary>
    public record AIResponse
    {
        public required string Content { get; init; }
        public required string ModelUsed { get; init; }
        public int? TokensUsed { get; init; }
        public Dictionary<string, object>? Metadata { get; init; }
    }

    /// <summary>
    /// Input for workflows that use multiple AI providers
    /// </summary>
    public record MultiAIWorkflowInput
    {
        public required string InitialPrompt { get; init; }
        public string? FilePath { get; init; }
        public List<string> Providers { get; init; } = new() { "gemini", "openai", "anthropic" };
    }

    /// <summary>
    /// Result from workflows using multiple AI providers
    /// </summary>
    public record MultiAIWorkflowResult
    {
        public required Dictionary<string, AIResponse> Results { get; init; }
        public string? Consensus { get; init; }
        public string? Analysis { get; init; }
    }

    /// <summary>
    /// Activity interface for Gemini AI
    /// </summary>
    public interface IGeminiActivities
    {
        [Activity]
        Task<AIResponse> ProcessRequestAsync(AIRequest request);
    }

    /// <summary>
    /// Activity interface for OpenAI
    /// </summary>
    public interface IOpenAIActivities
    {
        [Activity]
        Task<AIResponse> ProcessRequestAsync(AIRequest request);
    }

    /// <summary>
    /// Activity interface for Anthropic
    /// </summary>
    public interface IAnthropicActivities
    {
        [Activity]
        Task<AIResponse> ProcessRequestAsync(AIRequest request);
    }
}