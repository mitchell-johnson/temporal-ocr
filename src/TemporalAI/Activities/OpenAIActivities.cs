// AIDEV-NOTE: Generic OpenAI activities for Temporal workflows
using System;
using System.Collections.Generic;
using System.IO;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using OpenAI;
using OpenAI.Chat;
using OpenAI.Images;
using TemporalAI.Models;
using Temporalio.Activities;

namespace TemporalAI.Activities
{
    /// <summary>
    /// Implementation of OpenAI activities
    /// </summary>
    public class OpenAIActivities : IOpenAIActivities
    {
        private readonly ILogger<OpenAIActivities> _logger;
        private readonly OpenAIClient _client;
        private readonly string _defaultModel = "gpt-4-turbo-preview";

        public OpenAIActivities(ILogger<OpenAIActivities> logger)
        {
            _logger = logger;
            
            var apiKey = Environment.GetEnvironmentVariable("OPENAI_API_KEY");
            if (string.IsNullOrEmpty(apiKey))
            {
                throw new InvalidOperationException("OPENAI_API_KEY environment variable not set.");
            }

            _client = new OpenAIClient(apiKey);
            _logger.LogInformation("OpenAI Activities initialized");
        }

        [Activity]
        public async Task<AIResponse> ProcessRequestAsync(AIRequest request)
        {
            var context = ActivityExecutionContext.Current;
            _logger.LogInformation("Processing OpenAI request with prompt: {Prompt}", 
                request.Prompt.Length > 100 ? request.Prompt.Substring(0, 100) + "..." : request.Prompt);

            try
            {
                var messages = new List<ChatMessage>();
                var model = _defaultModel;

                // Handle file input if provided
                if (!string.IsNullOrEmpty(request.FilePath))
                {
                    var fileBytes = await File.ReadAllBytesAsync(request.FilePath);
                    var mimeType = GetMimeType(request.FilePath);

                    // AIDEV-NOTE: OpenAI supports image files for vision models
                    if (mimeType.StartsWith("image/"))
                    {
                        var base64Image = Convert.ToBase64String(fileBytes);
                        var imageUrl = $"data:{mimeType};base64,{base64Image}";
                        
                        messages.Add(new UserChatMessage(
                            new List<ChatMessageContentPart>
                            {
                                ChatMessageContentPart.CreateTextMessageContentPart(request.Prompt),
                                ChatMessageContentPart.CreateImageMessageContentPart(
                                    new Uri(imageUrl),
                                    ImageChatMessageContentPartDetail.Auto
                                )
                            }
                        ));
                        model = "gpt-4-vision-preview"; // Use vision model for images
                    }
                    else
                    {
                        // For non-image files, include content as text if possible
                        try
                        {
                            var fileContent = System.Text.Encoding.UTF8.GetString(fileBytes);
                            messages.Add(new UserChatMessage($"{request.Prompt}\n\nFile content:\n{fileContent}"));
                        }
                        catch
                        {
                            messages.Add(new UserChatMessage($"{request.Prompt}\n\n[Binary file provided: {request.FilePath}]"));
                        }
                    }
                }
                else
                {
                    messages.Add(new UserChatMessage(request.Prompt));
                }

                // Apply custom parameters
                var temperature = 0.7f;
                var maxTokens = 4096;

                if (request.Parameters != null)
                {
                    if (request.Parameters.TryGetValue("temperature", out var tempValue) && tempValue is double temp)
                        temperature = (float)temp;
                    if (request.Parameters.TryGetValue("max_tokens", out var tokensValue) && tokensValue is int tokens)
                        maxTokens = tokens;
                    if (request.Parameters.TryGetValue("model", out var modelValue) && modelValue is string modelName)
                        model = modelName;
                }

                // Create chat options
                var options = new ChatCompletionOptions
                {
                    Temperature = temperature,
                    MaxTokens = maxTokens
                };

                // Make API call
                var chatClient = _client.GetChatClient(model);
                var response = await chatClient.CompleteChatAsync(messages, options);
                var completion = response.Value;

                return new AIResponse
                {
                    Content = completion.Content[0].Text,
                    ModelUsed = model,
                    TokensUsed = completion.Usage?.TotalTokens,
                    Metadata = new Dictionary<string, object>
                    {
                        ["finish_reason"] = completion.FinishReason.ToString(),
                        ["prompt_tokens"] = completion.Usage?.InputTokens ?? 0,
                        ["completion_tokens"] = completion.Usage?.OutputTokens ?? 0
                    }
                };
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error processing OpenAI request");
                throw;
            }
        }

        private static string GetMimeType(string filePath)
        {
            var extension = Path.GetExtension(filePath).ToLowerInvariant();
            return extension switch
            {
                ".jpg" or ".jpeg" => "image/jpeg",
                ".png" => "image/png",
                ".gif" => "image/gif",
                ".webp" => "image/webp",
                ".pdf" => "application/pdf",
                ".txt" => "text/plain",
                ".json" => "application/json",
                ".xml" => "application/xml",
                _ => "application/octet-stream"
            };
        }
    }
}