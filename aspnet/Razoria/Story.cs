namespace Razoria;

/// <summary>The adventure itself. Each part of the story is a C# iterator: `yield return` hands
/// the page a prompt, and the story carries on from there with the explorer's move in q.Move.
/// `foreach ... yield return` walks through a smaller part of the story. A part that has an
/// outcome leaves it in q.Passed.</summary>
public static class Story
{
    // ------------------------------------------------------------------
    // Helpers
    // ------------------------------------------------------------------

    static void AddPoints(Quest q, int basePoints, string reason)
    {
        int points = basePoints * Rules.Levels[q.Difficulty].Multiplier;
        q.Score += points;
        q.Note("points", $"+{points} points ({reason})");
    }

    /// <summary>Takes away one life. Returns true if the explorer still has lives left.</summary>
    static bool LoseLife(Quest q)
    {
        q.Lives--;
        q.Note("life", q.Lives > 0 ? $"You lose a life! Lives remaining: {q.Lives}" : "You have no lives left!");
        return q.Lives > 0;
    }

    static void CollectRelic(Quest q, string relic)
    {
        q.Inventory.Add(relic);
        q.Note("relic", $"You found a relic: {relic}!");
    }

    /// <summary>The next question from the explorer's deck, reshuffling when it runs out. A path
    /// not taken yet starts with a deck of the questions the level's earlier paths didn't ask. A
    /// quest asks at most 6, so a level's 20 questions are enough for all three paths.</summary>
    static Question DrawQuestion(Quest q)
    {
        if (q.Deck.Count == 0)
        {
            var every = Enumerable.Range(0, Rules.QuestionCounts[q.Version]).ToList();
            var unasked = q.Asked.Count == 0 ? every.Where(n => !q.SkipQuestions.Contains(n)).ToList() : [];
            q.Deck = unasked.Count > 0 ? unasked : every;
            Game.Shuffle(q.Rng, q.Deck);
        }
        int number = q.Deck[^1];
        q.Deck.RemoveAt(q.Deck.Count - 1);
        q.Asked.Add(number);
        return Questions.Levels[q.Difficulty][number];
    }

    /// <summary>Asks one ASP.NET question: the next from the deck, or `given` (a dragon's or the
    /// boss's). Leaves q.Passed true if the answer is right, and earns `points`.</summary>
    static IEnumerable<Prompt> AskQuestion(Quest q, string challenger, Question? given = null,
                                           int points = Rules.CorrectAnswerPoints, string reason = "correct answer")
    {
        var question = given ?? DrawQuestion(q);
        var options = question.Options.ToArray();
        Game.Shuffle(q.Rng, options);

        yield return new Challenge(challenger, question, options);

        string correctLetter = Game.Letters[Array.IndexOf(options, question.Answer)];
        q.Passed = q.Move == correctLetter;
        if (q.Passed)
        {
            q.Note("correct", "Correct!");
            AddPoints(q, points, reason);
        }
        else
        {
            q.Note("wrong", $"{correctLetter}) {question.Answer}");
        }
        q.Note("why", question.Explain);
    }

    /// <summary>Asks questions until one is answered correctly. Each wrong answer costs a life.
    /// Leaves q.Passed false if the explorer runs out of lives.</summary>
    static IEnumerable<Prompt> FaceChallenge(Quest q, string challenger)
    {
        while (true)
        {
            foreach (var prompt in AskQuestion(q, challenger))
                yield return prompt;
            if (q.Passed)
                yield break;
            if (!LoseLife(q))
                yield break;
            q.Note("info", $"{challenger} gives you another chance...");
        }
    }

    // ------------------------------------------------------------------
    // The start
    // ------------------------------------------------------------------

    public static IEnumerable<Prompt> StartGame(Quest q)
    {
        q.Banner("start");
        int chosen;
        if (q.OnlyPath is string only)
        {
            // A winner going back for a path they didn't take, score and all.
            var path = Rules.Paths.First(p => p.Key == only);
            string fresh = q.SkipQuestions.Count > 0 ? ", where new riddles await" : "";
            q.Narrate($"Welcome back, {q.Name}! You return to the edge of Razoria with {q.Carried} points "
                      + "from your last quest, wondering what waits down the way you didn't take. "
                      + $"This time you turn toward {path.Sight}{fresh}.");
            yield return new Choice(path.Label);
            chosen = Array.IndexOf(Rules.Paths, path);
        }
        else
        {
            if (q.Carried > 0)
            {
                // A winner carrying their score up to the next level.
                q.Narrate($"Welcome back, {q.Name}! You return to the edge of Razoria with {q.Carried} points "
                          + "from your last quest. Word of your success has reached the guardians, and their "
                          + "riddles will be harder this time. Three paths lie before you once more: the Razor "
                          + "Forest, where every trunk is marked with an @; the Kestrel Caverns, where small fierce "
                          + "birds listen at every port; and a torch-lit trail that climbs to the ruins of Castle "
                          + "Web Forms.");
            }
            else
            {
                q.Narrate($"Welcome, {q.Name}! You arrive at the edge of Razoria with nothing but a backpack and a "
                          + "valid cookie. Three paths lie before you: the Razor Forest, where every trunk is marked "
                          + "with an @; the Kestrel Caverns, where small fierce birds listen at every port; and a "
                          + "torch-lit trail that climbs to the ruins of Castle Web Forms.");
            }
            yield return new Choice(Rules.Paths.Select(p => p.Label).ToArray());
            chosen = int.Parse(q.Move) - 1;
        }
        q.Path = Rules.Paths[chosen].Key;
        var story = q.Path switch
        {
            "forest" => ForestPath(q),
            "cave" => CavePath(q),
            _ => CastlePath(q),
        };
        foreach (var prompt in story)
            yield return prompt;
    }

    // ------------------------------------------------------------------
    // The forest
    // ------------------------------------------------------------------

    static IEnumerable<Prompt> ForestPath(Quest q)
    {
        q.Banner("forest");
        q.Narrate("Towering trees close in around you, their leaves as thin and sharp as razors. An @ is cut into "
                  + "every trunk, marking the place where plain wood stops and something living begins. To your "
                  + "left, a stream murmurs through the ferns. To your right stands the Dependency Tree, so tall its "
                  + "top disappears into the mist, every branch resting on another. From up there, you could see "
                  + "for miles.");
        yield return new Choice("Follow the stream", "Climb the Dependency Tree");
        var route = q.Move == "1" ? StreamRoute(q) : TreeRoute(q);
        foreach (var prompt in route)
            yield return prompt;
    }

    static IEnumerable<Prompt> StreamRoute(Quest q)
    {
        q.Banner("waterfall");
        q.Narrate("You follow the stream until it plunges over a cliff, ledge after ledge, each one taking the water "
                  + "in turn and handing it on to the next. The spray swirls, rises, and takes the shape of a "
                  + "towering figure: the Middleware Spirit. \"All that passes through me, I may change or stop,\" it "
                  + "booms. \"None may go on until I call next.\"");
        foreach (var prompt in FaceChallenge(q, "The Middleware Spirit"))
            yield return prompt;
        if (!q.Passed)
        {
            GameOver(q, "The Middleware Spirit short-circuits. A great wave sweeps you downstream, and nothing further "
                        + "along the pipeline ever hears of you.");
            yield break;
        }

        q.Narrate("The Middleware Spirit bows, calls next, and places a shimmering pearl in your hand.");
        CollectRelic(q, "Pipeline Pearl");
        q.Narrate("It points a watery finger at a dark gap hidden behind the falls. Nearby, a fallen log "
                  + "covered in slick green moss stretches across the gorge. It looks like a quicker way "
                  + "across, with no checks of any kind.");
        yield return new Choice("Slip behind the falls, as the Middleware Spirit showed you",
                                "Cross the gorge on the mossy log");
        if (q.Move == "1")
        {
            AddPoints(q, Rules.WiseChoicePoints, "wise choice");
            q.Narrate("Behind the curtain of water, a hidden tunnel routes you straight to the steps of an "
                      + "ancient temple.");
            foreach (var prompt in TempleVault(q))
                yield return prompt;
            yield break;
        }
        GameOver(q, "Halfway across, your boot slips on the moss. You tumble into the rapids and are carried "
                    + "far from the session. Somewhere behind you, the Middleware Spirit sighs.");
    }

    static IEnumerable<Prompt> TreeRoute(Quest q)
    {
        q.Banner("tree");
        q.Narrate("You climb branch by branch, each one resting on the branch it depends on, until you break "
                  + "through the mist. Far to the east, a golden temple roof glints above the jungle. A great "
                  + "grey owl lands beside you and blinks. \"Hoo! I am the Singleton Owl. There is only one of me, "
                  + "and everyone who climbs this tree is given the same me. Only those who think like a programmer "
                  + "may learn the safe way down.\"");
        foreach (var prompt in FaceChallenge(q, "The Singleton Owl"))
            yield return prompt;
        if (!q.Passed)
        {
            GameOver(q, "The owl ruffles its feathers and flies away. As you reach after it, the branch beneath "
                        + "you snaps, its dependency unresolved...");
            yield break;
        }

        q.Narrate("\"Well reasoned!\" hoots the owl, and it plucks a feather for you.");
        CollectRelic(q, "Singleton Feather");
        q.Narrate("\"Now listen closely. The swamp below is the shortest way to the temple, but it swallows "
                  + "the careless. The vines are slow, but each one is scoped to your climb alone.\"");
        yield return new Choice("Swing along the vines toward the temple", "Climb down and take the swamp shortcut");
        if (q.Move == "1")
        {
            AddPoints(q, Rules.WiseChoicePoints, "wise choice");
            q.Narrate("Vine by vine, you swing through the canopy like a jungle acrobat and land softly on the "
                      + "temple steps.");
            foreach (var prompt in TempleVault(q))
                yield return prompt;
            yield break;
        }
        GameOver(q, "Three steps into the swamp, the mud grabs your boots. The harder you struggle, the deeper "
                    + "you sink, held captive for as long as the swamp lives. You should have listened to the owl!");
    }

    // ------------------------------------------------------------------
    // The cavern
    // ------------------------------------------------------------------

    static IEnumerable<Prompt> CavePath(Quest q)
    {
        q.Banner("cave");
        q.Narrate("Cold air flows from the mouth of the Kestrel Caverns. Small fierce birds watch from every crag, "
                  + "each one listening at a port of its own. Just inside, you find an old torch and a flint. "
                  + "Lighting it would help you see, but the light might also wake whatever is hissing in the "
                  + "dark...");
        yield return new Choice("Light the torch", "Proceed in the dark");
        if (q.Move == "1")
        {
            AddPoints(q, Rules.WiseChoicePoints, "wise choice");
            q.Narrate("The torch flares to life. Good thing, too: the floor ahead is riddled with deep pits, and "
                      + "someone has scratched \"404\" beside each one. The hissing, you realize, is only wind "
                      + "whistling through cracks in the rock.");
            foreach (var prompt in AuthorizeDoor(q))
                yield return prompt;
            yield break;
        }
        foreach (var prompt in NotFoundPit(q))
            yield return prompt;
    }

    static IEnumerable<Prompt> NotFoundPit(Quest q)
    {
        q.Banner("dark");
        q.Narrate("You creep forward in total darkness, one hand on the cold, damp wall, never once checking "
                  + "the route ahead. Suddenly the ground simply can't be found, and you tumble into a pit!");
        if (!LoseLife(q))
        {
            GameOver(q, "404 Not Found. The pit is far too deep to climb out of without light. Your quest ends "
                        + "here, in the dark.");
            yield break;
        }

        yield return new Choice("Climb out of the pit");
        q.Narrate("Bruised but alive, you claw your way out and crawl back to the entrance. This time you light "
                  + "the torch. Lesson learned: never assume a route is there! In its glow you can see the floor is "
                  + "riddled with pits.");
        foreach (var prompt in AuthorizeDoor(q))
            yield return prompt;
    }

    static IEnumerable<Prompt> AuthorizeDoor(Quest q)
    {
        q.Banner("glyph");
        q.Narrate("You weave between the pits until the tunnel ends at a massive stone door, with one word cut above "
                  + "it in square brackets: [Authorize]. It doesn't care who you say you are. Glowing letters crawl "
                  + "across its surface and rearrange themselves into lines of ASP.NET.");
        foreach (var prompt in FaceChallenge(q, "The Authorize Door"))
            yield return prompt;
        if (!q.Passed)
        {
            GameOver(q, "The letters flash red: 401 Unauthorized. With a deep rumble the tunnel behind you seals "
                        + "shut, and your torch flickers out...");
            yield break;
        }

        q.Narrate("The letters flash gold and the door grinds open. A small carved tablet falls from the wall at "
                  + "your feet.");
        CollectRelic(q, "Bearer Tablet");
        q.Narrate("Beyond the door the tunnel splits in two. From the left drifts warm air and a faint golden "
                  + "glow. The right tunnel is cold, its walls marked with fresh, deep claw scratches, and "
                  + "something in there is growling.");
        yield return new Choice("Take the left tunnel toward the golden glow", "Take the right tunnel past the claw marks");
        if (q.Move == "1")
        {
            AddPoints(q, Rules.WiseChoicePoints, "wise choice");
            q.Narrate("The golden glow grows brighter with every step until you emerge at the heart of an "
                      + "ancient temple.");
            foreach (var prompt in TempleVault(q))
                yield return prompt;
            yield break;
        }
        GameOver(q, "The claw marks belong to a very large, very grumpy cave bear, and its answer is 403 Forbidden. "
                    + "You flee all the way back to the entrance, your quest in ruins.");
    }

    // ------------------------------------------------------------------
    // The castle
    // ------------------------------------------------------------------

    static IEnumerable<Prompt> CastlePath(Quest q)
    {
        q.Banner("castle");
        q.Narrate("A winding stone trail climbs out of the mist to the ruins of Castle Web Forms, raised long ago by "
                  + "coders who dragged and dropped every stone into place. Torches still burn along the way, "
                  + "though no one has upgraded this place in a thousand years. The trail ends at the Antiforgery "
                  + "Gate. Beside it, a crumbling stair climbs the outer wall toward the ramparts.");
        yield return new Choice("Follow the torches to the Antiforgery Gate", "Climb the crumbling stair to the ramparts");
        var route = q.Move == "1" ? AntiforgeryGate(q) : Ramparts(q);
        foreach (var prompt in route)
            yield return prompt;
    }

    static IEnumerable<Prompt> AntiforgeryGate(Quest q)
    {
        q.Banner("gate");
        q.Narrate("Golden griffins glare down from tattered banners as you reach the gate. The iron portcullis "
                  + "is raised, but as you step beneath it a ghostly knight in rusted armor drifts out of the "
                  + "stone. \"Halt! Anyone can claim to come from inside these walls. Only a true coder, with a token "
                  + "this castle gave them itself, may pass.\"");
        foreach (var prompt in FaceChallenge(q, "The Antiforgery Knight"))
            yield return prompt;
        if (!q.Passed)
        {
            GameOver(q, "\"400 Bad Request,\" says the knight, and the portcullis crashes down. You are left outside "
                        + "in the dark, far from the session.");
            yield break;
        }

        q.Narrate("The knight lowers its sword and presses a cold silver ring into your palm.");
        CollectRelic(q, "Antiforgery Signet");
        q.Banner("hall");
        q.Narrate("Beyond the gate lies the Hall of Postbacks, its arches broken and open to the sky. Every step you "
                  + "take here brings you back to where you started, trailing a hidden scroll of everything that "
                  + "has ever happened in the room. Torches flicker beside an empty throne. Behind it, a narrow "
                  + "passage glows with a faint golden light. To one side, a grand staircase climbs into the dark, "
                  + "its steps cracked, crumbling and long since out of support.");
        yield return new Choice("Take the glowing passage behind the throne", "Climb the unsupported grand staircase");
        if (q.Move == "1")
        {
            AddPoints(q, Rules.WiseChoicePoints, "wise choice");
            q.Narrate("The passage winds down beneath the castle and comes out on the steps of an ancient temple.");
            foreach (var prompt in TempleVault(q))
                yield return prompt;
            yield break;
        }
        GameOver(q, "Halfway up, the staircase gives way beneath your feet. You tumble down in a cloud of dust, "
                    + "and Castle Web Forms keeps its secrets.");
    }

    static IEnumerable<Prompt> Ramparts(Quest q)
    {
        q.Banner("ramparts");
        q.Narrate("You climb onto the Ramparts of Redirects, where every path sends you somewhere else, and a few "
                  + "send you there permanently. The moon hangs over a sea of mist and the wind howls between the "
                  + "towers. On the wall ahead crouches a stone gargoyle. As you come near, its eyes crack open and "
                  + "glow. \"Answer me, climber, or be moved.\"");
        foreach (var prompt in FaceChallenge(q, "The Status Code Gargoyle"))
            yield return prompt;
        if (!q.Passed)
        {
            GameOver(q, "The gargoyle spreads its stone wings. \"301,\" it says. Moved permanently: one great gust "
                        + "sweeps you off the wall and into the mist.");
            yield break;
        }

        q.Narrate("The gargoyle grinds out a laugh and drops a glittering stone from its claw.");
        CollectRelic(q, "Redirect Stone");
        q.Banner("gallery");
        q.Narrate("The ramparts lead into a tall tower and up to a moonlit gallery. Far below the balustrade, a "
                  + "golden temple roof glints through the mist. Ivy as thick as rope hangs over the edge, and a "
                  + "spiral stair winds down inside the tower.");
        yield return new Choice("Take the spiral stair down inside the tower", "Climb down the ivy from the gallery");
        if (q.Move == "1")
        {
            AddPoints(q, Rules.WiseChoicePoints, "wise choice");
            q.Narrate("Round and round you go, down and down, like a request redirected again and again, until a "
                      + "small door at the foot of the tower opens beside the temple steps.");
            foreach (var prompt in TempleVault(q))
                yield return prompt;
            yield break;
        }
        GameOver(q, "The ivy is older than the .NET Framework itself. It tears loose with a snap, and you drop into "
                    + "the mist far below.");
    }

    // ------------------------------------------------------------------
    // The temple and the end of the quest
    // ------------------------------------------------------------------

    static IEnumerable<Prompt> TempleVault(Quest q)
    {
        q.Banner("temple");
        q.Narrate("Torches burst into flame as you enter the temple's great hall. At the far end stands the "
                  + "vault, held shut by two locks, Authentication and Authorization, each in the coils of a stone "
                  + "serpent. They have only ever opened in that order: first who you are, then what you may do. "
                  + "Beside the path sits a small jeweled chest with a riddle carved into its lid. Solving it would "
                  + "earn you a rare relic, but a wrong answer will cost you a life.");
        yield return new Choice("Try to open the jeweled chest", "Ignore the chest and head for the vault");
        if (q.Move == "1")
        {
            foreach (var prompt in AskQuestion(q, "The Jeweled Chest"))
                yield return prompt;
            if (q.Passed)
            {
                q.Narrate("Click! The lid springs open, revealing a ring set with a blazing garnet.");
                CollectRelic(q, "Garnet Ring");
            }
            else
            {
                if (!LoseLife(q))
                {
                    GameOver(q, "A dart coated in sleeping venom shoots from the lock. You doze off just steps away "
                                + "from the session, and it times out without you...");
                    yield break;
                }
                q.Narrate("A tiny dart shoots from the lock and stings your hand. The chest stays shut.");
            }
        }
        else
        {
            q.Narrate("You leave the chest alone. Sometimes the wisest move is not to send the request.");
        }

        q.Narrate("You approach the vault door. The eyes of the stone serpents begin to glow.");
        foreach (string lockName in new[] { "Authentication", "Authorization" })
        {
            foreach (var prompt in FaceChallenge(q, $"The {lockName} Lock"))
                yield return prompt;
            if (!q.Passed)
            {
                GameOver(q, $"{lockName} failed. The serpent's eyes flash red and the vault seals itself forever. "
                            + "The session remains lost.");
                yield break;
            }
            q.Note("info", $"The {lockName} Lock slides open!");
        }
        Victory(q);
    }

    static void Victory(Quest q)
    {
        q.Banner("victory");
        q.Narrate("The vault door swings open with a groan. Inside, resting on a pedestal of black stone, sits the "
                  + "legendary Golden Session, humming with everything it remembers and not a minute past its "
                  + $"timeout. Congratulations, {q.Name}! Your name will be carved among the great coders of Razoria.");
        AddPoints(q, Rules.TreasurePoints, "found the session");
        foreach (var relic in q.Inventory)
            AddPoints(q, Rules.RelicPoints, $"relic: {relic}");
        AddPoints(q, Rules.LifePoints * q.Lives, $"lives remaining: {q.Lives}");
        q.Result = "win";
    }

    static void GameOver(Quest q, string message)
    {
        q.Narrate(message);
        q.Banner("game_over");
        q.Result = "lose";
    }

    // ------------------------------------------------------------------
    // The bonus dragons, and the final boss
    // ------------------------------------------------------------------

    /// <summary>The bonus after a win: the riddle of the dragon of this path and level. Right, a
    /// share of its treasure; wrong, nothing lost. The quest stays won whatever the answer.</summary>
    public static IEnumerable<Prompt> DragonBattle(Quest q)
    {
        var dragon = Rules.Dragons[(q.Difficulty, q.Path!)];
        string name = Rules.Scenes[dragon.Scene].Banner;
        q.Banner(dragon.Scene);
        q.Narrate(Rules.Paths.First(p => p.Key == q.Path).Lair
                  + $" There, coiled around an overflowing treasure chest, sleeps the {name["The ".Length..]}, "
                  + $"its scales {dragon.Scales}. As you creep closer, one great eye slides open. \"A riddle, "
                  + "little coder,\" it rumbles. \"Answer well, and a share of my treasure is yours. Answer badly, "
                  + "and run.\"");
        foreach (var prompt in AskQuestion(q, name, dragon.Question, Rules.DragonPoints, "the dragon's treasure"))
            yield return prompt;
        if (q.Passed)
        {
            q.Dragon = "won";
            q.Narrate("The dragon rumbles a deep laugh and nudges its chest toward you with its snout. You fill your "
                      + "pockets with treasure and slip away.");
        }
        else
        {
            q.Dragon = "lost";
            q.Narrate("The dragon snorts a cloud of smoke, and you flee, empty-handed but unharmed.");
        }
    }

    /// <summary>The final boss, for a winner who has completed every path on every level: one of
    /// the nine ultimate questions, picked at random. Right: the title of ASP.NET Master and BossPoints
    /// besides. Wrong: all is lost, the score falls to zero.</summary>
    public static IEnumerable<Prompt> BossBattle(Quest q)
    {
        q.Banner("boss");
        q.Narrate("You have walked every path in Razoria. As you leave the temple for the last time, the jungle "
                  + "falls silent and a sickly yellow light spills down the temple steps. Something is unfolding at "
                  + "the top of them, torn page over torn page, until only the moon is left above it. The Yellow "
                  + "Screen of Death towers over you, a giant of glowing parchment with two burning red eyes and a "
                  + "mouth of ripped paper fangs. Across its chest, in great red letters: Server Error in '/' "
                  + "Application. Through a crack in the page below them shines a blue ASP.NET emblem, and below that "
                  + "one line of code burns brighter than the rest: Line 43, user.Name = txtName.Text. The line above "
                  + "it asked for Session[\"User\"], and nothing came back. Strips of stack trace wind down its arms to "
                  + "claws of crumpled paper, and torn signs swing on their chains around it: 500 Internal Server "
                  + "Error, Session Expired, NullReferenceException. \"An unhandled exception,\" it says, \"has occurred "
                  + "during the execution of the current web request. That exception is you. One question remains. "
                  + "Answer it, and you are an ASP.NET Master. Fail, and everything in your session is gone.\"");
        var question = Questions.Boss[q.Rng.Next(Questions.Boss.Length)];
        foreach (var prompt in AskQuestion(q, Rules.BossName, question, Rules.BossPoints, "ASP.NET Master"))
            yield return prompt;
        if (q.Passed)
        {
            q.Boss = "won";
            q.Narrate("The red letters across its chest flicker and fade to a plain 200 OK, and its eyes go dim. "
                      + "\"Handled,\" the Yellow Screen rumbles, and it almost sounds pleased. \"Well answered, Master.\" "
                      + "Page by page it folds itself away, and the moonlight comes back to the temple steps. From this "
                      + "day on, the coders of Razoria will know you by your new title.");
            q.Note("relic", "You are an ASP.NET Master!");
        }
        else
        {
            q.Boss = "lost";
            q.Score = 0;
            q.Narrate("The paper claws close, and strips of stack trace wind around you, frame after frame. Every coin, "
                      + "relic and point you carried is gone with your session, and you wake at the edge of Razoria with "
                      + "nothing but a backpack and an expired cookie.");
            q.Note("life", "All is lost! Your score falls to 0.");
        }
    }
}
