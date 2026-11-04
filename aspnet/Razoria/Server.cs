using System.Text.Json;
using Microsoft.AspNetCore.Hosting.Server;
using Microsoft.AspNetCore.Http.Features;

namespace Razoria;

/// <summary>ASP.NET Core's servers are its own extension point: Kestrel is one IServer, and this is another, in
/// about forty lines. It has no socket. It answers exactly one request, read from a stream, and that's why the
/// application in Program.cs can run like any other program the website starts, one request at a time, with
/// nothing to keep alive on the server between them.</summary>
public sealed class OneRequestServer : IServer
{
    Func<IFeatureCollection, Task> handle = _ => throw new InvalidOperationException("The server hasn't started");

    public IFeatureCollection Features { get; } = new FeatureCollection();

    public Task StartAsync<TContext>(IHttpApplication<TContext> application, CancellationToken cancellationToken)
        where TContext : notnull
    {
        handle = async features =>
        {
            var context = application.CreateContext(features);
            try
            {
                await application.ProcessRequestAsync(context);
                application.DisposeContext(context, null);
            }
            catch (Exception error)
            {
                application.DisposeContext(context, error);
                throw;
            }
        };
        return Task.CompletedTask;
    }

    public Task StopAsync(CancellationToken cancellationToken) => Task.CompletedTask;

    public void Dispose() { }

    /// <summary>Reads one request from the website and sends the application's response back. Returns the
    /// program's exit code: 0 for a 200 OK, otherwise 2, which the website takes to mean the game can't run.</summary>
    public async Task<int> AnswerAsync(Stream input, Stream output)
    {
        using var body = new MemoryStream();
        await input.CopyToAsync(body);
        body.Position = 0;
        using var request = await JsonDocument.ParseAsync(body);
        string? command = request.RootElement.GetProperty("command").GetString();
        body.Position = 0;

        var response = new HttpResponseFeature();
        var features = new FeatureCollection();
        features.Set<IHttpRequestFeature>(new HttpRequestFeature
        {
            Protocol = "HTTP/1.1",
            Scheme = "http",
            Method = command == "replay" ? HttpMethods.Post : HttpMethods.Get,
            Path = "/" + command,
            Body = body,
        });
        features.Set<IHttpResponseFeature>(response);
        features.Set<IHttpResponseBodyFeature>(new StreamResponseBodyFeature(output));

        await handle(features);
        await output.FlushAsync();
        if (response.StatusCode == StatusCodes.Status200OK)
            return 0;
        Console.Error.WriteLine($"{response.StatusCode} for the command {command}");
        return 2;
    }
}
