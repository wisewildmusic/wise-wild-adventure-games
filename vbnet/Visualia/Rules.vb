Public NotInheritable Class Level

    Public ReadOnly Property Lives As Integer
    Public ReadOnly Property Multiplier As Integer
    Public ReadOnly Property Topics As String

    Public Sub New(lives As Integer, multiplier As Integer, topics As String)
        Me.Lives = lives
        Me.Multiplier = multiplier
        Me.Topics = topics
    End Sub

End Class

Public NotInheritable Class GamePath

    Public ReadOnly Property Key As String
    Public ReadOnly Property Label As String
    Public ReadOnly Property Name As String
    Public ReadOnly Property Sight As String
    Public ReadOnly Property Lair As String

    Public Sub New(key As String, label As String, name As String, sight As String, lair As String)
        Me.Key = key
        Me.Label = label
        Me.Name = name
        Me.Sight = sight
        Me.Lair = lair
    End Sub

End Class

Public NotInheritable Class Scene

    Public ReadOnly Property Banner As String
    Public ReadOnly Property Picture As String
    Public ReadOnly Property Description As String

    Public Sub New(banner As String, picture As String, description As String)
        Me.Banner = banner
        Me.Picture = picture
        Me.Description = description
    End Sub

End Class

Public NotInheritable Class Dragon

    Public ReadOnly Property Scene As String
    Public ReadOnly Property Scales As String
    Public ReadOnly Property Question As Question

    Public Sub New(scene As String, scales As String, question As Question)
        Me.Scene = scene
        Me.Scales = scales
        Me.Question = question
    End Sub

End Class

''' <summary>The game's settings and wording. Pictures are shared with the other games, in the
''' site's static/img/adventure folder, apart from the NotInheritable Door's and the final boss's.</summary>
Public Module Rules

    ' Change GameVersion when the questions change. A quest keeps the version it started on and
    ' is always replayed with that version's questions: the first QuestionCounts(version) of
    ' each level's list (new questions only ever go on the end).
    Public Const GameVersion As Integer = 1
    Public ReadOnly QuestionCounts As New Dictionary(Of Integer, Integer) From {{1, 20}}

    ' Base point values. Each one is multiplied by the difficulty multiplier.
    Public Const CorrectAnswerPoints As Integer = 10
    Public Const WiseChoicePoints As Integer = 5
    Public Const RelicPoints As Integer = 15
    Public Const TreasurePoints As Integer = 50
    Public Const LifePoints As Integer = 10
    Public Const DragonPoints As Integer = 30
    Public Const BossPoints As Integer = 100

    Public Const DragonMove As String = "dragon"
    Public Const BossMove As String = "boss"
    Public Const BossName As String = "Nothing"

    Public ReadOnly Levels As New Dictionary(Of String, Level) From {
        {"easy", New Level(3, 1, "variables, types, arrays, If/Else, simple loops")},
        {"medium", New Level(2, 2, "Select Case, strings, collections, ByVal and ByRef, scope")},
        {"hard", New Level(1, 3, "LINQ, lambdas, classes, value vs reference, iterators")}
    }

    ' The three ways into Visualia, in the order the first choice offers them.
    Public ReadOnly Paths As GamePath() = {
        New GamePath("forest", "Explore the Dim Forest", "the Dim Forest",
            "the Dim Forest, where every tree must be declared before it may grow",
            "On your way back through the Dim Forest, a glint of gold catches your eye in a mossy hollow."),
        New GamePath("cave", "Enter the GoTo Caverns", "the GoTo Caverns",
            "the GoTo Caverns, where the tunnels jump without warning",
            "On your way back out of the GoTo Caverns, a glint of gold catches your eye in a side cave."),
        New GamePath("castle", "Climb to the Ruins of Castle Classic", "the Ruins of Castle Classic",
            "the torch-lit trail that climbs to the ruins of Castle Classic",
            "On your way back through Castle Classic, a glint of gold catches your eye through a doorway: " &
            "a forgotten treasury.")
    }

    Public ReadOnly Scenes As New Dictionary(Of String, Scene) From {
        {"start", New Scene("The Lost Runtime of Visualia", "title.webp",
            "A moonlit jungle valley wrapped in mist, a golden temple glowing on a far hilltop")},
        {"forest", New Scene("The Dim Forest", "forest.webp",
            "Sunbeams falling through towering trees onto a stream, ferns and one giant mossy tree")},
        {"waterfall", New Scene("Select Case Falls", "waterfall.webp",
            "A roaring waterfall crashing into a green pool between mossy cliffs, a fallen log high across the gorge")},
        {"tree", New Scene("The Inherits Tree", "tree.webp",
            "A great owl on a mossy branch above a sea of mist at sunrise, a golden temple glinting in the distance")},
        {"cave", New Scene("The GoTo Caverns", "cave.webp",
            "A dark cave mouth framed by carved stone serpents, a torch burning beside it")},
        {"dark", New Scene("The Nothing Pit", "pit.webp",
            "A deep pit in the floor of a rocky tunnel, the cave entrance glowing far behind")},
        {"glyph", New Scene("The NotInheritable Door", "glyph-door-vbnet.webp",
            "A massive stone door glowing with lines of VB.NET code, fire bowls burning on either side")},
        {"castle", New Scene("The Ruins of Castle Classic", "castle.webp",
            "A ruined castle on a misty hilltop under a full moon, torches lighting the stone path that winds up to it")},
        {"gate", New Scene("The Friend Gate", "castle-gate.webp",
            "A great arched gate with a raised iron portcullis, griffin banners and blazing torches on ivy-covered walls")},
        {"hall", New Scene("The Hall of Forms", "great-hall.webp",
            "A ruined great hall of broken gothic arches, torches flickering beside an empty throne at the top of worn steps")},
        {"ramparts", New Scene("The Ramparts of On Error", "ramparts.webp",
            "Torch-lit battlements under a full moon, stone towers rising above a misty valley")},
        {"gallery", New Scene("The Moonlit Gallery", "gallery.webp",
            "A stone gallery high in a tower, ivy twisting around its pillars, the full moon over a misty valley beyond the balustrade")},
        {"temple", New Scene("The Temple of the Golden Runtime", "temple.webp",
            "A torch-lit temple hall leading to a golden vault door guarded by two stone serpents, a jeweled chest by the path")},
        {"victory", New Scene("The Runtime Is Yours!", "treasure.webp",
            "The Golden Runtime: a glowing golden orb wrapped by a serpent, on a stone pedestal among gold and gems")},
        {"dragon-emerald", New Scene("The Emerald Dragon", "dragon-emerald.webp",
            "A green dragon asleep in a cave, curled around an open treasure chest full of gold and emeralds")},
        {"dragon-ember", New Scene("The Ember Dragon", "dragon-ember.webp",
            "A red dragon asleep in a fiery cave around a treasure chest of gold and rubies, a sword and a crown beside it")},
        {"dragon-frost", New Scene("The Frost Dragon", "dragon-frost.webp",
            "A blue dragon asleep in an ice cave, its treasure chest full of gold and glowing sapphires")},
        {"dragon-pearl", New Scene("The Pearl Dragon", "dragon-pearl.webp",
            "A white dragon asleep in a sunlit forest beside a treasure chest of gold, diamonds and a silver crown")},
        {"dragon-amethyst", New Scene("The Amethyst Dragon", "dragon-amethyst.webp",
            "A purple dragon coiled around a treasure chest of gold and glowing amethysts in a violet forest")},
        {"dragon-autumn", New Scene("The Autumn Dragon", "dragon-autumn.webp",
            "A copper dragon asleep among autumn leaves beside a treasure chest of gold and a golden goblet")},
        {"dragon-gold", New Scene("The Golden Dragon", "dragon-gold.webp",
            "A golden dragon asleep on a heap of gold coins beside a treasure chest in a torch-lit castle hall")},
        {"dragon-silver", New Scene("The Silver Dragon", "dragon-silver.webp",
            "A silver dragon asleep in a castle hall beside a chest of silver and diamonds, a knight's helmet and a sword")},
        {"dragon-shadow", New Scene("The Shadow Dragon", "dragon-shadow.webp",
            "A black dragon asleep in a castle hall around a chest of gold and rubies, a jeweled crown at its feet")},
        {"boss", New Scene(BossName, "nothing.webp",
            "A towering hooded giant of black rags with glowing violet eyes and huge clawed hands, a swirling hole in " &
            "its chest with the word Nothing glowing in it, looming over a stone hall full of violet mist. A small " &
            "robed explorer in a VB.NET cloak faces it on the steps, raising a glowing staff, between banners of " &
            "VB.NET keywords and signs reading Dim obj As Object = Nothing, If obj Is Nothing Then, If obj IsNot " &
            "Nothing Then and obj = Nothing")},
        {"game_over", New Scene("Run-time Error 91", "game-over.webp",
            "A burnt-out torch and a lost compass on rocky ground under a blood-red sky")}
    }

    Public ReadOnly Dragons As New Dictionary(Of (Level As String, Path As String), Dragon) From {
        {("easy", "cave"), New Dragon("dragon-emerald", "green as moss", Questions.Dragons(("easy", "cave")))},
        {("medium", "cave"), New Dragon("dragon-ember", "glowing like hot coals", Questions.Dragons(("medium", "cave")))},
        {("hard", "cave"), New Dragon("dragon-frost", "glittering with ice", Questions.Dragons(("hard", "cave")))},
        {("easy", "forest"), New Dragon("dragon-pearl", "white as moonlight", Questions.Dragons(("easy", "forest")))},
        {("medium", "forest"), New Dragon("dragon-amethyst", "a deep, shimmering purple", Questions.Dragons(("medium", "forest")))},
        {("hard", "forest"), New Dragon("dragon-autumn", "the color of falling leaves", Questions.Dragons(("hard", "forest")))},
        {("easy", "castle"), New Dragon("dragon-gold", "as bright as the coins beneath it", Questions.Dragons(("easy", "castle")))},
        {("medium", "castle"), New Dragon("dragon-silver", "gleaming like polished armor", Questions.Dragons(("medium", "castle")))},
        {("hard", "castle"), New Dragon("dragon-shadow", "as black as a moonless night", Questions.Dragons(("hard", "castle")))}
    }

    Public ReadOnly Intro As String() = {
        "Long ago, the first coders of Visualia forged their greatest treasure, the Golden Runtime, and " &
        "hid it deep within this wild land. Its guardians still test every traveler, with riddles in the " &
        "language of the realm, the one that reads most nearly like plain English: Visual Basic .NET.",
        "One law holds throughout Visualia: Option Strict is On, unless a riddle says otherwise.",
        "Answer wisely and choose your path carefully. Every wrong answer costs you a life, and some " &
        "choices lead to certain doom..."
    }

    ' The page's own words for this game, by the same keys as the Python game's (pythonia.TEXTS).
    Public ReadOnly Texts As New Dictionary(Of String, String) From {
        {"title", "The Lost Runtime of Visualia"},
        {"language", "VB.NET"},
        {"found", "Found the runtime"},
        {"master", "VB.NET Master"},
        {"lost_to_boss", "Lost to Nothing"},
        {"hall_note", "Walk every path on every level to face Nothing."},
        {"boss_offer_title", "The final challenge: Nothing"},
        {"boss_offer", "You have walked every path on every level, and only Nothing is left to face: what every " &
            "variable holds before it holds anything. Answer its question, the hardest in all of Visualia, to " &
            "earn the title of VB.NET Master and {points} points."},
        {"boss_warning", "Beware: if you fail, all is lost. Your score is set to Nothing, which for an Integer " &
            "means 0, and you must start over."},
        {"boss_button", "Face Nothing"},
        {"boss_confirm", "Face Nothing? If you fail, all is lost: your score falls to zero and you must start over."},
        {"boss_won", "You have defeated Nothing. You are a VB.NET Master!"},
        {"boss_lost", "You have lost to Nothing. All is lost: your score has been set to Nothing, which for an " &
            "Integer means 0, and you must start over."},
        {"conquered_every_path", "Every path on every level: you've explored all of Visualia!"},
        {"conquered_every_level", "Easy, Medium and Hard: you've conquered every level of Visualia!"}
    }

End Module
