Imports System.Text.Json

''' <summary>What the game is waiting for: a menu of choices, or a VB.NET challenge.</summary>
Public MustInherit Class Prompt

    Public MustOverride ReadOnly Property Kind As String
    Public MustOverride ReadOnly Property Moves As IReadOnlyList(Of String)

    Public Function Accepts(move As String) As Boolean
        Return Moves.Contains(move)
    End Function

End Class

''' <summary>A menu: the explorer picks an option (moves "1", "2", ...).</summary>
Public NotInheritable Class Choice
    Inherits Prompt

    Public ReadOnly Property Options As String()
    Public Overrides ReadOnly Property Moves As IReadOnlyList(Of String)

    Public Overrides ReadOnly Property Kind As String
        Get
            Return "choice"
        End Get
    End Property

    Public Sub New(ParamArray options As String())
        Me.Options = options
        Moves = Enumerable.Range(1, options.Length).Select(Function(number) number.ToString()).ToArray()
    End Sub

End Class

''' <summary>A challenge: the explorer picks an answer (moves "a" to "d").</summary>
Public NotInheritable Class Challenge
    Inherits Prompt

    Public ReadOnly Property Challenger As String
    Public ReadOnly Property Question As Question
    Public ReadOnly Property Options As String()
    Public Overrides ReadOnly Property Moves As IReadOnlyList(Of String)

    Public Overrides ReadOnly Property Kind As String
        Get
            Return "question"
        End Get
    End Property

    Public Sub New(challenger As String, question As Question, options As String())
        Me.Challenger = challenger
        Me.Question = question
        Me.Options = options
        Moves = Game.Letters.Take(options.Length).ToArray()
    End Sub

End Class

''' <summary>Everything that defines a quest: replaying it always gives the same result.</summary>
Public NotInheritable Class QuestRequest

    Public Property Name As String
    Public Property Difficulty As String
    Public Property Seed As Long
    Public Property Moves As String()
    Public Property Carried As Integer
    Public Property OnlyPath As String
    Public Property SkipQuestions As Integer()
    Public Property Version As Integer
    Public Property Final As Boolean

    Public Shared Function From(json As JsonElement) As QuestRequest
        Return New QuestRequest With {
            .Name = json.GetProperty("name").GetString(),
            .Difficulty = json.GetProperty("difficulty").GetString(),
            .Seed = json.GetProperty("seed").GetInt64(),
            .Moves = json.GetProperty("moves").EnumerateArray().Select(Function(move) move.GetString()).ToArray(),
            .Carried = json.GetProperty("carried").GetInt32(),
            .OnlyPath = json.GetProperty("onlyPath").GetString(),
            .SkipQuestions = json.GetProperty("skipQuestions").EnumerateArray().Select(Function(number) number.GetInt32()).ToArray(),
            .Version = json.GetProperty("version").GetInt32(),
            .Final = json.GetProperty("final").GetBoolean()
        }
    End Function

End Class

''' <summary>One explorer's quest: their progress, the scene they're in, what happened since
''' their last move, and what the game is waiting for now.</summary>
Public NotInheritable Class Quest

    Public ReadOnly Property Rng As Random
    Public ReadOnly Property Request As QuestRequest

    Public ReadOnly Property Name As String
    Public ReadOnly Property Difficulty As String
    Public Property Lives As Integer
    Public Property Score As Integer
    Public ReadOnly Property Inventory As New List(Of String)
    Public Property Deck As New List(Of Integer)

    Public ReadOnly Property Carried As Integer
    Public ReadOnly Property OnlyPath As String
    Public ReadOnly Property SkipQuestions As HashSet(Of Integer)
    Public ReadOnly Property Version As Integer
    Public ReadOnly Property Final As Boolean

    Public ReadOnly Property Asked As New List(Of Integer)   ' question numbers asked, in order
    Public Property Path As String                           ' the path it went down, once chosen
    Public Property Dragon As String                         ' the bonus dragon: "won" or "lost" once answered
    Public Property Boss As String                           ' the final boss: "won" or "lost" once answered

    Public Property Scene As String = "start"
    Public ReadOnly Property Log As New List(Of (Kind As String, Text As String))
    Public Property Prompt As Prompt                         ' Nothing once the quest (or a battle) is over
    Public Property Result As String                         ' "win" or "lose" once the quest is over

    Public Property Move As String = ""                      ' the explorer's latest move, for the story to read
    Public Property Passed As Boolean                        ' how the latest challenge went

    Public Sub New(request As QuestRequest)
        Me.Request = request
        Rng = New Random(CInt(request.Seed And Integer.MaxValue))  ' the same seed, the same shuffles on every replay
        Name = request.Name
        Difficulty = request.Difficulty
        Lives = Rules.Levels(request.Difficulty).Lives
        Score = request.Carried
        Carried = request.Carried
        OnlyPath = request.OnlyPath
        SkipQuestions = New HashSet(Of Integer)(request.SkipQuestions)
        Version = request.Version
        Final = request.Final
    End Sub

    Public ReadOnly Property DragonAwaits As Dragon
        Get
            If Result = "win" AndAlso Prompt Is Nothing AndAlso Dragon Is Nothing AndAlso Boss Is Nothing Then
                Return Rules.Dragons.GetValueOrDefault((Difficulty, Path))
            End If
            Return Nothing
        End Get
    End Property

    Public ReadOnly Property BossAwaits As Boolean
        Get
            Return Final AndAlso Result = "win" AndAlso Prompt Is Nothing AndAlso Boss Is Nothing
        End Get
    End Property

    Public Sub Banner(scene As String)
        Me.Scene = scene
    End Sub

    Public Sub Narrate(text As String)
        Log.Add(("story", text))
    End Sub

    Public Sub Note(kind As String, text As String)
        Log.Add((kind, text))
    End Sub

End Class

Public Module Game

    Public ReadOnly Letters As String() = {"a", "b", "c", "d"}

    ''' <summary>Plays a quest from the start with the moves made so far, and returns it as it
    ''' stands now. Its log holds what happened after the last move. VB's iterators stand in for
    ''' the console game's input(): the story yields a prompt and carries on at the next move.
    ''' After a win, Rules.DragonMove wakes the bonus dragon and the next move answers its
    ''' riddle. A final quest (one that completes every path on every level) can then face the
    ''' boss: Rules.BossMove, then the answer.</summary>
    Public Function Replay(request As QuestRequest) As Quest
        Dim quest As New Quest(request)
        Dim adventure = Story.StartGame(quest).GetEnumerator()
        quest.Prompt = If(adventure.MoveNext(), adventure.Current, Nothing)
        For Each move In request.Moves
            Dim battle As IEnumerable(Of Prompt) = Nothing
            If move = Rules.DragonMove AndAlso quest.DragonAwaits IsNot Nothing Then
                battle = Story.DragonBattle(quest)
            ElseIf move = Rules.BossMove AndAlso quest.BossAwaits Then
                battle = Story.BossBattle(quest)
            End If
            If battle IsNot Nothing Then
                adventure.Dispose()
                adventure = battle.GetEnumerator()
                quest.Log.Clear()
                quest.Prompt = If(adventure.MoveNext(), adventure.Current, Nothing)
                Continue For
            End If
            If quest.Prompt Is Nothing OrElse Not quest.Prompt.Accepts(move) Then
                Exit For
            End If
            quest.Log.Clear()
            quest.Move = move
            quest.Prompt = If(adventure.MoveNext(), adventure.Current, Nothing)
        Next
        adventure.Dispose()
        Return quest
    End Function

    ''' <summary>A Fisher-Yates shuffle, written out so that saved quests replay the same however
    ''' the .NET libraries change. (A seeded Random's numbers are themselves promised not to.)</summary>
    Public Sub Shuffle(Of T)(rng As Random, items As IList(Of T))
        For i = items.Count - 1 To 1 Step -1
            Dim j = rng.Next(i + 1)
            Dim held = items(i)
            items(i) = items(j)
            items(j) = held
        Next
    End Sub

End Module

''' <summary>The program's JSON answers.</summary>
Public Module Answers

    Public Sub WriteInfo(json As Utf8JsonWriter)
        json.WriteStartObject()
        json.WriteNumber("gameVersion", Rules.GameVersion)
        json.WriteStartObject("questionCounts")
        For Each entry In Rules.QuestionCounts
            json.WriteNumber(entry.Key.ToString(), entry.Value)
        Next
        json.WriteEndObject()
        json.WriteStartArray("levels")
        For Each entry In Rules.Levels
            json.WriteStartObject()
            json.WriteString("key", entry.Key)
            json.WriteNumber("lives", entry.Value.Lives)
            json.WriteNumber("multiplier", entry.Value.Multiplier)
            json.WriteString("topics", entry.Value.Topics)
            json.WriteEndObject()
        Next
        json.WriteEndArray()
        json.WriteStartArray("paths")
        For Each path In Rules.Paths
            json.WriteStartObject()
            json.WriteString("key", path.Key)
            json.WriteString("label", path.Label)
            json.WriteString("name", path.Name)
            json.WriteEndObject()
        Next
        json.WriteEndArray()
        json.WriteStartObject("scenes")
        For Each entry In Rules.Scenes
            json.WriteStartArray(entry.Key)
            json.WriteStringValue(entry.Value.Banner)
            json.WriteStringValue(entry.Value.Picture)
            json.WriteStringValue(entry.Value.Description)
            json.WriteEndArray()
        Next
        json.WriteEndObject()
        json.WriteString("dragonMove", Rules.DragonMove)
        json.WriteNumber("dragonPoints", Rules.DragonPoints)
        json.WriteString("bossMove", Rules.BossMove)
        json.WriteNumber("bossPoints", Rules.BossPoints)
        json.WriteStartObject("texts")
        For Each entry In Rules.Texts
            json.WriteString(entry.Key, entry.Value)
        Next
        json.WriteStartArray("intro")
        For Each paragraph In Rules.Intro
            json.WriteStringValue(paragraph)
        Next
        json.WriteEndArray()
        json.WriteEndObject()
        json.WriteEndObject()
    End Sub

    Public Sub WriteQuest(json As Utf8JsonWriter, quest As Quest)
        json.WriteStartObject()
        json.WriteString("scene", quest.Scene)
        json.WriteString("result", quest.Result)
        json.WriteStartObject("player")
        json.WriteString("name", quest.Name)
        json.WriteString("difficulty", quest.Difficulty)
        json.WriteNumber("lives", quest.Lives)
        json.WriteNumber("score", quest.Score)
        json.WriteStartArray("inventory")
        For Each relic In quest.Inventory
            json.WriteStringValue(relic)
        Next
        json.WriteEndArray()
        json.WriteEndObject()
        json.WriteStartArray("log")
        For Each entry In quest.Log
            json.WriteStartArray()
            json.WriteStringValue(entry.Kind)
            json.WriteStringValue(entry.Text)
            json.WriteEndArray()
        Next
        json.WriteEndArray()
        json.WriteStartArray("asked")
        For Each number In quest.Asked
            json.WriteNumberValue(number)
        Next
        json.WriteEndArray()
        json.WriteString("path", quest.Path)
        json.WriteString("dragon", quest.Dragon)
        json.WriteString("boss", quest.Boss)
        Dim dragon = quest.DragonAwaits
        json.WriteString("dragonAwaits", If(dragon Is Nothing, Nothing, dragon.Scene))
        json.WriteBoolean("bossAwaits", quest.BossAwaits)
        json.WritePropertyName("prompt")
        WritePrompt(json, quest.Prompt)
        json.WriteEndObject()
    End Sub

    Private Sub WritePrompt(json As Utf8JsonWriter, prompt As Prompt)
        If prompt Is Nothing Then
            json.WriteNullValue()
            Return
        End If
        json.WriteStartObject()
        json.WriteString("kind", prompt.Kind)
        json.WriteStartArray("moves")
        For Each move In prompt.Moves
            json.WriteStringValue(move)
        Next
        json.WriteEndArray()
        json.WriteStartArray("options")
        Dim menu = TryCast(prompt, Choice)
        Dim asked = TryCast(prompt, Challenge)
        If menu IsNot Nothing Then
            For Each label In menu.Options
                json.WriteStringValue(label)
            Next
        ElseIf asked IsNot Nothing Then
            For i = 0 To asked.Options.Length - 1
                json.WriteStartArray()
                json.WriteStringValue(Game.Letters(i))
                json.WriteStringValue(asked.Options(i))
                json.WriteEndArray()
            Next
        End If
        json.WriteEndArray()
        If asked IsNot Nothing Then
            json.WriteString("challenger", asked.Challenger)
            json.WriteString("prompt", asked.Question.Prompt)
            json.WriteString("code", asked.Question.Code)
        End If
        json.WriteEndObject()
    End Sub

    Public Sub WriteQuestions(json As Utf8JsonWriter)
        json.WriteStartObject()
        json.WriteStartObject("levels")
        For Each entry In Questions.Levels
            json.WriteStartArray(entry.Key)
            For Each question In entry.Value
                WriteQuestion(json, question)
            Next
            json.WriteEndArray()
        Next
        json.WriteEndObject()
        json.WriteStartArray("dragons")
        For Each entry In Rules.Dragons
            json.WriteStartObject()
            json.WriteString("level", entry.Key.Level)
            json.WriteString("path", entry.Key.Path)
            json.WriteString("scene", entry.Value.Scene)
            json.WritePropertyName("question")
            WriteQuestion(json, entry.Value.Question)
            json.WriteEndObject()
        Next
        json.WriteEndArray()
        json.WriteStartArray("boss")
        For Each question In Questions.Boss
            WriteQuestion(json, question)
        Next
        json.WriteEndArray()
        json.WriteEndObject()
    End Sub

    Private Sub WriteQuestion(json As Utf8JsonWriter, question As Question)
        json.WriteStartObject()
        json.WriteString("prompt", question.Prompt)
        json.WriteString("code", question.Code)
        json.WriteStartArray("options")
        For Each label In question.Options
            json.WriteStringValue(label)
        Next
        json.WriteEndArray()
        json.WriteString("answer", question.Answer)
        json.WriteString("explain", question.Explain)
        json.WriteString("compileError", question.CompileError)
        json.WriteEndObject()
    End Sub

End Module
