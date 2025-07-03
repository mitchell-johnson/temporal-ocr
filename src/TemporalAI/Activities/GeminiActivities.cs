// AIDEV-NOTE: Generic Gemini AI activities for Temporal workflows
using System;
using System.Collections.Generic;
using System.IO;
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
    /// Implementation of Gemini AI activities
    /// </summary>
    public class GeminiActivities : IGeminiActivities
    {
        private readonly ILogger<GeminiActivities> _logger;
        private readonly HttpClient _httpClient;
        private readonly string _apiKey;
        private readonly string _model = "gemini-2.5-pro";

        public GeminiActivities(ILogger<GeminiActivities> logger)
        {
            _logger = logger;
            
            _apiKey = Environment.GetEnvironmentVariable("GEMINI_API_KEY");
            if (string.IsNullOrEmpty(_apiKey))
            {
                throw new InvalidOperationException("GEMINI_API_KEY environment variable not set.");
            }

            _httpClient = new HttpClient
            {
                BaseAddress = new Uri("https://generativelanguage.googleapis.com/v1beta/")
            };
            _httpClient.DefaultRequestHeaders.Accept.Add(new MediaTypeWithQualityHeaderValue("application/json"));

            _logger.LogInformation("Gemini Activities initialized");
        }

        [Activity]
        public async Task<AIResponse> ProcessRequestAsync(AIRequest request)
        {
            var context = ActivityExecutionContext.Current;
            _logger.LogInformation("Processing Gemini request with prompt: {Prompt}", 
                request.Prompt.Length > 100 ? request.Prompt.Substring(0, 100) + "..." : request.Prompt);

            try
            {
                // Create the content parts
                var parts = new List<object>();
                
                // Add text prompt
                parts.Add(new { text = request.Prompt });

                // If file is provided, include it
                if (!string.IsNullOrEmpty(request.FilePath))
                {
                    var fileBytes = await File.ReadAllBytesAsync(request.FilePath);
                    var mimeType = GetMimeType(request.FilePath);
                    
                    parts.Add(new
                    {
                        inline_data = new
                        {
                            mime_type = mimeType,
                            data = Convert.ToBase64String(fileBytes)
                        }
                    });
                    
                    _logger.LogInformation("Including file: {FilePath} with mime type: {MimeType}", 
                        request.FilePath, mimeType);
                }

                // Create generation config
                var generationConfig = new
                {
                    temperature = 0.7,
                    topP = 0.95,
                    topK = 40,
                    maxOutputTokens = 4096
                };

                // Apply custom parameters if provided
                if (request.Parameters != null)
                {
                    var configDict = new Dictionary<string, object>
                    {
                        ["temperature"] = 0.7,
                        ["topP"] = 0.95,
                        ["topK"] = 40,
                        ["maxOutputTokens"] = 4096
                    };

                    foreach (var param in request.Parameters)
                    {
                        if (configDict.ContainsKey(param.Key))
                        {
                            configDict[param.Key] = param.Value;
                        }
                    }

                    generationConfig = new
                    {
                        temperature = Convert.ToDouble(configDict["temperature"]),
                        topP = Convert.ToDouble(configDict["topP"]),
                        topK = Convert.ToInt32(configDict["topK"]),
                        maxOutputTokens = Convert.ToInt32(configDict["maxOutputTokens"])
                    };
                }

                // Create the request body
                var requestBody = new
                {
                    contents = new[]
                    {
                        new
                        {
                            parts = parts
                        }
                    },
                    generationConfig = generationConfig
                };

                var json = JsonConvert.SerializeObject(requestBody);
                var content = new StringContent(json, Encoding.UTF8, "application/json");

                // Make API call
                var response = await _httpClient.PostAsync(
                    $"models/{_model}:generateContent?key={_apiKey}",
                    content
                );

                var responseBody = await response.Content.ReadAsStringAsync();

                if (!response.IsSuccessStatusCode)
                {
                    _logger.LogError("Gemini API error: {StatusCode} - {Response}", response.StatusCode, responseBody);
                    throw new InvalidOperationException($"Gemini API error: {response.StatusCode}");
                }

                dynamic result = JsonConvert.DeserializeObject(responseBody);

                // Extract the response content
                string responseContent = "";
                if (result?.candidates != null && result.candidates.Count > 0)
                {
                    var candidate = result.candidates[0];
                    if (candidate?.content != null && candidate.content.parts != null && candidate.content.parts.Count > 0)
                    {
                        responseContent = candidate.content.parts[0].text?.ToString() ?? "";
                    }
                }

                // AIDEV-NOTE: Handle safety ratings and blocked content
                if (string.IsNullOrEmpty(responseContent))
                {
                    _logger.LogWarning("Gemini response was empty or blocked");
                    return new AIResponse
                    {
                        Content = "Response was blocked due to safety filters",
                        ModelUsed = _model,
                        Metadata = new Dictionary<string, object>
                        {
                            ["safety_blocked"] = true
                        }
                    };
                }

                return new AIResponse
                {
                    Content = responseContent,
                    ModelUsed = _model,
                    TokensUsed = null, // Gemini doesn't provide token count in the same way
                    Metadata = new Dictionary<string, object>
                    {
                        ["finish_reason"] = result.candidates?[0]?.finishReason?.ToString() ?? "completed"
                    }
                };
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error processing Gemini request");
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
                ".pdf" => "application/pdf",
                ".txt" => "text/plain",
                _ => "application/octet-stream"
            };
        }
    }
}