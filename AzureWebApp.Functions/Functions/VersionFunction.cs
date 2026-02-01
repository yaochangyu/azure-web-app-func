using Microsoft.Azure.Functions.Worker;
using Microsoft.Azure.Functions.Worker.Http;
using Microsoft.Extensions.Logging;
using System.Net;
using System.Reflection;
using AzureWebApp.Functions.Models;

namespace AzureWebApp.Functions.Functions;

public class VersionFunction
{
    private readonly ILogger<VersionFunction> _logger;

    public VersionFunction(ILogger<VersionFunction> logger)
    {
        _logger = logger;
    }

    [Function("VersionFunction")]
    public async Task<HttpResponseData> Run(
        [HttpTrigger(AuthorizationLevel.Anonymous, "get", Route = "version")] HttpRequestData req)
    {
        _logger.LogInformation("Version endpoint called.");

        var assembly = Assembly.GetExecutingAssembly();
        var informationalVersion = assembly.GetCustomAttribute<AssemblyInformationalVersionAttribute>()?.InformationalVersion ?? "unknown";
        
        // Parse version and build time from InformationalVersion
        string version;
        string buildTime;
        
        if (informationalVersion.StartsWith("+"))
        {
            // Format: +{fullCommitHash} - MSBuild SourceRevisionId format
            var fullCommit = informationalVersion.TrimStart('+');
            version = fullCommit.Length > 7 ? fullCommit.Substring(0, 7) : fullCommit;
            
            // Try to get build time from assembly compilation time
            var buildDate = File.GetLastWriteTimeUtc(assembly.Location);
            buildTime = buildDate.ToString("yyyy-MM-ddTHH:mm:ssZ");
        }
        else if (informationalVersion.Contains("-"))
        {
            // Format: {commit}-{buildTime}
            var versionParts = informationalVersion.Split('-', 2);
            version = versionParts[0];
            buildTime = versionParts[1];
        }
        else
        {
            version = informationalVersion;
            buildTime = DateTime.UtcNow.ToString("yyyy-MM-ddTHH:mm:ssZ");
        }

        var environment = System.Environment.GetEnvironmentVariable("AZURE_FUNCTIONS_ENVIRONMENT") 
                          ?? System.Environment.GetEnvironmentVariable("ASPNETCORE_ENVIRONMENT")
                          ?? "Development";

        var versionInfo = new VersionInfo
        {
            Version = version,
            BuildTime = buildTime,
            Environment = environment
        };

        var response = req.CreateResponse(HttpStatusCode.OK);
        await response.WriteAsJsonAsync(versionInfo);

        return response;
    }
}
