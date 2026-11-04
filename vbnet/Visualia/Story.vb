''' <summary>The adventure itself. Each part of the story is a VB iterator: `Yield` hands the page a
''' prompt, and the story carries on from there with the explorer's move in q.Move. `For Each ...
''' Yield` walks through a smaller part of the story. A part that has an outcome leaves it in
''' q.Passed.</summary>
Public Module Story

    ' ------------------------------------------------------------------
    ' Helpers
    ' ------------------------------------------------------------------

    Private Sub AddPoints(q As Quest, basePoints As Integer, reason As String)
        Dim points = basePoints * Rules.Levels(q.Difficulty).Multiplier
        q.Score += points
        q.Note("points", $"+{points} points ({reason})")
    End Sub

    ''' <summary>Takes away one life. Returns True if the explorer still has lives left.</summary>
    Private Function LoseLife(q As Quest) As Boolean
        q.Lives -= 1
        q.Note("life", If(q.Lives > 0, $"You lose a life! Lives remaining: {q.Lives}", "You have no lives left!"))
        Return q.Lives > 0
    End Function

    Private Sub CollectRelic(q As Quest, relic As String)
        q.Inventory.Add(relic)
        q.Note("relic", $"You found a relic: {relic}!")
    End Sub

    ''' <summary>The next question from the explorer's deck, reshuffling when it runs out. A path
    ''' not taken yet starts with a deck of the questions the level's earlier paths didn't ask. A
    ''' quest asks at most 6, so a level's 20 questions are enough for all three paths.</summary>
    Private Function DrawQuestion(q As Quest) As Question
        If q.Deck.Count = 0 Then
            Dim every = Enumerable.Range(0, Rules.QuestionCounts(q.Version)).ToList()
            Dim unasked = If(q.Asked.Count = 0,
                             every.Where(Function(n) Not q.SkipQuestions.Contains(n)).ToList(),
                             New List(Of Integer))
            q.Deck = If(unasked.Count > 0, unasked, every)
            Game.Shuffle(q.Rng, q.Deck)
        End If
        Dim number = q.Deck(q.Deck.Count - 1)
        q.Deck.RemoveAt(q.Deck.Count - 1)
        q.Asked.Add(number)
        Return Questions.Levels(q.Difficulty)(number)
    End Function

    ''' <summary>Asks one VB.NET question: the next from the deck, or `given` (a dragon's or the
    ''' boss's). Leaves q.Passed True if the answer is right, and earns `points`.</summary>
    Private Iterator Function AskQuestion(q As Quest, challenger As String, Optional given As Question = Nothing,
                                          Optional points As Integer = Rules.CorrectAnswerPoints,
                                          Optional reason As String = "correct answer") As IEnumerable(Of Prompt)
        Dim question = If(given, DrawQuestion(q))
        Dim options = question.Options.ToArray()
        Game.Shuffle(q.Rng, options)

        Yield New Challenge(challenger, question, options)

        Dim correctLetter = Game.Letters(Array.IndexOf(options, question.Answer))
        q.Passed = q.Move = correctLetter
        If q.Passed Then
            q.Note("correct", "Correct!")
            AddPoints(q, points, reason)
        Else
            q.Note("wrong", $"{correctLetter}) {question.Answer}")
        End If
        q.Note("why", question.Explain)
    End Function

    ''' <summary>Asks questions until one is answered correctly. Each wrong answer costs a life.
    ''' Leaves q.Passed False if the explorer runs out of lives.</summary>
    Private Iterator Function FaceChallenge(q As Quest, challenger As String) As IEnumerable(Of Prompt)
        Do
            For Each prompt In AskQuestion(q, challenger)
                Yield prompt
            Next
            If q.Passed Then Return
            If Not LoseLife(q) Then Return
            q.Note("info", $"{challenger} gives you another chance...")
        Loop
    End Function

    ' ------------------------------------------------------------------
    ' The start
    ' ------------------------------------------------------------------

    Public Iterator Function StartGame(q As Quest) As IEnumerable(Of Prompt)
        q.Banner("start")
        Dim chosen As Integer
        If q.OnlyPath IsNot Nothing Then
            ' A winner going back for a path they didn't take, score and all.
            Dim path = Rules.Paths.First(Function(p) p.Key = q.OnlyPath)
            Dim fresh = If(q.SkipQuestions.Count > 0, ", where new riddles await", "")
            q.Narrate($"Welcome back, {q.Name}! You return to the edge of Visualia with {q.Carried} points " &
                      "from your last quest, wondering what waits down the way you didn't take. " &
                      $"This time you turn toward {path.Sight}{fresh}.")
            Yield New Choice(path.Label)
            chosen = Array.IndexOf(Rules.Paths, path)
        Else
            If q.Carried > 0 Then
                ' A winner carrying their score up to the next level.
                q.Narrate($"Welcome back, {q.Name}! You return to the edge of Visualia with {q.Carried} points " &
                          "from your last quest. Word of your success has reached the guardians, and their " &
                          "riddles will be harder this time. Three paths lie before you once more: the Dim " &
                          "Forest, where every tree must be declared before it may grow; the GoTo Caverns, " &
                          "where the tunnels jump without warning; and a torch-lit trail that climbs to the " &
                          "ruins of Castle Classic.")
            Else
                q.Narrate($"Welcome, {q.Name}! You arrive at the edge of Visualia with Nothing but a backpack " &
                          "and your wits. Nobody here minds how you capitalize your name: in Visualia, ADA and " &
                          "ada are the same explorer. Three paths lie before you: the Dim Forest, where every " &
                          "tree must be declared before it may grow; the GoTo Caverns, where the tunnels jump " &
                          "without warning; and a torch-lit trail that climbs to the ruins of Castle Classic.")
            End If
            Yield New Choice(Rules.Paths.Select(Function(p) p.Label).ToArray())
            chosen = Integer.Parse(q.Move) - 1
        End If
        q.Path = Rules.Paths(chosen).Key
        Dim route As IEnumerable(Of Prompt)
        Select Case q.Path
            Case "forest"
                route = ForestPath(q)
            Case "cave"
                route = CavePath(q)
            Case Else
                route = CastlePath(q)
        End Select
        For Each prompt In route
            Yield prompt
        Next
    End Function

    ' ------------------------------------------------------------------
    ' The forest
    ' ------------------------------------------------------------------

    Private Iterator Function ForestPath(q As Quest) As IEnumerable(Of Prompt)
        q.Banner("forest")
        q.Narrate("The trees close in until the daylight grows dim, every trunk with a label carved into its " &
                  "bark: Dim Oak As Tree, Dim Elm As Tree, Dim Ash As Tree. Nothing grows here without being " &
                  "declared first. To your left, a stream murmurs through the ferns. To your right stands the " &
                  "Inherits Tree, so tall its top disappears into the mist. From up there, you could see for miles.")
        Yield New Choice("Follow the stream", "Climb the Inherits Tree")
        For Each prompt In If(q.Move = "1", StreamRoute(q), TreeRoute(q))
            Yield prompt
        Next
    End Function

    Private Iterator Function StreamRoute(q As Quest) As IEnumerable(Of Prompt)
        q.Banner("waterfall")
        q.Narrate("You follow the stream until it plunges over a cliff in a roaring waterfall. Here the water " &
                  "parts into many channels and each drop takes exactly one: at Select Case Falls, nothing ever " &
                  "falls through to the next. The spray swirls, rises, and takes the shape of a towering figure: " &
                  "the Case Guardian. ""None may pass,"" it booms, ""until they have answered.""")
        For Each prompt In FaceChallenge(q, "The Case Guardian")
            Yield prompt
        Next
        If Not q.Passed Then
            GameOver(q, """Case Else,"" says the Guardian, and a great wave sweeps you downstream, far away from " &
                        "the runtime.")
            Return
        End If

        q.Narrate("The Case Guardian bows and places a shimmering pearl in your hand.")
        CollectRelic(q, "Case Pearl")
        q.Narrate("It points a watery finger at a dark gap hidden behind the falls. Nearby, a fallen log " &
                  "covered in slick green moss stretches across the gorge. It looks like a quicker way " &
                  "across, with no checks of any kind.")
        Yield New Choice("Slip behind the falls, as the Case Guardian showed you",
                         "Cross the gorge on the mossy log")
        If q.Move = "1" Then
            AddPoints(q, Rules.WiseChoicePoints, "wise choice")
            q.Narrate("Behind the curtain of water, a hidden tunnel leads you straight to the steps of an " &
                      "ancient temple.")
            For Each prompt In TempleVault(q)
                Yield prompt
            Next
            Return
        End If
        GameOver(q, "Halfway across, your boot slips on the moss. You tumble into the rapids and are carried " &
                    "far from the runtime. Somewhere behind you, the Case Guardian sighs.")
    End Function

    Private Iterator Function TreeRoute(q As Quest) As IEnumerable(Of Prompt)
        q.Banner("tree")
        q.Narrate("You climb branch by branch, each one Inherits from the branch below, until you break " &
                  "through the mist. Far to the east, a golden temple roof glints above the jungle. A great " &
                  "grey owl lands beside you and blinks. ""Hoo! I am MyBase, and all who climb here inherit " &
                  "from me. Only those who think like a programmer may learn the safe way down.""")
        For Each prompt In FaceChallenge(q, "The MyBase Owl")
            Yield prompt
        Next
        If Not q.Passed Then
            GameOver(q, "The owl ruffles its feathers and flies away. As you reach after it, the branch beneath " &
                        "you snaps...")
            Return
        End If

        q.Narrate("""Well reasoned!"" hoots the owl, and it plucks a feather for you.")
        CollectRelic(q, "MyBase Feather")
        q.Narrate("""Now listen closely. The swamp below is the shortest way to the temple, but it's late bound: " &
                  "you won't find out what's in it until you're in it. The vines are slow, but Option Strict.""")
        Yield New Choice("Swing along the vines toward the temple", "Climb down and take the swamp shortcut")
        If q.Move = "1" Then
            AddPoints(q, Rules.WiseChoicePoints, "wise choice")
            q.Narrate("Vine by vine, you swing through the canopy like a jungle acrobat and land softly on the " &
                      "temple steps.")
            For Each prompt In TempleVault(q)
                Yield prompt
            Next
            Return
        End If
        GameOver(q, "Three steps into the swamp, the mud grabs your boots. What's in it turns out, at run time, " &
                    "to be you, and the harder you struggle, the deeper you sink. You should have listened to the owl!")
    End Function

    ' ------------------------------------------------------------------
    ' The caverns
    ' ------------------------------------------------------------------

    Private Iterator Function CavePath(q As Quest) As IEnumerable(Of Prompt)
        q.Banner("cave")
        q.Narrate("Cold air flows from the mouth of the GoTo Caverns, a tangle of tunnels that twist back on " &
                  "themselves like spaghetti. Labels are scratched into the walls, and whole passages jump to " &
                  "them without warning. Just inside, you find an old torch and a flint. Lighting it would help " &
                  "you see, but the light might also wake whatever is hissing in the dark...")
        Yield New Choice("Light the torch", "Proceed in the dark")
        If q.Move = "1" Then
            AddPoints(q, Rules.WiseChoicePoints, "wise choice")
            q.Narrate("The torch flares to life. Good thing, too: the floor ahead is riddled with deep pits, and " &
                      "someone has scratched ""Is Nothing"" beside each one. The hissing, you realize, is only " &
                      "wind whistling through cracks in the rock.")
            For Each prompt In NotInheritableDoor(q)
                Yield prompt
            Next
            Return
        End If
        For Each prompt In NothingPit(q)
            Yield prompt
        Next
    End Function

    Private Iterator Function NothingPit(q As Quest) As IEnumerable(Of Prompt)
        q.Banner("dark")
        q.Narrate("You creep forward in total darkness, one hand on the cold, damp wall, never once checking " &
                  "what's ahead. Suddenly there is Nothing under your feet, and you tumble into a pit!")
        If Not LoseLife(q) Then
            GameOver(q, "Object reference not set to an instance of an object. The pit is far too deep to climb " &
                        "out of without light. Your quest ends here, in the dark.")
            Return
        End If

        Yield New Choice("Climb out of the pit")
        q.Narrate("Bruised but alive, you claw your way out and crawl back to the entrance. This time you light " &
                  "the torch. Lesson learned: always check If ground IsNot Nothing! In its glow you can see the " &
                  "floor is riddled with pits.")
        For Each prompt In NotInheritableDoor(q)
            Yield prompt
        Next
    End Function

    Private Iterator Function NotInheritableDoor(q As Quest) As IEnumerable(Of Prompt)
        q.Banner("glyph")
        q.Narrate("You weave between the pits until the tunnel ends at a massive stone door, marked " &
                  "NotInheritable: nothing may derive from it, and nothing may pass. Glowing letters crawl across " &
                  "its surface and rearrange themselves into lines of VB.NET.")
        For Each prompt In FaceChallenge(q, "The NotInheritable Door")
            Yield prompt
        Next
        If Not q.Passed Then
            GameOver(q, "The letters flash red. With a deep rumble the tunnel behind you seals shut, and your " &
                        "torch flickers out...")
            Return
        End If

        q.Narrate("The letters flash gold and the door grinds open. A small carved tablet falls from the wall at " &
                  "your feet.")
        CollectRelic(q, "NotInheritable Tablet")
        q.Narrate("Beyond the door the tunnel splits in two. From the left drifts warm air and a faint golden " &
                  "glow. The right tunnel is cold, its walls marked with fresh, deep claw scratches, and " &
                  "something in there is growling.")
        Yield New Choice("Take the left tunnel toward the golden glow", "Take the right tunnel past the claw marks")
        If q.Move = "1" Then
            AddPoints(q, Rules.WiseChoicePoints, "wise choice")
            q.Narrate("The golden glow grows brighter with every step until you emerge at the heart of an " &
                      "ancient temple.")
            For Each prompt In TempleVault(q)
                Yield prompt
            Next
            Return
        End If
        GameOver(q, "The claw marks belong to a very large, very grumpy cave bear, and there is no On Error for " &
                    "that. You flee all the way back to the entrance, your quest in ruins.")
    End Function

    ' ------------------------------------------------------------------
    ' The castle
    ' ------------------------------------------------------------------

    Private Iterator Function CastlePath(q As Quest) As IEnumerable(Of Prompt)
        q.Banner("castle")
        q.Narrate("A winding stone trail climbs out of the mist to the ruins of Castle Classic, raised long ago " &
                  "by the coders of VB6 and left behind when the world moved on to .NET. Torches still burn along " &
                  "the way, because nobody ever quite managed to turn them off. The trail ends at the Friend Gate. " &
                  "Beside it, a crumbling stair climbs the outer wall toward the ramparts.")
        Yield New Choice("Follow the torches to the Friend Gate", "Climb the crumbling stair to the ramparts")
        For Each prompt In If(q.Move = "1", FriendGate(q), Ramparts(q))
            Yield prompt
        Next
    End Function

    Private Iterator Function FriendGate(q As Quest) As IEnumerable(Of Prompt)
        q.Banner("gate")
        q.Narrate("Golden griffins glare down from tattered banners as you reach the gate. The iron portcullis " &
                  "is raised, but as you step beneath it a ghostly knight in rusted armor drifts out of the " &
                  "stone. ""Halt! This castle's members are Private. Only a Friend may pass.""")
        For Each prompt In FaceChallenge(q, "The Private Sentinel")
            Yield prompt
        Next
        If Not q.Passed Then
            GameOver(q, """Not accessible in this context because it is Private,"" says the sentinel, and the " &
                        "portcullis crashes down. You are left outside in the dark, far from the runtime.")
            Return
        End If

        q.Narrate("""Friend,"" says the sentinel. It lowers its sword and presses a cold silver ring into your palm.")
        CollectRelic(q, "Friend Signet")
        q.Banner("hall")
        q.Narrate("Beyond the gate lies the Hall of Forms, its arches broken and open to the sky: every empty " &
                  "window here was once called Form1, and no one is left to click its buttons. Torches flicker " &
                  "beside an empty throne. Behind it, a narrow passage glows with a faint golden light. To one " &
                  "side, a grand staircase climbs into the dark, its steps cracked, crumbling and long since " &
                  "marked Obsolete.")
        Yield New Choice("Take the glowing passage behind the throne", "Climb the Obsolete grand staircase")
        If q.Move = "1" Then
            AddPoints(q, Rules.WiseChoicePoints, "wise choice")
            q.Narrate("The passage winds down beneath the castle and comes out on the steps of an ancient temple.")
            For Each prompt In TempleVault(q)
                Yield prompt
            Next
            Return
        End If
        GameOver(q, "Halfway up, the staircase gives way beneath your feet. You tumble down in a cloud of dust, " &
                    "and Castle Classic keeps its secrets.")
    End Function

    Private Iterator Function Ramparts(q As Quest) As IEnumerable(Of Prompt)
        q.Banner("ramparts")
        q.Narrate("You climb onto the Ramparts of On Error, where many have fallen and the watch has never once " &
                  "looked up: whatever goes wrong here, they simply Resume Next. The moon hangs over a sea of mist " &
                  "and the wind howls between the towers. On the wall ahead crouches a stone gargoyle. As you come " &
                  "near, its eyes crack open and glow. ""Answer me, climber, or fall. Nobody here will notice.""")
        For Each prompt In FaceChallenge(q, "The Resume Next Gargoyle")
            Yield prompt
        Next
        If Not q.Passed Then
            GameOver(q, "The gargoyle spreads its stone wings, and one great gust sweeps you off the wall and into " &
                        "the mist. The watch doesn't even turn around. It resumes next.")
            Return
        End If

        q.Narrate("The gargoyle grinds out a laugh and drops a glittering stone from its claw.")
        CollectRelic(q, "Resume Stone")
        q.Banner("gallery")
        q.Narrate("The ramparts lead into a tall tower and up to a moonlit gallery. Far below the balustrade, a " &
                  "golden temple roof glints through the mist. Ivy as thick as rope hangs over the edge, and a " &
                  "spiral stair winds down inside the tower.")
        Yield New Choice("Take the spiral stair down inside the tower", "Climb down the ivy from the gallery")
        If q.Move = "1" Then
            AddPoints(q, Rules.WiseChoicePoints, "wise choice")
            q.Narrate("Round and round you go, down and down, a Do Loop with an honest Until, and at last a small " &
                      "door at the foot of the tower opens beside the temple steps.")
            For Each prompt In TempleVault(q)
                Yield prompt
            Next
            Return
        End If
        GameOver(q, "The ivy is older than .NET itself. It tears loose with a snap, and you drop into the mist far " &
                    "below.")
    End Function

    ' ------------------------------------------------------------------
    ' The temple and the end of the quest
    ' ------------------------------------------------------------------

    Private Iterator Function TempleVault(q As Quest) As IEnumerable(Of Prompt)
        q.Banner("temple")
        q.Narrate("Torches burst into flame as you enter the temple's great hall. At the far end stands the " &
                  "vault, held shut by two locks, Option Explicit and Option Strict, each in the coils of a stone " &
                  "serpent: trophies, they say, taken from a rival language. Beside the path sits a small jeweled " &
                  "chest with a riddle carved into its lid. Solving it would earn you a rare relic, but a wrong " &
                  "answer will cost you a life.")
        Yield New Choice("Try to open the jeweled chest", "Ignore the chest and head for the vault")
        If q.Move = "1" Then
            For Each prompt In AskQuestion(q, "The Jeweled Chest")
                Yield prompt
            Next
            If q.Passed Then
                q.Narrate("Click! The lid springs open, revealing a ring set with a blazing topaz.")
                CollectRelic(q, "Topaz Ring")
            Else
                If Not LoseLife(q) Then
                    GameOver(q, "A dart coated in sleeping venom shoots from the lock. You doze off just steps away " &
                                "from the runtime...")
                    Return
                End If
                q.Narrate("A tiny dart shoots from the lock and stings your hand. The chest stays shut.")
            End If
        Else
            q.Narrate("You leave the chest alone. Sometimes the wisest move is to leave a Sub uncalled.")
        End If

        q.Narrate("You approach the vault door. The eyes of the stone serpents begin to glow.")
        For Each lockName In {"Option Explicit", "Option Strict"}
            For Each prompt In FaceChallenge(q, $"The {lockName} Lock")
                Yield prompt
            Next
            If Not q.Passed Then
                GameOver(q, $"{lockName} is not satisfied. The serpent's eyes flash red and the vault seals itself " &
                            "forever. The runtime remains lost.")
                Return
            End If
            q.Note("info", $"The {lockName} Lock slides open!")
        Next
        Victory(q)
    End Function

    Private Sub Victory(q As Quest)
        q.Banner("victory")
        q.Narrate("The vault door swings open with a groan. Inside, resting on a pedestal of black stone, sits the " &
                  "legendary Golden Runtime, humming with ancient power. Congratulations, " &
                  $"{q.Name}! Your name will be carved among the great coders of Visualia.")
        AddPoints(q, Rules.TreasurePoints, "found the runtime")
        For Each relic In q.Inventory
            AddPoints(q, Rules.RelicPoints, $"relic: {relic}")
        Next
        AddPoints(q, Rules.LifePoints * q.Lives, $"lives remaining: {q.Lives}")
        q.Result = "win"
    End Sub

    Private Sub GameOver(q As Quest, message As String)
        q.Narrate(message)
        q.Banner("game_over")
        q.Result = "lose"
    End Sub

    ' ------------------------------------------------------------------
    ' The bonus dragons, and the final boss
    ' ------------------------------------------------------------------

    ''' <summary>The bonus after a win: the riddle of the dragon of this path and level. Right, a
    ''' share of its treasure; wrong, nothing lost. The quest stays won whatever the answer.</summary>
    Public Iterator Function DragonBattle(q As Quest) As IEnumerable(Of Prompt)
        Dim dragon = Rules.Dragons((q.Difficulty, q.Path))
        Dim name = Rules.Scenes(dragon.Scene).Banner
        q.Banner(dragon.Scene)
        q.Narrate(Rules.Paths.First(Function(p) p.Key = q.Path).Lair &
                  $" There, coiled around an overflowing treasure chest, sleeps the {name.Substring("The ".Length)}, " &
                  $"its scales {dragon.Scales}. As you creep closer, one great eye slides open. ""A riddle, " &
                  "little coder,"" it rumbles. ""Answer well, and a share of my treasure is yours. Answer badly, " &
                  "and run.""")
        For Each prompt In AskQuestion(q, name, dragon.Question, Rules.DragonPoints, "the dragon's treasure")
            Yield prompt
        Next
        If q.Passed Then
            q.Dragon = "won"
            q.Narrate("The dragon rumbles a deep laugh and nudges its chest toward you with its snout. You fill your " &
                      "pockets with treasure and slip away.")
        Else
            q.Dragon = "lost"
            q.Narrate("The dragon snorts a cloud of smoke, and you flee, empty-handed but unharmed.")
        End If
    End Function

    ''' <summary>The final boss, for a winner who has completed every path on every level: one of
    ''' the nine ultimate questions, picked at random. Right: the title of VB.NET Master and BossPoints
    ''' besides. Wrong: all is lost, the score is set to Nothing.</summary>
    Public Iterator Function BossBattle(q As Quest) As IEnumerable(Of Prompt)
        q.Banner("boss")
        q.Narrate("You have walked every path in Visualia. As you leave the temple for the last time, the sounds " &
                  "of the jungle do not fade: they simply stop. The way back is gone. In its place, worn steps climb " &
                  "into a ruined hall, between banners of VB.NET and torches guttering in a violet mist. You climb, " &
                  "and at the top the dark stands up: a hooded giant of rags and shadow, clawed hands spreading wide, " &
                  "two violet eyes burning in a hood with no face in it. Where its heart should be, a hole turns " &
                  "slowly in the world, and one word glows in it: Nothing. It is what every variable holds before it " &
                  "holds anything, and what waits at the bottom of every pit. ""Every path, every level,"" says a " &
                  "voice from no direction. ""And still you fear Nothing? One question remains. Answer it, and you " &
                  "are a VB.NET Master. Fail, and you will be set to Me.""")
        Dim question = Questions.Boss(q.Rng.Next(Questions.Boss.Length))
        For Each prompt In AskQuestion(q, Rules.BossName, question, Rules.BossPoints, "VB.NET Master")
            Yield prompt
        Next
        If q.Passed Then
            q.Boss = "won"
            q.Narrate("The giant wavers, thins and comes apart like smoke, the violet mist drains away, and somewhere " &
                      "a bird starts singing as if it had never stopped. ""IsNot Nothing,"" the voice murmurs, already " &
                      "far away, and it almost sounds pleased. From this day on, the coders of Visualia will know you " &
                      "by your new title.")
            q.Note("relic", "You are a VB.NET Master!")
        Else
            q.Boss = "lost"
            q.Score = Nothing  ' Just as the boss warned: an Integer set to Nothing is 0.
            q.Narrate("The great claws close, and the dark closes with them, without a sound. Every coin, relic and " &
                      "point you carried is set to Nothing, and for an Integer that means 0. You wake at the edge of " &
                      "Visualia with Nothing but a backpack and your wits.")
            q.Note("life", "All is lost! Your score falls to 0.")
        End If
    End Function

End Module
