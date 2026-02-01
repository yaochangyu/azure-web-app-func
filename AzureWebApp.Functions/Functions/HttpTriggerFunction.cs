using Microsoft.Azure.Functions.Worker;
using Microsoft.Azure.Functions.Worker.Http;
using Microsoft.Extensions.Logging;
using System.Net;

namespace AzureWebApp.Functions.Functions;

public class HttpTriggerFunction
{
    private readonly ILogger<HttpTriggerFunction> _logger;

    public HttpTriggerFunction(ILogger<HttpTriggerFunction> logger)
    {
        _logger = logger;
    }

    [Function("HttpTriggerFunction")]
    public async Task<HttpResponseData> Run(
        [HttpTrigger(AuthorizationLevel.Function, "get", "post")] HttpRequestData req)
    {
        _logger.LogInformation("C# HTTP trigger function processed a request.");

        var responseData = new
        {
            message = "Welcome to Azure Functions!",
            timestamp = DateTime.UtcNow,
            method = req.Method,
            url = req.Url.ToString()
        };

        var response = req.CreateResponse(HttpStatusCode.OK);
        await response.WriteAsJsonAsync(responseData);

        return response;
    }
}
