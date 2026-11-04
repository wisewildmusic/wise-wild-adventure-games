''' <summary>A VB.NET challenge: its options, the correct one (which must match an option exactly) and
''' a short explanation. CompileError is the compiler's code when the answer is that the snippet
''' doesn't compile.
'''
''' VB has no top-level statements, so a snippet of plain statements stands for the inside of Sub Main,
''' and one that shows its own Sub Main (beside its functions and classes) stands for the inside of a
''' Module. Like the whole realm of Visualia, snippets run with Option Strict On unless they begin
''' otherwise. tools/check-vb-questions.py builds and runs every snippet that way, and checks each
''' answer against what really happens.</summary>
Public NotInheritable Class Question

    Public ReadOnly Property Prompt As String
    Public ReadOnly Property Code As String
    Public ReadOnly Property Options As String()
    Public ReadOnly Property Answer As String
    Public ReadOnly Property Explain As String
    Public ReadOnly Property CompileError As String

    Public Sub New(prompt As String, code As String, options As String(), answer As String, explain As String,
                   compileError As String)
        Me.Prompt = prompt
        Me.Code = code
        Me.Options = options
        Me.Answer = answer
        Me.Explain = explain
        Me.CompileError = compileError
    End Sub

End Class

Public Module Questions

    Private Const Prints As String = "What does this code print?"
    Private Const NoCompile As String = "Compile error"

    ' Each snippet is an XML literal holding a CDATA section, a very VB way to write text that runs over
    ' several lines and is full of quotes: nothing inside it needs escaping.
    Private Function Code(snippet As XElement, options As String(), answer As String, explain As String,
                          Optional compileError As String = Nothing) As Question
        Return New Question(Prints, Dedent(snippet.Value), options, answer, explain, compileError)
    End Function

    Private Function Ask(prompt As String, options As String(), answer As String, explain As String) As Question
        Return New Question(prompt, Nothing, options, answer, explain, Nothing)
    End Function

    ''' <summary>A snippet's text, without the indenting it has in this file.</summary>
    Private Function Dedent(text As String) As String
        Dim lines = text.Replace(vbCr, "").TrimEnd().Split(vbLf).SkipWhile(Function(line) line.Trim() = "").ToArray()
        Dim margin = lines.Where(Function(line) line.Trim() <> "").Min(Function(line) line.Length - line.TrimStart().Length)
        Return String.Join(vbLf, lines.Select(Function(line) If(line.Length < margin, "", line.Substring(margin))))
    End Function

    Public ReadOnly Levels As New Dictionary(Of String, Question()) From {
        {"easy", {
            Code(<c><![CDATA[
                Dim x As Integer = 5
                x = x + 2
                Console.WriteLine(x)
                ]]></c>, {"5", "7", "52", "x + 2"}, "7",
                "x starts at 5, then x + 2 (which is 7) is stored back into x."),
            Ask("Which of these is a valid VB.NET variable name?",
                {"2ndPlace", "my-score", "playerName", "Dim"}, "playerName",
                "Names can't start with a digit, can't contain '-', and can't be a keyword such as Dim."),
            Code(<c><![CDATA[
                Dim fruits() As String = {"apple", "banana", "cherry"}
                Console.WriteLine(fruits(1))
                ]]></c>, {"apple", "banana", "cherry", "IndexOutOfRangeException"}, "banana",
                "Array indexes start at 0, and VB uses round brackets for them, so fruits(1) is the second item."),
            Ask("What type does the literal 3.14 have in VB.NET?",
                {"Integer", "Single", "Double", "Decimal"}, "Double",
                "A number with a decimal point is a Double unless it ends in F (Single) or D (Decimal)."),
            Code(<c><![CDATA[
                Dim age As Integer = 12
                If age >= 13 Then
                    Console.WriteLine("Teen")
                Else
                    Console.WriteLine("Kid")
                End If
                ]]></c>, {"Teen", "Kid", "Teen Kid", "Nothing is printed"}, "Kid",
                "12 >= 13 is False, so the Else branch runs."),
            Code(<c><![CDATA[
                For i As Integer = 1 To 3
                    Console.Write(i & " ")
                Next
                ]]></c>, {"1 2 3", "0 1 2", "1 2", "0 1 2 3"}, "1 2 3",
                "For ... To includes both ends, so i takes the values 1, 2 and 3."),
            Code(<c><![CDATA[
                Function Greet(name As String) As String
                    Return "Hi " & name
                End Function

                Sub Main()
                    Console.WriteLine(Greet("Ada"))
                End Sub
                ]]></c>, {"Hi Ada", "Hi name", "Greet Ada", "Nothing is printed"}, "Hi Ada",
                "The argument ""Ada"" is passed into the name parameter, and & joins it onto ""Hi ""."),
            Ask("Which keyword declares a local variable in VB.NET?",
                {"Dim", "Var", "Let", "Local"}, "Dim",
                "Dim, short for dimension, declares a variable: Dim score As Integer."),
            Code(<c><![CDATA[
                Dim items As New List(Of Integer) From {1, 2, 3}
                items.Add(4)
                Console.WriteLine(items.Count)
                ]]></c>, {"3", "4", "5", "10"}, "4",
                "Add() puts one item on the end, so the list now holds 4 items."),
            Code(<c><![CDATA[
                Console.WriteLine("VB" & 1 & 2)
                ]]></c>, {"VB12", "VB3", "VB 1 2", NoCompile}, "VB12",
                "& always joins text, so each number is turned into a string and joined on in turn."),
            Code(<c><![CDATA[
                Console.WriteLine(7 > 3 AndAlso 2 > 5)
                ]]></c>, {"True", "False", "7", NoCompile}, "False",
                "AndAlso is only True when both sides are True, and 2 > 5 is False."),
            Ask("Which symbol starts a comment in VB.NET?",
                {"'", "//", "#", "--"}, "'",
                "Everything after ' on a line is ignored by the compiler. (REM works too, but hardly anyone uses it now.)"),
            Code(<c><![CDATA[
                Console.WriteLine(10 \ 3)
                ]]></c>, {"3", "3.33", "3.3333333333333335", "4"}, "3",
                "VB has two divisions. \ gives a whole number and drops the remainder, while / always gives a Double."),
            Code(<c><![CDATA[
                Console.WriteLine(17 Mod 5)
                ]]></c>, {"3", "2", "3.4", "12"}, "2",
                "Mod gives the remainder of a division: 17 is 3 fives (15) with 2 left over."),
            Code(<c><![CDATA[
                Dim name As String = "Castle"
                Console.WriteLine(name.Length)
                ]]></c>, {"5", "6", "7", "Castle"}, "6",
                "Length counts the characters in a string: C-a-s-t-l-e is 6."),
            Code(<c><![CDATA[
                Dim colors(2) As String
                Console.WriteLine(colors.Length)
                ]]></c>, {"2", "3", "0", NoCompile}, "3",
                "The number in a VB array declaration is the last index, not the size: colors(2) has indexes 0, 1 and 2."),
            Code(<c><![CDATA[
                Dim x As Integer = 3
                If x > 5 Then
                    Console.WriteLine("big")
                ElseIf x > 2 Then
                    Console.WriteLine("medium")
                Else
                    Console.WriteLine("small")
                End If
                ]]></c>, {"big", "medium", "small", "medium small"}, "medium",
                "x > 5 is False, so VB checks the ElseIf: 3 > 2 is True, and the last Else is skipped."),
            Code(<c><![CDATA[
                Dim total As Integer = 0
                For Each n As Integer In {2, 4, 6}
                    total += n
                Next
                Console.WriteLine(total)
                ]]></c>, {"6", "12", "246", "0"}, "12",
                "The loop adds each number to total in turn: 2 + 4 + 6 = 12."),
            Code(<c><![CDATA[
                Dim Score As Integer = 10
                score = SCORE + 1
                Console.WriteLine(sCoRe)
                ]]></c>, {"11", "10", "1", NoCompile}, "11",
                "VB doesn't care about capitals: Score, score, SCORE and sCoRe are all the same variable."),
            Code(<c><![CDATA[
                Dim count As Integer = "5"
                Console.WriteLine(count)
                ]]></c>, {"5", "0", """5""", NoCompile}, NoCompile,
                "With Option Strict On, a String can't quietly become an Integer. CInt(""5"") would convert it.",
                "BC30512")
        }},
        {"medium", {
            Code(<c><![CDATA[
                Dim total As Integer = 0
                For n As Integer = 1 To 4
                    total += n
                Next
                Console.WriteLine(total)
                ]]></c>, {"10", "15", "4", "9"}, "10",
                "n takes the values 1, 2, 3 and 4, and their sum is 10."),
            Code(<c><![CDATA[
                Dim word As String = "visual"
                Console.WriteLine(word.Substring(1, 3))
                ]]></c>, {"vis", "isu", "isua", "sual"}, "isu",
                "Substring(1, 3) starts at index 1 and takes 3 characters. The second number is a length, not an end."),
            Code(<c><![CDATA[
                Dim word As String = "basic"
                Console.WriteLine(Mid(word, 2, 3) & " " & word.Substring(2, 3))
                ]]></c>, {"asi sic", "asi asi", "sic sic", "bas sic"}, "asi sic",
                "VB's own Mid() counts from 1, but .NET's Substring() counts from 0, so the same numbers pick different letters."),
            Code(<c><![CDATA[
                Dim scores As New Dictionary(Of String, Integer) From {{"ana", 90}, {"ben", 75}}
                Console.WriteLine(scores.GetValueOrDefault("cal", 0))
                ]]></c>, {"0", "Nothing", "cal", "KeyNotFoundException"}, "0",
                "GetValueOrDefault() returns the default you give it when the key is missing. scores(""cal"") would throw."),
            Code(<c><![CDATA[
                Dim n As Integer = 15
                Select Case n
                    Case 1 To 9
                        Console.WriteLine("small")
                    Case 10, 20, 30
                        Console.WriteLine("round")
                    Case Is > 10
                        Console.WriteLine("big")
                    Case Else
                        Console.WriteLine("other")
                End Select
                ]]></c>, {"small", "round", "big", "other"}, "big",
                "Select Case takes the first Case that fits: 15 isn't in 1 To 9 or the list, but Is > 10 matches. Only one ever runs."),
            Code(<c><![CDATA[
                Dim count As Integer = 0
                Do While count < 10
                    count += 3
                Loop
                Console.WriteLine(count)
                ]]></c>, {"9", "10", "12", "3"}, "12",
                "count goes 3, 6, 9, 12. The condition is only checked before each pass, so it stops once count is 12."),
            Code(<c><![CDATA[
                Function Power(number As Integer, Optional exponent As Integer = 2) As Integer
                    Return CInt(number ^ exponent)
                End Function

                Sub Main()
                    Console.WriteLine(Power(3))
                End Sub
                ]]></c>, {"6", "9", "27", NoCompile}, "9",
                "exponent is Optional and uses its default of 2. ^ raises to a power and gives a Double, which CInt turns back."),
            Code(<c><![CDATA[
                Dim half As Integer = 7 / 2
                Console.WriteLine(half)
                ]]></c>, {"3", "3.5", "4", NoCompile}, NoCompile,
                "/ always gives a Double, and Option Strict On won't squeeze a Double into an Integer. 7 \ 2 would give 3.",
                "BC30512"),
            Code(<c><![CDATA[
                Dim name As String = "Ada"
                Dim level As Integer = 3
                Console.WriteLine($"{name} is level {level + 1}")
                ]]></c>, {"Ada is level 4", "Ada is level 3 + 1", "{name} is level {level + 1}", "Ada is level 31"},
                "Ada is level 4",
                "An interpolated string ($""..."") evaluates the expressions inside {} and inserts the results."),
            Code(<c><![CDATA[
                For i As Integer = 0 To 4
                    If i = 3 Then Exit For
                    Console.Write(i & " ")
                Next
                ]]></c>, {"0 1 2", "0 1 2 3", "0 1 2 4", "3"}, "0 1 2",
                "Exit For leaves the loop as soon as i is 3, before 3 is printed."),
            Code(<c><![CDATA[
                Sub Change(ByVal value As Integer)
                    value = 5
                End Sub

                Sub Main()
                    Dim x As Integer = 10
                    Change(x)
                    Console.WriteLine(x)
                End Sub
                ]]></c>, {"5", "10", "0", NoCompile}, "10",
                "ByVal passes a copy: Change() gets its own value, and x is untouched."),
            Code(<c><![CDATA[
                Sub Add(ByRef value As Integer)
                    value += 1
                End Sub

                Sub Main()
                    Dim n As Integer = 1
                    Add(n)
                    Add(n)
                    Console.WriteLine(n)
                End Sub
                ]]></c>, {"1", "2", "3", NoCompile}, "3",
                "ByRef passes the variable itself, not a copy, so both calls change n. The caller doesn't have to say so."),
            Code(<c><![CDATA[
                Console.WriteLine("hello world".Split(" "c).Length)
                ]]></c>, {"2", "11", "10", "1"}, "2",
                "The c makes "" "" a Char, and Split() breaks the string at it into an array of two strings."),
            Code(<c><![CDATA[
                Dim castle As New Dictionary(Of String, Integer) From {{"towers", 4}, {"gates", 1}}
                Dim total As Integer = 0
                For Each pair In castle
                    total += pair.Value
                Next
                Console.WriteLine(total)
                ]]></c>, {"5", "2", "41", NoCompile}, "5",
                "Looping over a Dictionary gives KeyValuePair items, each with a Key and a Value: 4 + 1 = 5."),
            Code(<c><![CDATA[
                Dim s As String = "abc"
                s.ToUpper()
                Console.WriteLine(s)
                ]]></c>, {"abc", "ABC", "Abc", NoCompile}, "abc",
                "Strings can't be changed. ToUpper() returns a new string, and this code throws it away."),
            Code(<c><![CDATA[
                Function Greet(name As String, Optional greeting As String = "Hello") As String
                    Return $"{greeting}, {name}!"
                End Function

                Sub Main()
                    Console.WriteLine(Greet("Ada", greeting:="Hail"))
                End Sub
                ]]></c>, {"Hail, Ada!", "Hello, Ada!", "Hello, Hail!", NoCompile}, "Hail, Ada!",
                "A named argument (greeting:=...) replaces the Optional parameter's default for that call."),
            Code(<c><![CDATA[
                For i As Integer = 0 To 2
                Next
                Console.WriteLine(i)
                ]]></c>, {"3", "2", "0", NoCompile}, NoCompile,
                "A variable declared in a For statement only exists inside that loop, so i is out of scope here.",
                "BC30451"),
            Code(<c><![CDATA[
                For i As Integer = 0 To 4
                    If i Mod 2 = 0 Then Continue For
                    Console.Write(i & " ")
                Next
                ]]></c>, {"1 3", "0 2 4", "0 1 2 3 4", "1 3 5"}, "1 3",
                "Continue For skips the rest of the loop body for that pass, so the even numbers are never printed."),
            Code(<c><![CDATA[
                For i As Integer = 10 To 1 Step -3
                    Console.Write(i & " ")
                Next
                ]]></c>, {"10 7 4 1", "10 7 4", "1 4 7 10", "10 7 4 1 -2"}, "10 7 4 1",
                "Step -3 counts down by 3 each pass, and 1 is still in range, so the loop runs for 10, 7, 4 and 1."),
            Code(<c><![CDATA[
                Function Loud() As Boolean
                    Console.Write("loud ")
                    Return True
                End Function

                Sub Main()
                    Dim a As Boolean = False And Loud()
                    Dim b As Boolean = False AndAlso Loud()
                    Console.WriteLine(a Or b)
                End Sub
                ]]></c>, {"loud False", "loud loud False", "False", "loud True"}, "loud False",
                "And always runs both sides. AndAlso stops once the left side is False, so Loud() only runs once.")
        }},
        {"hard", {
            Code(<c><![CDATA[
                Dim squares = From x In Enumerable.Range(0, 6)
                              Where x Mod 2 = 0
                              Select x * x
                Console.WriteLine(String.Join(",", squares))
                ]]></c>, {"0,4,16", "4,16", "1,9,25", "0,2,4"}, "0,4,16",
                "VB has LINQ queries built in. Where keeps the even numbers 0, 2 and 4, then Select squares them."),
            Code(<c><![CDATA[
                Dim list As New List(Of Integer) From {1, 2}
                Dim query = list.Select(Function(x) x * 10)
                list.Add(3)
                Console.WriteLine(query.Count())
                ]]></c>, {"2", "3", "0", NoCompile}, "3",
                "LINQ queries are lazy: Select() runs only when the results are asked for, by then over 3 items."),
            Code(<c><![CDATA[
                Structure Point
                    Public X As Integer
                End Structure

                Sub Main()
                    Dim a As New Point With {.X = 1}
                    Dim b = a
                    b.X = 2
                    Console.WriteLine(a.X)
                End Sub
                ]]></c>, {"1", "2", "0", NoCompile}, "1",
                "A Structure is a value type: b = a copies it, so changing b leaves a alone."),
            Code(<c><![CDATA[
                Class Point
                    Public X As Integer
                End Class

                Sub Main()
                    Dim a As New Point With {.X = 1}
                    Dim b = a
                    b.X = 2
                    Console.WriteLine(a.X)
                End Sub
                ]]></c>, {"1", "2", "0", NoCompile}, "2",
                "A Class is a reference type: a and b refer to the same object, so a change through b shows in a."),
            Code(<c><![CDATA[
                Dim makeMultiplier = Function(n As Integer) Function(x As Integer) x * n
                Dim triple = makeMultiplier(3)
                Console.WriteLine(triple(7))
                ]]></c>, {"21", "10", "7", NoCompile}, "21",
                "The inner lambda remembers n = 3 from the call that made it (a closure), so triple(7) is 7 * 3."),
            Code(<c><![CDATA[
                Function Average(ParamArray values() As Integer) As Double
                    Return values.Sum() / values.Length
                End Function

                Sub Main()
                    Console.WriteLine(Average(2, 4, 9))
                End Sub
                ]]></c>, {"5", "5.0", "15", NoCompile}, "5",
                "ParamArray collects the arguments into an array, and / gives a Double. A whole Double prints with no decimal point."),
            Code(<c><![CDATA[
                Dim words() As String = {"pear", "fig", "kiwi", "apple"}
                Dim sorted = From w In words Order By w.Length, w Select w
                Console.WriteLine(String.Join(" ", sorted))
                ]]></c>, {"fig kiwi pear apple", "fig pear kiwi apple", "apple fig kiwi pear", "apple kiwi pear fig"},
                "fig kiwi pear apple",
                "Order By sorts by length first, then alphabetically to break ties, so kiwi comes before pear."),
            Code(<c><![CDATA[
                Function Mystery(n As Integer) As Integer
                    Return If(n <= 1, 1, n * Mystery(n - 1))
                End Function

                Sub Main()
                    Console.WriteLine(Mystery(5))
                End Sub
                ]]></c>, {"120", "15", "24", "StackOverflowException"}, "120",
                "Mystery() is a recursive factorial: 5 * 4 * 3 * 2 * 1 = 120."),
            Code(<c><![CDATA[
                Function Loud(word As String) As String
                    Console.Write(word & " ")
                    Return word
                End Function

                Sub Main()
                    Console.WriteLine(CStr(IIf(True, Loud("a"), Loud("b"))))
                End Sub
                ]]></c>, {"a b a", "a a", "a", "b a"}, "a b a",
                "IIf is an ordinary function, so both arguments run before it picks one. The If() operator runs only the one it needs."),
            Code(<c><![CDATA[
                Dim names() As String = {"Ana", "Ben", "Cy"}
                Dim ages() As Integer = {30, 25}
                Dim pairs = names.Zip(ages, Function(name, age) $"{name}={age}")
                Console.WriteLine(String.Join(" ", pairs))
                ]]></c>, {"Ana=30 Ben=25", "Ana=30 Ben=25 Cy=0", "Ana=30 Ben=25 Cy=", "IndexOutOfRangeException"},
                "Ana=30 Ben=25",
                "Zip() stops at the end of the shorter sequence, so Cy is left out."),
            Code(<c><![CDATA[
                Function Tick() As Integer
                    Static count As Integer = 0
                    count += 1
                    Return count
                End Function

                Sub Main()
                    Tick()
                    Tick()
                    Console.WriteLine(Tick())
                End Sub
                ]]></c>, {"1", "3", "0", NoCompile}, "3",
                "Static keeps a local variable alive between calls, and its initializer only runs the first time."),
            Code(<c><![CDATA[
                Function Check(n As Integer) As String
                    Try
                        Return (10 \ n).ToString()
                    Catch ex As DivideByZeroException
                        Return "oops"
                    Finally
                        Console.Write("done ")
                    End Try
                End Function

                Sub Main()
                    Console.WriteLine(Check(0))
                End Sub
                ]]></c>, {"done oops", "oops done", "oops", "DivideByZeroException"}, "done oops",
                "The Finally block runs before the function hands back its return value, so ""done"" prints first."),
            Code(<c><![CDATA[
                Dim actions As New List(Of Func(Of Integer))
                For i As Integer = 0 To 2
                    actions.Add(Function() i)
                Next
                Console.WriteLine(String.Join(",", actions.Select(Function(a) a())))
                ]]></c>, {"0,1,2", "3,3,3", "2,2,2", NoCompile}, "3,3,3",
                "A For loop has one i, shared by all three lambdas (the compiler warns you). By the time they run, it's 3."),
            Code(<c><![CDATA[
                Iterator Function Numbers() As IEnumerable(Of Integer)
                    Console.Write("start ")
                    Yield 1
                    Yield 2
                End Function

                Sub Main()
                    Dim seq = Numbers()
                    Console.Write("first ")
                    Console.WriteLine(seq.First())
                End Sub
                ]]></c>, {"first start 1", "start first 1", "first 1", "start 1 2 first 1"}, "first start 1",
                "Calling an Iterator function runs none of its code. It starts only when something asks for the first item."),
            Code(<c><![CDATA[
                Console.WriteLine(CInt(2.5) & " " & CInt(3.5))
                ]]></c>, {"2 4", "3 4", "2 3", "3 3"}, "2 4",
                "CInt rounds a .5 to the nearest even number (banker's rounding), so 2.5 goes down and 3.5 goes up."),
            Code(<c><![CDATA[
                Dim n As Integer = Nothing
                Dim s As String = Nothing
                Console.WriteLine($"{n} {s Is Nothing} {s = ""}")
                ]]></c>, {"0 True True", "Nothing True True", "0 True False", "0 False True"}, "0 True True",
                "Nothing means a type's default: 0 for an Integer, no string at all for a String. Yet = treats Nothing and """" as equal."),
            Code(<c><![CDATA[
                Class Vault
                    Public Shared Total As Integer
                    Public Mine As Integer

                    Public Sub Add()
                        Total += 1
                        Mine += 1
                    End Sub
                End Class

                Sub Main()
                    Dim a As New Vault()
                    Dim b As New Vault()
                    a.Add()
                    b.Add()
                    Console.WriteLine($"{Vault.Total} {a.Mine}")
                End Sub
                ]]></c>, {"2 1", "1 1", "2 2", "1 2"}, "2 1",
                "A Shared field belongs to the class, so all objects share Total. Each object has its own Mine."),
            Code(<c><![CDATA[
                Class Animal
                    Public Overridable Function Speak() As String
                        Return "..."
                    End Function

                    Public Function Name() As String
                        Return "animal"
                    End Function
                End Class

                Class Dog
                    Inherits Animal

                    Public Overrides Function Speak() As String
                        Return "Woof"
                    End Function

                    Public Shadows Function Name() As String
                        Return "dog"
                    End Function
                End Class

                Sub Main()
                    Dim pet As Animal = New Dog()
                    Console.WriteLine(pet.Speak() & " " & pet.Name())
                End Sub
                ]]></c>, {"Woof animal", "Woof dog", "... animal", "... dog"}, "Woof animal",
                "Overrides replaces the method for every caller. Shadows only hides it, so a caller using an Animal gets Animal's."),
            Code(<c><![CDATA[
                Dim nums() As Integer = {1, 2, 3, 4}
                Dim total = Aggregate n In nums Into Sum(n)
                Console.WriteLine(total)
                ]]></c>, {"10", "24", "4", "1"}, "10",
                "VB's queries have their own Aggregate keyword: Aggregate ... Into Sum(n) adds the values up into one number."),
            Code(<c><![CDATA[
                Dim big As Integer = Integer.MaxValue
                big += 1
                Console.WriteLine(big)
                ]]></c>, {"2147483648", "-2147483648", "0", "OverflowException"}, "OverflowException",
                "VB checks whole-number arithmetic by default, so going past Integer.MaxValue throws instead of wrapping around.")
        }}
    }

    ' One bonus riddle for each dragon, a step harder than its level's own questions.
    Public ReadOnly Dragons As New Dictionary(Of (Level As String, Path As String), Question) From {
        {("easy", "cave"), Code(<c><![CDATA[
            Dim a As Integer = 7
            Console.WriteLine(a \ 2 & " " & a / 2)
            ]]></c>, {"3 3.5", "3.5 3.5", "3 3", "4 3.5"}, "3 3.5",
            "\ divides into whole numbers and drops the remainder, while / always gives a Double. Both come before &.")},
        {("medium", "cave"), Code(<c><![CDATA[
            Console.WriteLine($"{CInt(True)} {Convert.ToInt32(True)}")
            ]]></c>, {"-1 1", "1 1", "-1 -1", "1 -1"}, "-1 1",
            "VB's CInt makes True -1, all its bits set, as old Basic always did. .NET's Convert makes it 1.")},
        {("hard", "cave"), Code(<c><![CDATA[
            Iterator Function Flatten(items() As Object) As IEnumerable(Of Integer)
                For Each item In items
                    Dim inner = TryCast(item, Object())
                    If inner IsNot Nothing Then
                        For Each n In Flatten(inner)
                            Yield n
                        Next
                    Else
                        Yield CInt(item)
                    End If
                Next
            End Function

            Sub Main()
                Dim data() As Object = {1, New Object() {2, New Object() {3, 4}}, 5}
                Console.WriteLine(String.Join(",", Flatten(data)))
            End Sub
            ]]></c>, {"1,2,3,4,5", "1,2,5", "1,System.Object[],5", "InvalidCastException"}, "1,2,3,4,5",
            "Each inner array is flattened by a recursive call, however deep it goes, and its items are yielded in order.")},
        {("easy", "forest"), Code(<c><![CDATA[
            Dim trees As New List(Of String) From {"oak", "elm", "ash"}
            trees.Insert(1, "fir")
            trees.RemoveAt(0)
            Console.WriteLine(trees(1))
            ]]></c>, {"elm", "fir", "ash", "oak"}, "elm",
            "After Insert(): oak, fir, elm, ash. After RemoveAt(0): fir, elm, ash. So index 1 is elm.")},
        {("medium", "forest"), Code(<c><![CDATA[
            Dim trees(1) As String
            trees(0) = "oak"
            trees(1) = "elm"
            ReDim Preserve trees(2)
            trees(2) = "ash"
            Console.WriteLine(trees.Length & " " & trees(0))
            ]]></c>, {"3 oak", "4 oak", "3 ash", "2 oak"}, "3 oak",
            "ReDim Preserve makes a bigger array and copies the old items in. Its number is the last index, so it holds 3.")},
        {("hard", "forest"), Code(<c><![CDATA[
            Dim actions As New List(Of Func(Of Integer))
            For i As Integer = 1 To 3
                Dim copy As Integer = i
                actions.Add(Function() copy * 10)
            Next
            Console.WriteLine(String.Join(",", actions.Select(Function(a) a())))
            ]]></c>, {"10,20,30", "40,40,40", "30,30,30", "0,10,20"}, "10,20,30",
            "copy is a new variable on each pass, so each lambda captures its own. Without it they'd share i.")},
        {("easy", "castle"), Code(<c><![CDATA[
            Console.WriteLine(2 + 3 * 2 ^ 2)
            ]]></c>, {"14", "100", "20", "64"}, "14",
            "^ comes first, then *, then +: 2 ^ 2 is 4, 3 * 4 is 12, and 2 + 12 is 14.")},
        {("medium", "castle"), Code(<c><![CDATA[
            Dim value As Integer
            Dim ok As Boolean = Integer.TryParse("12x", value)
            Console.WriteLine($"{ok} {value}")
            ]]></c>, {"False 0", "True 12", "False 12", "FormatException"}, "False 0",
            "TryParse() never throws on bad input: it returns False and sets value, passed ByRef, to 0.")},
        {("hard", "castle"), Code(<c><![CDATA[
            Dim castle = <castle name="Classic">
                             <tower>North</tower>
                             <tower>South</tower>
                         </castle>
            Console.WriteLine($"{castle.@name} {castle.<tower>.Count()} {castle.<tower>(1).Value}")
            ]]></c>, {"Classic 2 South", "Classic 2 North", "name 2 South", NoCompile}, "Classic 2 South",
            "XML is built into VB: .@name reads an attribute, .<tower> finds child elements, and (1) picks the second.")}
    }

    ' The final boss's nine: the hardest questions in the game, and the most VB of all.
    Public ReadOnly Boss As Question() = {
        Code(<c><![CDATA[
            Dim a As Integer? = Nothing
            Dim b As Integer? = 5
            If a = b Then
                Console.Write("same ")
            ElseIf Not (a = b) Then
                Console.Write("different ")
            Else
                Console.Write("neither ")
            End If
            Console.WriteLine(a + b Is Nothing)
            ]]></c>, {"neither True", "different True", "same True", "different False"}, "neither True",
            "Comparing with a Nothing Integer? gives Nothing, which If doesn't count as True. Not Nothing is still Nothing, so only Else runs."),
        Code(<c><![CDATA[
            Dim a As String = Nothing
            Dim b As String = ""
            Console.WriteLine($"[{If(a, "left")}] [{If(b, "right")}] {a = b} {a Is b}")
            ]]></c>, {"[left] [] True False", "[left] [right] True False", "[left] [] False False", "[left] [right] True True"},
            "[left] [] True False",
            "If(x, y) only replaces Nothing, not an empty string. = treats Nothing and """" as equal, but Is asks if they're the same object."),
        Code(<c><![CDATA[
            Class Parent
                Public Overridable Function Who() As String
                    Return "parent"
                End Function

                Public Function Report() As String
                    Return Me.Who() & " " & MyClass.Who()
                End Function
            End Class

            Class Child
                Inherits Parent

                Public Overrides Function Who() As String
                    Return "child"
                End Function
            End Class

            Sub Main()
                Console.WriteLine(New Child().Report())
            End Sub
            ]]></c>, {"child parent", "child child", "parent parent", "parent child"}, "child parent",
            "Me.Who() reaches the override on the real object. MyClass is VB's own: it calls this class's version, as if it weren't Overridable."),
        Code(<c><![CDATA[
            Dim a = New With {Key .Name = "ruby", .Value = 5}
            Dim b = New With {Key .Name = "ruby", .Value = 9}
            b.Value = 7
            Console.WriteLine($"{a.Equals(b)} {b.Value}")
            ]]></c>, {"True 7", "False 7", "True 9", NoCompile}, "True 7",
            "A VB anonymous type's properties can be changed unless marked Key, and only Key properties count in Equals(): the Names match."),
        Code(<c><![CDATA[
            Function Loud(word As String) As Boolean
                Console.Write(word & " ")
                Return True
            End Function

            Sub Inner()
                Try
                    Throw New Exception()
                Finally
                    Console.Write("finally ")
                End Try
            End Sub

            Sub Main()
                Try
                    Inner()
                Catch ex As Exception When Loud("filter")
                    Console.WriteLine("catch")
                End Try
            End Sub
            ]]></c>, {"filter finally catch", "finally filter catch", "filter catch finally", "finally catch"},
            "filter finally catch",
            "An exception takes two passes. The first looks for a handler, running When filters. Only then does it unwind, running Finally blocks."),
        Code(<c><![CDATA[
            Function Total() As Integer
                Total = 5
                Try
                    Return Total + 1
                Finally
                    Total = 100
                End Try
            End Function

            Sub Main()
                Console.WriteLine(Total())
            End Sub
            ]]></c>, {"6", "100", "5", NoCompile}, "100",
            "A VB function's name is a variable holding its return value. Return stores into it, and Finally then changes it before it's handed back."),
        Code(<c><![CDATA[
            Interface IOpen
                Function Open() As String
            End Interface

            Class Door
                Implements IOpen

                Public Function Open() As String
                    Return "public"
                End Function

                Private Function Unlock() As String Implements IOpen.Open
                    Return "secret"
                End Function
            End Class

            Sub Main()
                Dim door As New Door()
                Dim asOpen As IOpen = door
                Console.WriteLine($"{door.Open()} {asOpen.Open()}")
            End Sub
            ]]></c>, {"public secret", "public public", "secret secret", NoCompile}, "public secret",
            "A VB method says for itself which interface member it implements, whatever its name, even if Private. Through IOpen, Open() reaches Unlock()."),
        Code(<c><![CDATA[
            Option Strict Off

            Sub Main()
                Dim a = "5" + 3
                Dim b = "5" & 3
                Console.WriteLine(a + 1 & " " & b)
            End Sub
            ]]></c>, {"9 53", "531 53", "8 53", NoCompile}, "9 53",
            "With Option Strict Off, + sees a String and a number and does arithmetic, so ""5"" + 3 is 8. & always joins text. Hence the law of Visualia."),
        Code(<c><![CDATA[
            Function Risky() As Integer
                On Error Resume Next
                Dim zero As Integer = 0
                Dim result As Integer = 1
                result = 10 \ zero
                Console.Write("alive ")
                Return result
            End Function

            Sub Main()
                Console.WriteLine(Risky())
            End Sub
            ]]></c>, {"alive 1", "alive 0", "1", "DivideByZeroException"}, "alive 1",
            "On Error Resume Next ignores the failed line and goes on to the next. The assignment never finished, so result is still 1.")
    }

End Module
