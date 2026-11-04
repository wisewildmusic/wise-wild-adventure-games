namespace Razoria;

public sealed record Level(int Lives, int Multiplier, string Topics);
public sealed record GamePath(string Key, string Label, string Name, string Sight, string Lair);
public sealed record Scene(string Banner, string Picture, string Description);
public sealed record Dragon(string Scene, string Scales, Question Question);

/// <summary>The game's settings and wording. Pictures are shared with the Python game, in the
/// site's static/img/adventure folder, apart from the Authorize Door's and the final boss's.</summary>
public static class Rules
{
    // Change GameVersion when the questions change. A quest keeps the version it started on and
    // is always replayed with that version's questions: the first QuestionCounts[version] of
    // each level's list (new questions only ever go on the end).
    public const int GameVersion = 1;
    public static readonly Dictionary<int, int> QuestionCounts = new() { [1] = 20 };

    // Base point values. Each one is multiplied by the difficulty multiplier.
    public const int CorrectAnswerPoints = 10;
    public const int WiseChoicePoints = 5;
    public const int RelicPoints = 15;
    public const int TreasurePoints = 50;
    public const int LifePoints = 10;
    public const int DragonPoints = 30;
    public const int BossPoints = 100;

    public const string DragonMove = "dragon";
    public const string BossMove = "boss";
    public const string BossName = "The Yellow Screen of Death";

    public static readonly Dictionary<string, Level> Levels = new()
    {
        ["easy"] = new(3, 1, "routes, Razor's @, status codes, configuration"),
        ["medium"] = new(2, 2, "middleware, dependency injection, model binding, Razor Pages, Web Forms"),
        ["hard"] = new(1, 3, "route matching, filters, authorization, tag helpers, layouts, caching"),
    };

    public static string? NextLevel(string level) => level switch
    {
        "easy" => "medium",
        "medium" => "hard",
        _ => null,
    };

    // The three ways into Razoria, in the order the first choice offers them.
    public static readonly GamePath[] Paths =
    [
        new("forest", "Explore the Razor Forest", "the Razor Forest",
            "the Razor Forest, where every trunk is marked with an @",
            "On your way back through the Razor Forest, a glint of gold catches your eye in a mossy hollow."),
        new("cave", "Enter the Kestrel Caverns", "the Kestrel Caverns",
            "the Kestrel Caverns, where small fierce birds listen at every port",
            "On your way back out of the Kestrel Caverns, a glint of gold catches your eye in a side cave."),
        new("castle", "Climb to the Ruins of Castle Web Forms", "the Ruins of Castle Web Forms",
            "the torch-lit trail that climbs to the ruins of Castle Web Forms",
            "On your way back through Castle Web Forms, a glint of gold catches your eye through a doorway: "
            + "a forgotten treasury."),
    ];

    public static readonly Dictionary<string, Scene> Scenes = new()
    {
        ["start"] = new("The Lost Session of Razoria", "title.webp",
            "A moonlit jungle valley wrapped in mist, a golden temple glowing on a far hilltop"),
        ["forest"] = new("The Razor Forest", "forest.webp",
            "Sunbeams falling through towering trees onto a stream, ferns and one giant mossy tree"),
        ["waterfall"] = new("The Pipeline Falls", "waterfall.webp",
            "A roaring waterfall crashing into a green pool between mossy cliffs, a fallen log high across the gorge"),
        ["tree"] = new("The Dependency Tree", "tree.webp",
            "A great owl on a mossy branch above a sea of mist at sunrise, a golden temple glinting in the distance"),
        ["cave"] = new("The Kestrel Caverns", "cave.webp",
            "A dark cave mouth framed by carved stone serpents, a torch burning beside it"),
        ["dark"] = new("The 404 Pit", "pit.webp",
            "A deep pit in the floor of a rocky tunnel, the cave entrance glowing far behind"),
        ["glyph"] = new("The Authorize Door", "glyph-door-aspnet.webp",
            "A massive stone door glowing with lines of ASP.NET code, fire bowls burning on either side"),
        ["castle"] = new("The Ruins of Castle Web Forms", "castle.webp",
            "A ruined castle on a misty hilltop under a full moon, torches lighting the stone path that winds up to it"),
        ["gate"] = new("The Antiforgery Gate", "castle-gate.webp",
            "A great arched gate with a raised iron portcullis, griffin banners and blazing torches on ivy-covered walls"),
        ["hall"] = new("The Hall of Postbacks", "great-hall.webp",
            "A ruined great hall of broken gothic arches, torches flickering beside an empty throne at the top of worn steps"),
        ["ramparts"] = new("The Ramparts of Redirects", "ramparts.webp",
            "Torch-lit battlements under a full moon, stone towers rising above a misty valley"),
        ["gallery"] = new("The Moonlit Gallery", "gallery.webp",
            "A stone gallery high in a tower, ivy twisting around its pillars, the full moon over a misty valley beyond the balustrade"),
        ["temple"] = new("The Temple of the Golden Session", "temple.webp",
            "A torch-lit temple hall leading to a golden vault door guarded by two stone serpents, a jeweled chest by the path"),
        ["victory"] = new("The Session Is Yours!", "treasure.webp",
            "The Golden Session: a glowing golden orb wrapped by a serpent, on a stone pedestal among gold and gems"),
        ["dragon-emerald"] = new("The Emerald Dragon", "dragon-emerald.webp",
            "A green dragon asleep in a cave, curled around an open treasure chest full of gold and emeralds"),
        ["dragon-ember"] = new("The Ember Dragon", "dragon-ember.webp",
            "A red dragon asleep in a fiery cave around a treasure chest of gold and rubies, a sword and a crown beside it"),
        ["dragon-frost"] = new("The Frost Dragon", "dragon-frost.webp",
            "A blue dragon asleep in an ice cave, its treasure chest full of gold and glowing sapphires"),
        ["dragon-pearl"] = new("The Pearl Dragon", "dragon-pearl.webp",
            "A white dragon asleep in a sunlit forest beside a treasure chest of gold, diamonds and a silver crown"),
        ["dragon-amethyst"] = new("The Amethyst Dragon", "dragon-amethyst.webp",
            "A purple dragon coiled around a treasure chest of gold and glowing amethysts in a violet forest"),
        ["dragon-autumn"] = new("The Autumn Dragon", "dragon-autumn.webp",
            "A copper dragon asleep among autumn leaves beside a treasure chest of gold and a golden goblet"),
        ["dragon-gold"] = new("The Golden Dragon", "dragon-gold.webp",
            "A golden dragon asleep on a heap of gold coins beside a treasure chest in a torch-lit castle hall"),
        ["dragon-silver"] = new("The Silver Dragon", "dragon-silver.webp",
            "A silver dragon asleep in a castle hall beside a chest of silver and diamonds, a knight's helmet and a sword"),
        ["dragon-shadow"] = new("The Shadow Dragon", "dragon-shadow.webp",
            "A black dragon asleep in a castle hall around a chest of gold and rubies, a jeweled crown at its feet"),
        ["boss"] = new(BossName, "yellow-screen-of-death.webp",
            "A towering giant of torn, glowing yellow parchment with burning red eyes and a mouth of ripped paper fangs, on "
            + "the steps of a ruined jungle temple under a full moon. Across its chest is the heading Server Error in '/' "
            + "Application, then Object reference not set to an instance of an object, then a crack in the page showing a "
            + "blue ASP.NET emblem. Below that it lists Exception Details, Source Error, with Line 43, user.Name = "
            + "txtName.Text, highlighted beneath var user = Session[\"User\"], and a Stack Trace. Strips of stack trace wind "
            + "down its arms to clawed hands of crumpled paper, and torn signs hang on chains around it, reading 500 "
            + "Internal Server Error, Session Expired, NullReferenceException and customErrors mode=\"Off\""),
        ["game_over"] = new("500 Internal Server Error", "game-over.webp",
            "A burnt-out torch and a lost compass on rocky ground under a blood-red sky"),
    };

    public static readonly Dictionary<(string Level, string Path), Dragon> Dragons = new()
    {
        [("easy", "cave")] = new("dragon-emerald", "green as moss", Questions.Dragons[("easy", "cave")]),
        [("medium", "cave")] = new("dragon-ember", "glowing like hot coals", Questions.Dragons[("medium", "cave")]),
        [("hard", "cave")] = new("dragon-frost", "glittering with ice", Questions.Dragons[("hard", "cave")]),
        [("easy", "forest")] = new("dragon-pearl", "white as moonlight", Questions.Dragons[("easy", "forest")]),
        [("medium", "forest")] = new("dragon-amethyst", "a deep, shimmering purple", Questions.Dragons[("medium", "forest")]),
        [("hard", "forest")] = new("dragon-autumn", "the color of falling leaves", Questions.Dragons[("hard", "forest")]),
        [("easy", "castle")] = new("dragon-gold", "as bright as the coins beneath it", Questions.Dragons[("easy", "castle")]),
        [("medium", "castle")] = new("dragon-silver", "gleaming like polished armor", Questions.Dragons[("medium", "castle")]),
        [("hard", "castle")] = new("dragon-shadow", "as black as a moonless night", Questions.Dragons[("hard", "castle")]),
    };

    public static readonly string[] Intro =
    [
        "Long ago, the coders of Razoria forged their greatest treasure, the Golden Session, which remembers "
        + "everyone who has ever visited, and hid it deep within this wild land. It has lain idle ever since, and "
        + "no one knows whether it has timed out. Its guardians still test every traveler, and they accept only "
        + "answers that would really run: riddles written in the language of the realm, ASP.NET.",
        "One law holds throughout Razoria: every riddle of code is a real ASP.NET Core app on .NET 10, and you're "
        + "shown all of it. It runs in Production unless it says otherwise. Its requests arrive one at a time, each with "
        + "any body it sends written after its address, and they keep any cookies they're given. A riddle of Razor alone "
        + "is the page at Pages/Index.cshtml, in an app that does nothing but map its Razor Pages. When there are several "
        + "responses, the answers show them side by side, and the white space around a page's lines is ignored.",
        "Answer wisely and choose your path carefully. Every wrong answer costs you a life, and some "
        + "choices lead to certain doom...",
    ];

    // The page's own words for this game, by the same keys as the Python game's (pythonia.TEXTS).
    public static readonly Dictionary<string, string> Texts = new()
    {
        ["title"] = "The Lost Session of Razoria",
        ["language"] = "ASP.NET",
        ["found"] = "Found the session",
        ["master"] = "ASP.NET Master",
        ["lost_to_boss"] = "Lost to the Yellow Screen of Death",
        ["hall_note"] = "Walk every path on every level to face the Yellow Screen of Death.",
        ["boss_offer_title"] = "The final challenge: The Yellow Screen of Death",
        ["boss_offer"] = "You have walked every path on every level, and the Yellow Screen of Death, the oldest error "
            + "in all of Razoria, has noticed you. Answer its question, the hardest in the land, to earn the title of "
            + "ASP.NET Master and {points} points.",
        ["boss_warning"] = "Beware: if you fail, all is lost. Your score falls to zero and you must start over.",
        ["boss_button"] = "Face the Yellow Screen of Death",
        ["boss_confirm"] = "Face the Yellow Screen of Death? If you fail, all is lost: your score falls to zero and you must start over.",
        ["boss_won"] = "You have cleared the Yellow Screen of Death. You are an ASP.NET Master!",
        ["boss_lost"] = "The Yellow Screen of Death has the last word. All is lost: your session is gone, and you must start over.",
        ["conquered_every_path"] = "Every path on every level: you've explored all of Razoria!",
        ["conquered_every_level"] = "Easy, Medium and Hard: you've conquered every level of Razoria!",
    };
}
