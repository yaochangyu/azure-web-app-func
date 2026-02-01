namespace AzureWebApp.Functions.Models;

public class VersionInfo
{
    public string Version { get; set; } = string.Empty;
    public string BuildTime { get; set; } = string.Empty;
    public string Environment { get; set; } = string.Empty;
}
