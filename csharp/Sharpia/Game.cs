using System.Text.Json;

namespace Sharpia;

/// <summary>What the game is waiting for: a menu of choices, or a C# challenge.</summary>
public abstract class Prompt
{
    public abstract string Kind { get; }
    public abstract IReadOnlyList<string> Moves { get; }
    public bool Accepts(string move) => Moves.Contains(move);
}

/// <summary>A menu: the explorer picks an option (moves "1", "2", ...).</summary>
public sealed class Choice(params string[] options) : Prompt
{
    public string[] Options { get; } = options;
    public override string Kind => "choice";
    public override IReadOnlyList<string> Moves { get; } =
        Enumerable.Range(1, options.Length).Select(number => number.ToString()).ToArray();
}

/// <summary>A challenge: the explorer picks an answer (moves "a" to "d").</summary>
public sealed class Challenge(string challenger, Question question, string[] options) : Prompt
{
    public string Challenger { get; } = challenger;
    public Question Question { get; } = question;
    public string[] Options { get; } = options;
    public override string Kind => "question";
    public override IReadOnlyList<string> Moves { get; } = Game.Letters.Take(options.Length).ToArray();
}

/// <summary>Everything that defines a quest: replaying it always gives the same result.</summary>
public sealed record QuestRequest(
    string Name, string Difficulty, long Seed, string[] Moves, int Carried, string? OnlyPath,
    int[] SkipQuestions, int Version, bool Final)
{
    public static QuestRequest From(JsonElement json) => new(
        json.GetProperty("name").GetString()!,
        json.GetProperty("difficulty").GetString()!,
        json.GetProperty("seed").GetInt64(),
        json.GetProperty("moves").EnumerateArray().Select(move => move.GetString()!).ToArray(),
        json.GetProperty("carried").GetInt32(),
        json.GetProperty("onlyPath").GetString(),
        json.GetProperty("skipQuestions").EnumerateArray().Select(number => number.GetInt32()).ToArray(),
        json.GetProperty("version").GetInt32(),
        json.GetProperty("final").GetBoolean());
}

/// <summary>One explorer's quest: their progress, the scene they're in, what happened since
/// their last move, and what the game is waiting for now.</summary>
public sealed class Quest(QuestRequest request)
{
    // With the same seed, the same shuffles on every replay.
    public Random Rng { get; } = new((int)(request.Seed & int.MaxValue));
    public QuestRequest Request { get; } = request;

    public string Name { get; } = request.Name;
    public string Difficulty { get; } = request.Difficulty;
    public int Lives { get; set; } = Rules.Levels[request.Difficulty].Lives;
    public int Score { get; set; } = request.Carried;
    public List<string> Inventory { get; } = [];
    public List<int> Deck { get; set; } = [];

    public int Carried { get; } = request.Carried;
    public string? OnlyPath { get; } = request.OnlyPath;
    public HashSet<int> SkipQuestions { get; } = [.. request.SkipQuestions];
    public int Version { get; } = request.Version;
    public bool Final { get; } = request.Final;

    public List<int> Asked { get; } = [];         // question numbers asked, in order
    public string? Path { get; set; }             // the path it went down, once chosen
    public string? Dragon { get; set; }           // the bonus dragon: "won" or "lost" once answered
    public string? Boss { get; set; }             // the final boss: "won" or "lost" once answered

    public string Scene { get; private set; } = "start";
    public List<(string Kind, string Text)> Log { get; } = [];
    public Prompt? Prompt { get; set; }           // null once the quest (or a battle) is over
    public string? Result { get; set; }           // "win" or "lose" once the quest is over

    public string Move { get; set; } = "";        // the explorer's latest move, for the story to read
    public bool Passed { get; set; }              // how the latest challenge went

    public Dragon? DragonAwaits =>
        Result == "win" && Prompt is null && Dragon is null && Boss is null
            ? Rules.Dragons.GetValueOrDefault((Difficulty, Path!))
            : null;

    public bool BossAwaits => Final && Result == "win" && Prompt is null && Boss is null;

    public void Banner(string scene) => Scene = scene;
    public void Narrate(string text) => Log.Add(("story", text));
    public void Note(string kind, string text) => Log.Add((kind, text));
}

public static class Game
{
    public static readonly string[] Letters = ["a", "b", "c", "d"];

    /// <summary>Plays a quest from the start with the moves made so far, and returns it as it
    /// stands now. Its log holds what happened after the last move. C#'s iterators stand in for
    /// the console game's input(): the story yields a prompt and carries on at the next move.
    /// After a win, Rules.DragonMove wakes the bonus dragon and the next move answers its
    /// riddle. A final quest (one that completes every path on every level) can then face the
    /// boss: Rules.BossMove, then the answer.</summary>
    public static Quest Replay(QuestRequest request)
    {
        var quest = new Quest(request);
        var game = Story.StartGame(quest).GetEnumerator();
        quest.Prompt = game.MoveNext() ? game.Current : null;
        foreach (var move in request.Moves)
        {
            IEnumerable<Prompt>? battle =
                move == Rules.DragonMove && quest.DragonAwaits is not null ? Story.DragonBattle(quest)
                : move == Rules.BossMove && quest.BossAwaits ? Story.BossBattle(quest)
                : null;
            if (battle is not null)
            {
                game.Dispose();
                game = battle.GetEnumerator();
                quest.Log.Clear();
                quest.Prompt = game.MoveNext() ? game.Current : null;
                continue;
            }
            if (quest.Prompt is null || !quest.Prompt.Accepts(move))
                break;
            quest.Log.Clear();
            quest.Move = move;
            quest.Prompt = game.MoveNext() ? game.Current : null;
        }
        game.Dispose();
        return quest;
    }

    /// <summary>A Fisher-Yates shuffle, written out so that saved quests replay the same however
    /// the .NET libraries change. (A seeded Random's numbers are themselves promised not to.)</summary>
    public static void Shuffle<T>(Random rng, IList<T> items)
    {
        for (int i = items.Count - 1; i > 0; i--)
        {
            int j = rng.Next(i + 1);
            (items[i], items[j]) = (items[j], items[i]);
        }
    }
}

/// <summary>The program's JSON answers.</summary>
public static class Answers
{
    public static void WriteInfo(Utf8JsonWriter json)
    {
        json.WriteStartObject();
        json.WriteNumber("gameVersion", Rules.GameVersion);
        json.WriteStartObject("questionCounts");
        foreach (var (version, count) in Rules.QuestionCounts)
            json.WriteNumber(version.ToString(), count);
        json.WriteEndObject();
        json.WriteStartArray("levels");
        foreach (var (key, level) in Rules.Levels)
        {
            json.WriteStartObject();
            json.WriteString("key", key);
            json.WriteNumber("lives", level.Lives);
            json.WriteNumber("multiplier", level.Multiplier);
            json.WriteString("topics", level.Topics);
            json.WriteEndObject();
        }
        json.WriteEndArray();
        json.WriteStartArray("paths");
        foreach (var path in Rules.Paths)
        {
            json.WriteStartObject();
            json.WriteString("key", path.Key);
            json.WriteString("label", path.Label);
            json.WriteString("name", path.Name);
            json.WriteEndObject();
        }
        json.WriteEndArray();
        json.WriteStartObject("scenes");
        foreach (var (key, scene) in Rules.Scenes)
        {
            json.WriteStartArray(key);
            json.WriteStringValue(scene.Banner);
            json.WriteStringValue(scene.Picture);
            json.WriteStringValue(scene.Description);
            json.WriteEndArray();
        }
        json.WriteEndObject();
        json.WriteString("dragonMove", Rules.DragonMove);
        json.WriteNumber("dragonPoints", Rules.DragonPoints);
        json.WriteString("bossMove", Rules.BossMove);
        json.WriteNumber("bossPoints", Rules.BossPoints);
        json.WriteStartObject("texts");
        foreach (var (key, text) in Rules.Texts)
            json.WriteString(key, text);
        json.WriteStartArray("intro");
        foreach (var paragraph in Rules.Intro)
            json.WriteStringValue(paragraph);
        json.WriteEndArray();
        json.WriteEndObject();
        json.WriteEndObject();
    }

    public static void WriteQuest(Utf8JsonWriter json, Quest quest)
    {
        json.WriteStartObject();
        json.WriteString("scene", quest.Scene);
        json.WriteString("result", quest.Result);
        json.WriteStartObject("player");
        json.WriteString("name", quest.Name);
        json.WriteString("difficulty", quest.Difficulty);
        json.WriteNumber("lives", quest.Lives);
        json.WriteNumber("score", quest.Score);
        json.WriteStartArray("inventory");
        foreach (var relic in quest.Inventory)
            json.WriteStringValue(relic);
        json.WriteEndArray();
        json.WriteEndObject();
        json.WriteStartArray("log");
        foreach (var (kind, text) in quest.Log)
        {
            json.WriteStartArray();
            json.WriteStringValue(kind);
            json.WriteStringValue(text);
            json.WriteEndArray();
        }
        json.WriteEndArray();
        json.WriteStartArray("asked");
        foreach (var number in quest.Asked)
            json.WriteNumberValue(number);
        json.WriteEndArray();
        json.WriteString("path", quest.Path);
        json.WriteString("dragon", quest.Dragon);
        json.WriteString("boss", quest.Boss);
        json.WriteString("dragonAwaits", quest.DragonAwaits?.Scene);
        json.WriteBoolean("bossAwaits", quest.BossAwaits);
        json.WritePropertyName("prompt");
        WritePrompt(json, quest.Prompt);
        json.WriteEndObject();
    }

    static void WritePrompt(Utf8JsonWriter json, Prompt? prompt)
    {
        if (prompt is null)
        {
            json.WriteNullValue();
            return;
        }
        json.WriteStartObject();
        json.WriteString("kind", prompt.Kind);
        json.WriteStartArray("moves");
        foreach (var move in prompt.Moves)
            json.WriteStringValue(move);
        json.WriteEndArray();
        json.WriteStartArray("options");
        switch (prompt)
        {
            case Choice choice:
                foreach (var option in choice.Options)
                    json.WriteStringValue(option);
                break;
            case Challenge challenge:
                for (int i = 0; i < challenge.Options.Length; i++)
                {
                    json.WriteStartArray();
                    json.WriteStringValue(Game.Letters[i]);
                    json.WriteStringValue(challenge.Options[i]);
                    json.WriteEndArray();
                }
                break;
        }
        json.WriteEndArray();
        if (prompt is Challenge asked)
        {
            json.WriteString("challenger", asked.Challenger);
            json.WriteString("prompt", asked.Question.Prompt);
            json.WriteString("code", asked.Question.Code);
        }
        json.WriteEndObject();
    }

    public static void WriteQuestions(Utf8JsonWriter json)
    {
        json.WriteStartObject();
        json.WriteStartObject("levels");
        foreach (var (level, questions) in Questions.Levels)
        {
            json.WriteStartArray(level);
            foreach (var question in questions)
                WriteQuestion(json, question);
            json.WriteEndArray();
        }
        json.WriteEndObject();
        json.WriteStartArray("dragons");
        foreach (var ((level, path), dragon) in Rules.Dragons)
        {
            json.WriteStartObject();
            json.WriteString("level", level);
            json.WriteString("path", path);
            json.WriteString("scene", dragon.Scene);
            json.WritePropertyName("question");
            WriteQuestion(json, dragon.Question);
            json.WriteEndObject();
        }
        json.WriteEndArray();
        json.WriteStartArray("boss");
        foreach (var question in Questions.Boss)
            WriteQuestion(json, question);
        json.WriteEndArray();
        json.WriteEndObject();
    }

    static void WriteQuestion(Utf8JsonWriter json, Question question)
    {
        json.WriteStartObject();
        json.WriteString("prompt", question.Prompt);
        json.WriteString("code", question.Code);
        json.WriteStartArray("options");
        foreach (var option in question.Options)
            json.WriteStringValue(option);
        json.WriteEndArray();
        json.WriteString("answer", question.Answer);
        json.WriteString("explain", question.Explain);
        json.WriteString("compileError", question.CompileError);
        json.WriteEndObject();
    }
}
