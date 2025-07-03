// AIDEV-NOTE: Generic Anthropic Claude activities for Temporal workflows
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Text;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Newtonsoft.Json;
using TemporalAI.Models;
using Temporalio.Activities;

namespace TemporalAI.Activities
{
    /// <summary>
    /// Implementation of Anthropic Claude activities
    /// </summary>
    public class AnthropicActivities : IAnthropicActivities
    {
        private readonly ILogger<AnthropicActivities> _logger;
        private readonly HttpClient _httpClient;
        private readonly string _defaultModel = "claude-3-opus-20240229";
        private readonly string _apiKey;

        public AnthropicActivities(ILogger<AnthropicActivities> logger)
        {
            _logger = logger;
            
            _apiKey = Environment.GetEnvironmentVariable("ANTHROPIC_API_KEY");
            if (string.IsNullOrEmpty(_apiKey))
            {
                throw new InvalidOperationException("ANTHROPIC_API_KEY environment variable not set.");
            }

            _httpClient = new HttpClient
            {
                BaseAddress = new Uri("https://api.anthropic.com/v1/")
            };
            _httpClient.DefaultRequestHeaders.Add("x-api-key", _apiKey);
            _httpClient.DefaultRequestHeaders.Add("anthropic-version", "2023-06-01");
            _httpClient.DefaultRequestHeaders.Accept.Add(new MediaTypeWithQualityHeaderValue("application/json"));

            _logger.LogInformation("Anthropic Activities initialized");
        }

        [Activity]
        public async Task<AIResponse> ProcessRequestAsync(AIRequest request)
        {
            var context = ActivityExecutionContext.Current;
            _logger.LogInformation("Processing Anthropic request with prompt: {Prompt}", 
                request.Prompt.Length > 100 ? request.Prompt.Substring(0, 100) + "..." : request.Prompt);

            try
            {
                var messages = new List<object>();
                var messageContent = new List<object>();

                // Handle file input if provided
                if (!string.IsNullOrEmpty(request.FilePath))
                {
                    var fileBytes = await File.ReadAllBytesAsync(request.FilePath);
                    var mimeType = GetMimeType(request.FilePath);

                    // AIDEV-NOTE: Claude supports image analysis
                    if (mimeType.StartsWith("image/"))
                    {
                        var base64Image = Convert.ToBase64String(fileBytes);
                        
                        messageContent.Add(new
                        {
                            type = "text",
                            text = request.Prompt
                        });
                        
                        messageContent.Add(new
                        {
                            type = "image",
                            source = new
                            {
                                type = "base64",
                                media_type = mimeType,
                                data = base64Image
                            }
                        });
                    }
                    else
                    {
                        // For non-image files, include content as text if possible
                        try
                        {
                            var fileContent = Encoding.UTF8.GetString(fileBytes);
                            messageContent.Add(new
                            {
                                type = "text",
                                text = $"{request.Prompt}\n\nFile content:\n{fileContent}"
                            });
                        }
                        catch
                        {
                            messageContent.Add(new
                            {
                                type = "text",
                                text = $"{request.Prompt}\n\n[Binary file provided: {request.FilePath}]"
                            });
                        }
                    }
                }
                else
                {
                    messageContent.Add(new
                    {
                        type = "text",
                        text = request.Prompt
                    });
                }

                messages.Add(new
                {
                    role = "user",
                    content = messageContent.Count == 1 ? messageContent[0] : messageContent
                });

                // Apply custom parameters
                var model = _defaultModel;
                var temperature = 0.7;
                var maxTokens = 4096;

                if (request.Parameters != null)
                {
                    if (request.Parameters.TryGetValue("temperature", out var tempValue) && tempValue is double temp)
                        temperature = temp;
                    if (request.Parameters.TryGetValue("max_tokens", out var tokensValue) && tokensValue is int tokens)
                        maxTokens = tokens;
                    if (request.Parameters.TryGetValue("model", out var modelValue) && modelValue is string modelName)
                        model = modelName;
                }

                // Create request payload
                var requestBody = new
                {
                    model = model,
                    messages = messages,
                    max_tokens = maxTokens,
                    temperature = temperature
                };

                var json = JsonConvert.SerializeObject(requestBody);
                var content = new StringContent(json, Encoding.UTF8, "application/json");

                // Make API call
                var response = await _httpClient.PostAsync("messages", content);
                var responseBody = await response.Content.ReadAsStringAsync();

                if (!response.IsSuccessStatusCode)
                {
                    _logger.LogError("Anthropic API error: {StatusCode} - {Response}", response.StatusCode, responseBody);
                    throw new InvalidOperationException($"Anthropic API error: {response.StatusCode}");
                }

                dynamic result = JsonConvert.DeserializeObject(responseBody);

                // Calculate total tokens (Anthropic provides input and output tokens)
                int? totalTokens = null;
                if (result.usage != null)
                {
                    totalTokens = (int?)result.usage.input_tokens + (int?)result.usage.output_tokens;
                }

                return new AIResponse
                {
                    Content = result.content[0].text,
                    ModelUsed = model,
                    TokensUsed = totalTokens,
                    Metadata = new Dictionary<string, object>
                    {
                        ["stop_reason"] = result.stop_reason?.ToString() ?? "unknown",
                        ["input_tokens"] = (int?)result.usage?.input_tokens ?? 0,
                        ["output_tokens"] = (int?)result.usage?.output_tokens ?? 0
                    }
                };
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error processing Anthropic request");
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