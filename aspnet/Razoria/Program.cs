// The Lost Session of Razoria: a text adventure with ASP.NET challenges, written in ASP.NET.
//
// This is an ASP.NET Core application: a WebApplication with a pipeline, routes and endpoints. What it doesn't
// have is a socket. The website (site/compiled_game.py) starts it whenever it needs the game, as it starts the
// other games' programs, and sends one JSON request on standard input. OneRequestServer (Server.cs) turns that
// into a real HTTP request, the application answers it, and the response's body goes to standard output:
//
//     {"command": "info"}        GET  /info       the game's settings, paths, scenes and wording
//     {"command": "replay", ...} POST /replay     a quest played through to where it stands (Game.Replay)
//     {"command": "questions"}   GET  /questions  every question, so their answers can be checked by running them
//
// So nothing has to keep running on the server, and no port has to be opened. The program keeps nothing between
// runs. A quest is its random seed plus the moves made so far, and every replay plays it again from the start,
// which always ends in the same place.

using System.Text.Json;
using Microsoft.AspNetCore.Hosting.Server;
using Razoria;

var builder = WebApplication.CreateEmptyBuilder(new WebApplicationOptions { Args = args });
builder.Services.AddRoutingCore();
builder.Services.AddSingleton<OneRequestServer>();
builder.Services.AddSingleton<IServer>(services => services.GetRequiredService<OneRequestServer>());

var app = builder.Build();

app.MapGet("/info", http => Answers.Send(http, Answers.WriteInfo));

app.MapPost("/replay", async http =>
{
    using var request = await JsonDocument.ParseAsync(http.Request.Body);
    var quest = Game.Replay(QuestRequest.From(request.RootElement));
    await Answers.Send(http, json => Answers.WriteQuest(json, quest));
});

app.MapGet("/questions", http => Answers.Send(http, Answers.WriteQuestions));

await app.StartAsync();
return await app.Services.GetRequiredService<OneRequestServer>()
    .AnswerAsync(Console.OpenStandardInput(), Console.OpenStandardOutput());
