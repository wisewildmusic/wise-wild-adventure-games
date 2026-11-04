namespace Sharpia;

/// <summary>A C# challenge: its options, the correct one (which must match an option exactly) and
/// a short explanation. CompileError is the compiler's code when the answer is that the snippet
/// doesn't compile: tools/check-csharp-questions.py compiles and runs every snippet, as a modern
/// C# program (top-level statements, implicit usings), and checks each answer against what
/// really happens.</summary>
public sealed record Question(string Prompt, string? Code, string[] Options, string Answer, string Explain,
                              string? CompileError = null);

public static class Questions
{
    const string Prints = "What does this code print?";
    const string NoCompile = "Compile error";

    static Question Code(string code, string[] options, string answer, string explain, string? compileError = null) =>
        new(Prints, code.ReplaceLineEndings("\n"), options, answer, explain, compileError);

    static Question Ask(string prompt, string[] options, string answer, string explain) =>
        new(prompt, null, options, answer, explain);

    public static readonly Dictionary<string, Question[]> Levels = new()
    {
        ["easy"] =
        [
            Code("""
                int x = 5;
                x = x + 2;
                Console.WriteLine(x);
                """, ["5", "7", "52", "x + 2"], "7",
                "x starts at 5, then x + 2 (which is 7) is stored back into x."),
            Ask("Which of these is a valid C# variable name?",
                ["2ndPlace", "my-score", "playerName", "class"], "playerName",
                "Names can't start with a digit, can't contain '-', and can't be a keyword such as 'class'."),
            Code("""
                string[] fruits = { "apple", "banana", "cherry" };
                Console.WriteLine(fruits[1]);
                """, ["apple", "banana", "cherry", "IndexOutOfRangeException"], "banana",
                "Array indexes start at 0, so index 1 is the second item."),
            Ask("What type does the literal 3.14 have in C#?",
                ["int", "float", "double", "decimal"], "double",
                "A number with a decimal point is a double unless it ends in f (float) or m (decimal)."),
            Code("""
                int age = 12;
                if (age >= 13)
                    Console.WriteLine("Teen");
                else
                    Console.WriteLine("Kid");
                """, ["Teen", "Kid", "Teen Kid", "Nothing"], "Kid",
                "12 >= 13 is false, so the else branch runs."),
            Code("""
                for (int i = 0; i < 3; i++)
                    Console.Write(i + " ");
                """, ["0 1 2", "1 2 3", "0 1 2 3", "1 2"], "0 1 2",
                "i starts at 0 and the loop stops as soon as i < 3 is false."),
            Code("""
                string Greet(string name)
                {
                    return "Hi " + name;
                }

                Console.WriteLine(Greet("Ada"));
                """, ["Hi Ada", "Hi name", "Greet Ada", "Nothing"], "Hi Ada",
                "The argument \"Ada\" is passed into the name parameter and joined onto \"Hi \"."),
            Ask("Which keyword declares a local variable whose type the compiler works out for you?",
                ["var", "let", "auto", "dim"], "var",
                "var x = 5; is still strongly typed: the compiler makes x an int, and it stays one."),
            Code("""
                var items = new List<int> { 1, 2, 3 };
                items.Add(4);
                Console.WriteLine(items.Count);
                """, ["3", "4", "5", "10"], "4",
                "Add() puts one item on the end, so the list now holds 4 items."),
            Code("""
                Console.WriteLine("C#" + 1 + 2);
                """, ["C#12", "C#3", "C# 1 2", NoCompile], "C#12",
                "+ works left to right: \"C#\" + 1 makes the string \"C#1\", then + 2 makes \"C#12\"."),
            Code("""
                Console.WriteLine(7 > 3 && 2 > 5);
                """, ["True", "False", "7", NoCompile], "False",
                "&& is only true when both sides are true, and 2 > 5 is false."),
            Ask("Which symbol starts a single-line comment in C#?",
                ["#", "//", "--", "<!--"], "//",
                "Everything after // on a line is ignored by the compiler."),
            Code("""
                Console.WriteLine(10 / 3);
                """, ["3", "3.33", "3.3333333333333335", "4"], "3",
                "Dividing one int by another gives an int: the remainder is dropped."),
            Code("""
                Console.WriteLine(17 % 5);
                """, ["3", "2", "3.4", "12"], "2",
                "% gives the remainder of a division: 17 is 3 fives (15) with 2 left over."),
            Code("""
                string name = "Castle";
                Console.WriteLine(name.Length);
                """, ["5", "6", "7", "Castle"], "6",
                "Length counts the characters in a string: C-a-s-t-l-e is 6."),
            Code("""
                string[] colors = { "red", "green", "blue" };
                Console.WriteLine(colors[^1]);
                """, ["red", "green", "blue", NoCompile], "blue",
                "The ^ operator counts from the end, so ^1 is the last item."),
            Code("""
                int x = 3;
                if (x > 5)
                    Console.WriteLine("big");
                else if (x > 2)
                    Console.WriteLine("medium");
                else
                    Console.WriteLine("small");
                """, ["big", "medium", "small", "medium small"], "medium",
                "x > 5 is false, so C# checks the else if: 3 > 2 is true, and the last else is skipped."),
            Code("""
                int total = 0;
                foreach (int n in new[] { 2, 4, 6 })
                    total += n;
                Console.WriteLine(total);
                """, ["6", "12", "246", "0"], "12",
                "The loop adds each number to total in turn: 2 + 4 + 6 = 12."),
            Code("""
                Console.WriteLine("knight".ToUpper());
                """, ["KNIGHT", "Knight", "knight", NoCompile], "KNIGHT",
                "ToUpper() gives back a copy of the string in capital letters."),
            Code("""
                int count = "5";
                Console.WriteLine(count);
                """, ["5", "0", "\"5\"", NoCompile], NoCompile,
                "C# is statically typed: a string can't be stored in an int. int.Parse(\"5\") would convert it.",
                "CS0029"),
        ],
        ["medium"] =
        [
            Code("""
                int total = 0;
                for (int n = 1; n < 5; n++)
                    total += n;
                Console.WriteLine(total);
                """, ["10", "15", "4", "9"], "10",
                "n takes the values 1, 2, 3 and 4, and their sum is 10."),
            Code("""
                string word = "csharp";
                Console.WriteLine(word.Substring(1, 3));
                """, ["csh", "sha", "shar", "harp"], "sha",
                "Substring(1, 3) starts at index 1 and takes 3 characters. The second number is a length, not an end."),
            Code("""
                var scores = new Dictionary<string, int> { ["ana"] = 90, ["ben"] = 75 };
                Console.WriteLine(scores.GetValueOrDefault("cal", 0));
                """, ["0", "null", "cal", "KeyNotFoundException"], "0",
                "GetValueOrDefault() returns the default you give it when the key is missing. scores[\"cal\"] would throw."),
            Code("""
                int n = 15;
                string result = (n % 3, n % 5) switch
                {
                    (0, 0) => "FizzBuzz",
                    (0, _) => "Fizz",
                    (_, 0) => "Buzz",
                    _ => n.ToString(),
                };
                Console.WriteLine(result);
                """, ["FizzBuzz", "Fizz", "Buzz", "15"], "FizzBuzz",
                "A switch expression takes the first pattern that matches: both remainders are 0, so (0, 0) wins."),
            Code("""
                int count = 0;
                while (count < 10)
                    count += 3;
                Console.WriteLine(count);
                """, ["9", "10", "12", "3"], "12",
                "count goes 3, 6, 9, 12. The condition is only checked before each pass, so it stops once count is 12."),
            Code("""
                int Power(int number, int exponent = 2)
                {
                    int result = 1;
                    for (int i = 0; i < exponent; i++)
                        result *= number;
                    return result;
                }

                Console.WriteLine(Power(3));
                """, ["6", "9", "27", NoCompile], "9",
                "exponent is optional and uses its default of 2, so the result is 3 * 3."),
            Code("""
                var nums = new List<int> { 4, 1, 3 };
                nums.Sort();
                Console.WriteLine(string.Join(",", nums));
                """, ["1,3,4", "4,1,3", "4,3,1", NoCompile], "1,3,4",
                "List<T>.Sort() sorts the list in place, so nums itself is now in order."),
            Code("""
                string name = "Ada";
                int level = 3;
                Console.WriteLine($"{name} is level {level + 1}");
                """, ["Ada is level 4", "Ada is level 3 + 1", "{name} is level {level + 1}", "Ada is level 31"],
                "Ada is level 4",
                "An interpolated string ($\"...\") evaluates the expressions inside {} and inserts the results."),
            Code("""
                string[] letters = { "a", "b", "c", "d" };
                Console.WriteLine(string.Join("", letters[^2..]));
                """, ["cd", "d", "bc", "c"], "cd",
                "^2 is the second item from the end, and ^2.. is the range from there to the end."),
            Code("""
                for (int i = 0; i < 5; i++)
                {
                    if (i == 3)
                        break;
                    Console.Write(i + " ");
                }
                """, ["0 1 2", "0 1 2 3", "0 1 2 4", "3"], "0 1 2",
                "break leaves the loop as soon as i is 3, before 3 is printed."),
            Code("""
                void Change(int value)
                {
                    value = 5;
                }

                int x = 10;
                Change(x);
                Console.WriteLine(x);
                """, ["5", "10", "0", NoCompile], "10",
                "An int is passed by value: Change() gets its own copy, and x is untouched."),
            Code("""
                Console.WriteLine("hello world".Split(' ').Length);
                """, ["2", "11", "10", "1"], "2",
                "Split(' ') breaks the string at the space into an array of two strings."),
            Code("""
                var castle = new Dictionary<string, int> { ["towers"] = 4, ["gates"] = 1 };
                int total = 0;
                foreach (var pair in castle)
                    total += pair.Value;
                Console.WriteLine(total);
                """, ["5", "2", "41", NoCompile], "5",
                "Looping over a Dictionary gives KeyValuePair items, each with a Key and a Value: 4 + 1 = 5."),
            Code("""
                void Add(ref int value)
                {
                    value += 1;
                }

                int n = 1;
                Add(ref n);
                Add(ref n);
                Console.WriteLine(n);
                """, ["1", "2", "3", NoCompile], "3",
                "ref passes the variable itself, not a copy, so both calls change n."),
            Code("""
                string s = "abc";
                s.ToUpper();
                Console.WriteLine(s);
                """, ["abc", "ABC", "Abc", NoCompile], "abc",
                "Strings can't be changed. ToUpper() returns a new string, and this code throws it away."),
            Code("""
                string Greet(string name, string greeting = "Hello") => $"{greeting}, {name}!";

                Console.WriteLine(Greet("Ada", greeting: "Hail"));
                """, ["Hail, Ada!", "Hello, Ada!", "Hello, Hail!", NoCompile], "Hail, Ada!",
                "A named argument (greeting: ...) replaces the optional parameter's default for that call."),
            Code("""
                for (int i = 0; i < 3; i++)
                {
                }
                Console.WriteLine(i);
                """, ["3", "2", "0", NoCompile], NoCompile,
                "A variable declared in a for statement only exists inside that loop, so i is out of scope here.",
                "CS0103"),
            Code("""
                for (int i = 0; i < 5; i++)
                {
                    if (i % 2 == 0)
                        continue;
                    Console.Write(i + " ");
                }
                """, ["1 3", "0 2 4", "0 1 2 3 4", "1 3 5"], "1 3",
                "continue skips the rest of the loop body for that pass, so the even numbers are never printed."),
            Code("""
                var knights = new Dictionary<string, int> { ["Ana"] = 3 };
                knights["Ben"] = 5;
                knights["Ana"] = 4;
                Console.WriteLine($"{knights.Count} {knights["Ana"]}");
                """, ["2 4", "3 4", "2 3", "ArgumentException"], "2 4",
                "Assigning through the indexer replaces an existing key's value. Only Add() would throw on a repeat."),
            Code("""
                for (int i = 10; i > 0; i -= 3)
                    Console.Write(i + " ");
                """, ["10 7 4 1", "10 7 4", "1 4 7 10", "10 7 4 1 -2"], "10 7 4 1",
                "i goes down by 3 each pass, and the loop stops when i > 0 is false, at -2."),
        ],
        ["hard"] =
        [
            Code("""
                var squares = Enumerable.Range(0, 6).Where(x => x % 2 == 0).Select(x => x * x);
                Console.WriteLine(string.Join(",", squares));
                """, ["0,4,16", "4,16", "1,9,25", "0,2,4"], "0,4,16",
                "Where() keeps the even numbers 0, 2 and 4, then Select() squares them."),
            Code("""
                var list = new List<int> { 1, 2 };
                var query = list.Select(x => x * 10);
                list.Add(3);
                Console.WriteLine(query.Count());
                """, ["2", "3", "0", NoCompile], "3",
                "LINQ queries are lazy: Select() runs only when the results are asked for, by then over 3 items."),
            Code("""
                var a = new Point { X = 1 };
                var b = a;
                b.X = 2;
                Console.WriteLine(a.X);

                struct Point { public int X; }
                """, ["1", "2", "0", NoCompile], "1",
                "A struct is a value type: b = a copies it, so changing b leaves a alone."),
            Code("""
                var a = new Point { X = 1 };
                var b = a;
                b.X = 2;
                Console.WriteLine(a.X);

                class Point { public int X; }
                """, ["1", "2", "0", NoCompile], "2",
                "A class is a reference type: a and b refer to the same object, so a change through b shows in a."),
            Code("""
                Func<int, Func<int, int>> makeMultiplier = n => x => x * n;
                var triple = makeMultiplier(3);
                Console.WriteLine(triple(7));
                """, ["21", "10", "7", NoCompile], "21",
                "The inner lambda remembers n = 3 from the call that made it (a closure), so triple(7) is 7 * 3."),
            Code("""
                double Average(params int[] values) => (double)values.Sum() / values.Length;

                Console.WriteLine(Average(2, 4, 9));
                """, ["5", "5.0", "15", NoCompile], "5",
                "params collects the arguments into an array. 15.0 / 3 is 5, and a whole double prints with no decimal point."),
            Code("""
                string[] words = { "pear", "fig", "kiwi", "apple" };
                var sorted = words.OrderBy(w => w.Length).ThenBy(w => w);
                Console.WriteLine(string.Join(" ", sorted));
                """, ["fig kiwi pear apple", "fig pear kiwi apple", "apple fig kiwi pear", "apple kiwi pear fig"],
                "fig kiwi pear apple",
                "OrderBy() sorts by length first, then ThenBy() breaks ties alphabetically, so kiwi comes before pear."),
            Code("""
                int Mystery(int n) => n <= 1 ? 1 : n * Mystery(n - 1);

                Console.WriteLine(Mystery(5));
                """, ["120", "15", "24", "StackOverflowException"], "120",
                "Mystery() is a recursive factorial: 5 * 4 * 3 * 2 * 1 = 120."),
            Code("""
                string[] names = { "Ana", "Ben", "Cy" };
                int[] ages = { 30, 25 };
                var pairs = names.Zip(ages, (name, age) => $"{name}={age}");
                Console.WriteLine(string.Join(" ", pairs));
                """, ["Ana=30 Ben=25", "Ana=30 Ben=25 Cy=0", "Ana=30 Ben=25 Cy=", "IndexOutOfRangeException"],
                "Ana=30 Ben=25",
                "Zip() stops at the end of the shorter sequence, so Cy is left out."),
            Code("""
                string word = "banana";
                var counts = word.GroupBy(c => c).Select(g => $"{g.Key}{g.Count()}");
                Console.WriteLine(string.Join(" ", counts));
                """, ["b1 a3 n2", "a3 b1 n2", "b1 a1 n1", "b1 a1 n1 a1 n1 a1"], "b1 a3 n2",
                "A string is a sequence of chars. GroupBy() makes one group per letter, in the order each first appears."),
            Code("""
                Func<int> Counter()
                {
                    int count = 0;
                    return () => ++count;
                }

                var tick = Counter();
                tick();
                tick();
                Console.WriteLine(tick());
                """, ["1", "3", "0", NoCompile], "3",
                "The lambda captures the variable count itself, which lives on between calls."),
            Code("""
                string Check(int n)
                {
                    try
                    {
                        return (10 / n).ToString();
                    }
                    catch (DivideByZeroException)
                    {
                        return "oops";
                    }
                    finally
                    {
                        Console.Write("done ");
                    }
                }

                Console.WriteLine(Check(0));
                """, ["done oops", "oops done", "oops", "DivideByZeroException"], "done oops",
                "The finally block runs before the method hands back its return value, so \"done\" prints first."),
            Code("""
                var actions = new List<Func<int>>();
                for (int i = 0; i < 3; i++)
                    actions.Add(() => i);
                Console.WriteLine(string.Join(",", actions.Select(a => a())));
                """, ["0,1,2", "3,3,3", "2,2,2", NoCompile], "3,3,3",
                "A for loop has one i, shared by all three lambdas. By the time they run, the loop has left it at 3."),
            Code("""
                IEnumerable<int> Numbers()
                {
                    Console.Write("start ");
                    yield return 1;
                    yield return 2;
                }

                var seq = Numbers();
                Console.Write("first ");
                Console.WriteLine(seq.First());
                """, ["first start 1", "start first 1", "first 1", "start 1 2 first 1"], "first start 1",
                "Calling an iterator method runs none of its code. It starts only when something asks for the first item."),
            Code("""
                string Describe(object o) => o switch
                {
                    int n when n > 10 => "big",
                    int => "small",
                    string s => s.Length.ToString(),
                    _ => "other",
                };

                Console.WriteLine(Describe(5) + " " + Describe("sword"));
                """, ["small 5", "big 5", "small sword", "other other"], "small 5",
                "The patterns are tried in order: 5 is an int but not over 10, and \"sword\" is a string of length 5."),
            Code("""
                var a = new Gem("ruby", 5);
                var b = a with { Value = 9 };
                Console.WriteLine($"{a.Value} {b.Value} {a == new Gem("ruby", 5)}");

                record Gem(string Name, int Value);
                """, ["5 9 True", "9 9 True", "5 9 False", "9 9 False"], "5 9 True",
                "with makes a changed copy and leaves a alone. Records compare by their values, not as references."),
            Code("""
                object a = 1;
                object b = 1;
                Console.WriteLine($"{a == b} {a.Equals(b)}");
                """, ["False True", "True True", "False False", "True False"], "False True",
                "Each int is boxed into its own object. == on objects compares references, while Equals() compares values."),
            Code("""
                var a = new Vault();
                var b = new Vault();
                a.Add();
                b.Add();
                Console.WriteLine($"{Vault.Total} {a.Mine}");

                class Vault
                {
                    public static int Total;
                    public int Mine;

                    public void Add()
                    {
                        Total++;
                        Mine++;
                    }
                }
                """, ["2 1", "1 1", "2 2", "1 2"], "2 1",
                "A static field belongs to the class, so all objects share Total. Each object has its own Mine."),
            Code("""
                Animal pet = new Dog();
                Console.WriteLine(pet.Speak() + " " + pet.Name());

                class Animal
                {
                    public virtual string Speak() => "...";
                    public string Name() => "animal";
                }

                class Dog : Animal
                {
                    public override string Speak() => "Woof";
                    public new string Name() => "dog";
                }
                """, ["Woof animal", "Woof dog", "... animal", "... dog"], "Woof animal",
                "override replaces the method for every caller. new only hides it, so a caller using an Animal gets Animal's."),
            Code("""
                int[] nums = { 1, 2, 3, 4 };
                Console.WriteLine(nums.Aggregate(1, (total, n) => total * n));
                """, ["24", "10", "1", "4"], "24",
                "Aggregate() folds the sequence, starting from 1: 1 * 1 * 2 * 3 * 4 = 24."),
        ],
    };

    // One bonus riddle for each dragon, a step harder than its level's own questions.
    public static readonly Dictionary<(string Level, string Path), Question> Dragons = new()
    {
        [("easy", "cave")] = Code("""
            int a = 5;
            int b = a++;
            int c = ++a;
            Console.WriteLine($"{a} {b} {c}");
            """, ["7 5 7", "6 5 6", "7 6 7", "7 5 6"], "7 5 7",
            "a++ hands back the old value and then adds 1, so b is 5. ++a adds 1 first, so c and a are both 7."),
        [("medium", "cave")] = Code("""
            var hoard = new Dictionary<string, int> { ["gold"] = 3, ["gems"] = 5, ["crowns"] = 1 };
            int total = 0;
            foreach (var (item, count) in hoard)
            {
                if (count > 2)
                    total += count;
            }
            Console.WriteLine(total);
            """, ["8", "9", "5", "3"], "8",
            "Each KeyValuePair can be split into (key, value). Only gold (3) and gems (5) are more than 2."),
        [("hard", "cave")] = Code("""
            IEnumerable<int> Flatten(object[] items)
            {
                foreach (var item in items)
                {
                    if (item is object[] inner)
                    {
                        foreach (var n in Flatten(inner))
                            yield return n;
                    }
                    else
                    {
                        yield return (int)item;
                    }
                }
            }

            object[] data = { 1, new object[] { 2, new object[] { 3, 4 } }, 5 };
            Console.WriteLine(string.Join(",", Flatten(data)));
            """, ["1,2,3,4,5", "1,2,5", "1,System.Object[],5", "InvalidCastException"], "1,2,3,4,5",
            "Each inner array is flattened by a recursive call, however deep it goes, and its items are yielded in order."),
        [("easy", "forest")] = Code("""
            var trees = new List<string> { "oak", "elm", "ash" };
            trees.Insert(1, "fir");
            trees.RemoveAt(0);
            Console.WriteLine(trees[1]);
            """, ["elm", "fir", "ash", "oak"], "elm",
            "After Insert(): oak, fir, elm, ash. After RemoveAt(0): fir, elm, ash. So index 1 is elm."),
        [("medium", "forest")] = Code("""
            string word = "amethyst";
            Console.WriteLine(word[2..^3] + word[^1]);
            """, ["etht", "ethy", "eth", "ethyt"], "etht",
            "word has 8 letters, so ^3 is index 5. The range 2..5 is \"eth\", and ^1 is the last letter, t."),
        [("hard", "forest")] = Code("""
            var actions = new List<Func<int>>();
            for (int i = 1; i <= 3; i++)
            {
                int copy = i;
                actions.Add(() => copy * 10);
            }
            Console.WriteLine(string.Join(",", actions.Select(a => a())));
            """, ["10,20,30", "40,40,40", "30,30,30", "0,10,20"], "10,20,30",
            "copy is a new variable on each pass, so each lambda captures its own. Without it they'd share i."),
        [("easy", "castle")] = Code("""
            double result = 7 / 2 * 2.0;
            Console.WriteLine(result);
            """, ["6", "7", "6.0", "3.5"], "6",
            "Left to right: 7 / 2 is integer division, giving 3. Then 3 * 2.0 is 6, printed with no decimal point."),
        [("medium", "castle")] = Code("""
            bool ok = int.TryParse("12x", out int value);
            Console.WriteLine($"{ok} {value}");
            """, ["False 0", "True 12", "False 12", "FormatException"], "False 0",
            "TryParse() never throws on bad input: it returns false and sets its out parameter to 0."),
        [("hard", "castle")] = Code("""
            int calls = 0;
            var query = Enumerable.Range(0, 3).Select(n => { calls++; return n; });
            query.Sum();
            query.Sum();
            Console.WriteLine(calls);
            """, ["6", "3", "0", NoCompile], "6",
            "A lazy query isn't stored: it runs again each time it's enumerated, so the lambda is called 3 + 3 times."),
    };

    // The final boss's nine: the hardest questions in the game.
    public static readonly Question[] Boss =
    [
        Code("""
            new Child();

            class Parent
            {
                public Parent() => Console.Write(Describe() + " ");
                public virtual string Describe() => "parent";
            }

            class Child : Parent
            {
                string name = "field";

                public Child()
                {
                    name = "ctor";
                    Console.Write(Describe());
                }

                public override string Describe() => name;
            }
            """, ["field ctor", "parent ctor", "ctor ctor", "parent field"], "field ctor",
            "Field initializers run before the base constructor. Parent's constructor then calls the override, which already sees \"field\"."),
        Code("""
            var list = new List<Counter> { new Counter() };
            var copy = list[0];
            copy.Count++;
            list[0].Bump();
            Console.WriteLine($"{copy.Count} {list[0].Count}");

            struct Counter
            {
                public int Count;
                public void Bump() => Count++;
            }
            """, ["1 0", "1 1", "2 2", NoCompile], "1 0",
            "A List's indexer returns a copy of a struct, so Bump() changes a temporary copy and the item in the list stays 0."),
        Code("""
            IBump boxed = new Counter();
            boxed.Bump();
            boxed.Bump();
            Counter unboxed = (Counter)boxed;
            unboxed.Bump();
            Console.WriteLine($"{((Counter)boxed).N} {unboxed.N}");

            interface IBump
            {
                void Bump();
            }

            struct Counter : IBump
            {
                public int N;
                public void Bump() => N++;
            }
            """, ["2 3", "3 3", "0 1", "2 2"], "2 3",
            "Calls through the interface change the boxed struct itself, making it 2. Unboxing copies it, so only the copy reaches 3."),
        Code("""
            var gate = new TaskCompletionSource<string>();

            async Task<string> Work()
            {
                Console.Write("A ");
                string text = await gate.Task;
                Console.Write("B ");
                return text + "C";
            }

            var task = Work();
            Console.Write("D ");
            gate.SetResult("E");
            Console.Write("F ");
            Console.WriteLine(await task);
            """, ["A D B F EC", "A D F B EC", "D A B F EC", "A B D F EC"], "A D B F EC",
            "An async method runs synchronously up to its first unfinished await. SetResult() then runs the continuation right there, before F."),
        Code("""
            int? a = null;
            int? b = 5;
            Console.WriteLine($"{a + b == null} {(a ?? 0) + b} {a < b} {a >= b}");
            """, ["True 5 False False", "True 5 True False", "False 5 False True", "InvalidOperationException"],
            "True 5 False False",
            "Arithmetic with a null int? gives null, and every ordered comparison with null is false, so both < and >= are false."),
        Code("""
            Pick.It(1);
            Pick.It('a');
            Pick.It(1.5f);

            static class Pick
            {
                public static void It(long n) => Console.Write("long ");
                public static void It(double d) => Console.Write("double ");
                public static void It(object o) => Console.Write("object ");
            }
            """, ["long long double", "object object object", "long object double", "double double double"],
            "long long double",
            "A numeric conversion beats boxing to object. int and char both convert to long and double, and long is the better match. float only fits double."),
        Code("""
            var door = new Door();
            IOpen asOpen = door;
            Console.WriteLine($"{door.Open()} {asOpen.Open()}");

            interface IOpen
            {
                string Open();
            }

            class Door : IOpen
            {
                public string Open() => "public";
                string IOpen.Open() => "explicit";
            }
            """, ["public explicit", "public public", "explicit explicit", NoCompile], "public explicit",
            "An explicit interface implementation is only reached through the interface. Through the class, the public method is the one called."),
        Code("""
            int min = 1;
            var query = new[] { 1, 2, 3 }.Where(n => n > min);
            min = 2;
            var first = query.ToList();
            min = 0;
            Console.WriteLine($"{first.Count} {query.Count()}");
            """, ["1 3", "2 2", "2 3", "1 1"], "1 3",
            "The lambda captures the variable min, and the query runs only when enumerated: ToList() sees min = 2 and Count() sees min = 0."),
        Code("""
            IEnumerable<int> Numbers()
            {
                try
                {
                    yield return 1;
                    yield return 2;
                }
                finally
                {
                    Console.Write("closed ");
                }
            }

            Console.WriteLine(Numbers().First());
            """, ["closed 1", "1 closed", "1", "2 closed"], "closed 1",
            "First() disposes the enumerator as it finishes, which runs the iterator's finally block before First() returns its value."),
    ];
}
