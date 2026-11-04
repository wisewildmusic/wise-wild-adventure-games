// The Lost Compiler of Sharpia: a text adventure with C# challenges, written in C#.
//
// The website (site/compiled_game.py) starts this program whenever it needs the game. It sends one
// JSON request on standard input and reads one JSON answer from standard output:
//
//     {"command": "info"}        the game's settings, paths, scenes and wording
//     {"command": "replay", ...} a quest played through to where it stands (Game.Replay)
//     {"command": "questions"}   every question, so their answers can be checked by running them
//
// The program keeps nothing between runs. A quest is its random seed plus the moves made so
// far, and every replay plays it again from the start, which always ends in the same place.

using System.Text.Json;
using Sharpia;

using var input = Console.OpenStandardInput();
using var request = JsonDocument.Parse(input);
var root = request.RootElement;
using var output = Console.OpenStandardOutput();
using var writer = new Utf8JsonWriter(output);

switch (root.GetProperty("command").GetString())
{
    case "info":
        Answers.WriteInfo(writer);
        break;
    case "replay":
        Answers.WriteQuest(writer, Game.Replay(QuestRequest.From(root)));
        break;
    case "questions":
        Answers.WriteQuestions(writer);
        break;
    default:
        Console.Error.WriteLine("Unknown command");
        return 2;
}
return 0;
