' The Lost Runtime of Visualia: a text adventure with VB.NET challenges, written in VB.NET.
'
' The website (site/compiled_game.py) starts this program whenever it needs the game. It sends one
' JSON request on standard input and reads one JSON answer from standard output:
'
'     {"command": "info"}        the game's settings, paths, scenes and wording
'     {"command": "replay", ...} a quest played through to where it stands (Game.Replay)
'     {"command": "questions"}   every question, so their answers can be checked by running them
'
' The program keeps nothing between runs. A quest is its random seed plus the moves made so
' far, and every replay plays it again from the start, which always ends in the same place.

Imports System.Text.Json

Module Program

    Function Main() As Integer
        Using input = Console.OpenStandardInput(),
              request = JsonDocument.Parse(input),
              output = Console.OpenStandardOutput(),
              writer = New Utf8JsonWriter(output)
            Dim root = request.RootElement
            Select Case root.GetProperty("command").GetString()
                Case "info"
                    Answers.WriteInfo(writer)
                Case "replay"
                    Answers.WriteQuest(writer, Game.Replay(QuestRequest.From(root)))
                Case "questions"
                    Answers.WriteQuestions(writer)
                Case Else
                    Console.Error.WriteLine("Unknown command")
                    Return 2
            End Select
        End Using
        Return 0
    End Function

End Module
