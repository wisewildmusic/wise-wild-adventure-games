// All 78 questions. Snippets are raw string literals, a C++ way of writing text that runs over several
// lines and is full of quotes, with nothing to escape. As the game's start page says, every riddle is
// standard C++20 with the headers it needs: plain statements stand for the inside of main(), and a
// snippet showing its own main() is the whole program.
#include "Questions.hpp"

#include <map>
#include <stdexcept>
#include <string_view>
#include <utility>

namespace templaria {
namespace {

const std::string prints = "What does this code print?";
const std::string no_compile = "Compile error";
const std::string undefined_behavior = "Undefined behavior";
const std::string terminates = "std::terminate is called";

using Options = std::vector<std::string>;

/// A raw string starts and ends on lines of its own, so that it can be read in the source: those two
/// line ends aren't part of the snippet. (Nor are a Windows editor's carriage returns.)
std::string tidy(std::string_view source) {
    std::string code;
    for (const char c : source)
        if (c != '\r') code += c;
    if (code.starts_with('\n')) code.erase(0, 1);
    if (code.ends_with('\n')) code.pop_back();
    return code;
}

Question snippet(std::string_view source, Options options, std::string answer, std::string explain) {
    return {prints, tidy(source), std::move(options), std::move(answer), std::move(explain), {}, {}};
}

/// A snippet that doesn't compile, with MSVC's error code for why.
Question refused(std::string_view source, Options options, std::string explain, std::string error_code) {
    return {prints, tidy(source), std::move(options), no_compile, std::move(explain), std::move(error_code), {}};
}

/// A snippet whose behavior is undefined, with what the sanitizers must catch it doing.
Question undefined(std::string_view source, Options options, std::string explain, std::string finding) {
    return {prints, tidy(source), std::move(options), undefined_behavior, std::move(explain), {}, std::move(finding)};
}

Question ask(std::string prompt, Options options, std::string answer, std::string explain) {
    return {std::move(prompt), {}, std::move(options), std::move(answer), std::move(explain), {}, {}};
}

}  // namespace

const std::vector<Question>& level_questions(const std::string& level) {
    static const std::map<std::string, std::vector<Question>> levels = {
        {"easy", {
            snippet(R"cpp(
int x = 5;
x = x + 2;
std::cout << x;
)cpp", {"5", "7", "52", "x + 2"}, "7",
                "x starts at 5, then x + 2 (which is 7) is stored back into x."),
            ask("Which of these is a valid C++ variable name?",
                {"2ndPlace", "my-score", "player_name", "class"}, "player_name",
                "Names can't start with a digit, can't contain '-', and can't be a keyword such as 'class'."),
            snippet(R"cpp(
std::string fruits[] = {"apple", "banana", "cherry"};
std::cout << fruits[1];
)cpp", {"apple", "banana", "cherry", no_compile}, "banana",
                "Array indexes start at 0, so index 1 is the second item."),
            ask("What type does the literal 3.14 have in C++?",
                {"int", "float", "double", "long double"}, "double",
                "A number with a decimal point is a double unless it ends in f (float) or L (long double)."),
            snippet(R"cpp(
std::string word = "cat";
word[0] = 'b';
std::cout << word;
)cpp", {"bat", "cat", "bcat", no_compile}, "bat",
                "A std::string can be changed in place: word[0] is the first character itself, not a copy."),
            snippet(R"cpp(
for (int i = 0; i < 3; i++)
    std::cout << i << " ";
)cpp", {"0 1 2", "1 2 3", "0 1 2 3", "1 2"}, "0 1 2",
                "i starts at 0 and the loop stops as soon as i < 3 is false."),
            snippet(R"cpp(
std::string greet(std::string name) {
    return "Hi " + name;
}

int main() {
    std::cout << greet("Ada");
}
)cpp", {"Hi Ada", "Hi name", "greet Ada", "Nothing"}, "Hi Ada",
                "The argument \"Ada\" is passed into the name parameter and joined onto \"Hi \"."),
            ask("Which keyword declares a variable whose type the compiler works out for you?",
                {"var", "let", "auto", "dim"}, "auto",
                "auto x = 5; is still strongly typed: the compiler makes x an int, and it stays one."),
            snippet(R"cpp(
std::vector<int> items = {1, 2, 3};
items.push_back(4);
std::cout << items.size();
)cpp", {"3", "4", "5", "10"}, "4",
                "push_back() puts one item on the end, so the vector now holds 4 items."),
            snippet(R"cpp(
std::cout << (7 > 3 && 2 > 5);
)cpp", {"true", "false", "0", "1"}, "0",
                "&& is only true when both sides are, and 2 > 5 isn't. A bool prints as 0 or 1 unless you ask for std::boolalpha."),
            ask("Which line lets a program use std::cout?",
                {"#include <iostream>", "import stdio;", "using cout;", "#define iostream"}, "#include <iostream>",
                "#include pastes in a header's declarations before compiling, and <iostream> is the one that declares std::cout."),
            snippet(R"cpp(
std::cout << 10 / 3;
)cpp", {"3", "3.33", "3.33333", "4"}, "3",
                "Dividing one int by another gives an int: the remainder is dropped. 10 / 3.0 would give 3.33333."),
            snippet(R"cpp(
std::cout << 17 % 5;
)cpp", {"3", "2", "3.4", "12"}, "2",
                "% gives the remainder of a division: 17 is 3 fives (15) with 2 left over."),
            snippet(R"cpp(
std::string name = "Castle";
std::cout << name.size();
)cpp", {"5", "6", "7", "Castle"}, "6",
                "size() counts the characters in a string: C-a-s-t-l-e is 6."),
            snippet(R"cpp(
char letter = 'A';
letter = letter + 1;
std::cout << letter;
)cpp", {"A", "B", "66", no_compile}, "B",
                "A char is a small number underneath. 'A' + 1 is the number for 'B', and printing a char shows its letter."),
            snippet(R"cpp(
int x = 3;
if (x > 5)
    std::cout << "big";
else if (x > 2)
    std::cout << "medium";
else
    std::cout << "small";
)cpp", {"big", "medium", "small", "medium small"}, "medium",
                "x > 5 is false, so C++ checks the else if: 3 > 2 is true, and the last else is skipped."),
            snippet(R"cpp(
int total = 0;
for (int n : {2, 4, 6})
    total += n;
std::cout << total;
)cpp", {"6", "12", "246", "0"}, "12",
                "The loop adds each number to total in turn: 2 + 4 + 6 = 12."),
            snippet(R"cpp(
int x = 10;
int& r = x;
r = 20;
std::cout << x;
)cpp", {"10", "20", "0", no_compile}, "20",
                "A reference is another name for the same variable, so changing r changes x."),
            refused(R"cpp(
const int lives = 3;
lives = 2;
std::cout << lives;
)cpp", {"3", "2", "0", no_compile},
                "const promises a variable will never change, and the compiler holds you to it.", "C3892"),
            snippet(R"cpp(
int x = 3.9;
std::cout << x;
)cpp", {"3", "4", "3.9", no_compile}, "3",
                "Storing a double in an int simply cuts off the fraction. It doesn't round, and it isn't an error, though with braces, int x{3.9}, it would be."),
        }},
        {"medium", {
            snippet(R"cpp(
int x = 5;
int* p = &x;
*p = 9;
std::cout << x;
)cpp", {"5", "9", "The address of x", no_compile}, "9",
                "p holds the address of x, and *p is x itself, so *p = 9 changes x."),
            snippet(R"cpp(
std::string word = "template";
std::cout << word.substr(1, 3);
)cpp", {"tem", "emp", "empl", "late"}, "emp",
                "substr(1, 3) starts at index 1 and takes 3 characters. The second number is a length, not an end."),
            snippet(R"cpp(
std::map<std::string, int> scores;
scores["ana"] = 90;
std::cout << scores["cal"] << " " << scores.size();
)cpp", {"0 2", "0 1", "90 1", "std::out_of_range"}, "0 2",
                "Reading a missing key with [] doesn't fail: it quietly adds the key with a value of 0, so the map now has 2 items. at() would throw."),
            snippet(R"cpp(
int n = 1;
switch (n) {
    case 1: std::cout << "one ";
    case 2: std::cout << "two ";
    case 3: std::cout << "three "; break;
    default: std::cout << "other";
}
)cpp", {"one", "one two", "one two three", "one two three other"}, "one two three",
                "A case without a break falls through into the next one. The break after three stops it."),
            snippet(R"cpp(
std::map<std::string, int> m = {{"pear", 1}, {"apple", 2}, {"fig", 3}};
for (const auto& [key, value] : m)
    std::cout << key[0];
)cpp", {"afp", "paf", "pfa", no_compile}, "afp",
                "A std::map always keeps its keys in sorted order, whatever order they went in."),
            snippet(R"cpp(
int power(int number, int exponent = 2) {
    int result = 1;
    for (int i = 0; i < exponent; i++)
        result *= number;
    return result;
}

int main() {
    std::cout << power(3);
}
)cpp", {"6", "9", "27", no_compile}, "9",
                "exponent is optional and uses its default of 2, so the result is 3 * 3."),
            snippet(R"cpp(
std::vector<int> nums = {4, 1, 3};
std::sort(nums.begin(), nums.end());
for (int n : nums)
    std::cout << n;
)cpp", {"134", "413", "431", no_compile}, "134",
                "std::sort() takes a range of iterators and sorts it in place, so nums itself is now in order."),
            snippet(R"cpp(
void change(int value) {
    value = 5;
}

int main() {
    int x = 10;
    change(x);
    std::cout << x;
}
)cpp", {"5", "10", "0", no_compile}, "10",
                "An int parameter is a copy: change() gets its own, and x is untouched."),
            snippet(R"cpp(
void add(int& value) {
    value += 1;
}

int main() {
    int n = 1;
    add(n);
    add(n);
    std::cout << n;
}
)cpp", {"1", "2", "3", no_compile}, "3",
                "int& passes the variable itself, not a copy, so both calls change n."),
            snippet(R"cpp(
std::vector<int> v = {1, 2, 3};
for (auto x : v)
    x *= 2;
for (auto& x : v)
    x += 1;
std::cout << v[0] << v[1] << v[2];
)cpp", {"234", "246", "357", "123"}, "234",
                "auto x is a copy, so the first loop changes nothing. auto& x is a reference, so the second really adds 1 to each item."),
            snippet(R"cpp(
int a[] = {10, 20, 30};
int* p = a;
p++;
std::cout << *p + 1;
)cpp", {"11", "21", "30", no_compile}, "21",
                "An array's name turns into a pointer to its first item, and p++ moves it on one int, to 20. * comes before +, so it's 20 + 1."),
            refused(R"cpp(
std::string s = "Hello, " + "world";
std::cout << s;
)cpp", {"Hello, world", "Hello, ", "world", no_compile},
                "String literals aren't std::strings. They're char arrays, which turn into pointers, and two pointers can't be added.", "C2110"),
            snippet(R"cpp(
std::vector<int> v = {1, 2, 3};
try {
    std::cout << v.at(3);
} catch (const std::out_of_range&) {
    std::cout << "caught";
}
)cpp", {"caught", "0", "3", undefined_behavior}, "caught",
                "at() checks the index and throws std::out_of_range when it's too big. v[3] wouldn't check, and that would be undefined behavior."),
            snippet(R"cpp(
int next_id() {
    static int id = 0;
    return ++id;
}

int main() {
    next_id();
    next_id();
    std::cout << next_id();
}
)cpp", {"1", "3", "0", no_compile}, "3",
                "A static local is made once, the first time through, and lives on between calls."),
            undefined(R"cpp(
int a[3] = {1, 2, 3};
std::cout << a[3];
)cpp", {"3", "0", undefined_behavior, no_compile},
                "The indexes stop at 2, and C++ doesn't check. Reading a[3] reads past the end of the array, and from then on the standard doesn't say what happens.",
                "out-of-bounds"),
            snippet(R"cpp(
int n = 1;
auto by_value = [n] { return n; };
auto by_ref = [&n] { return n; };
n = 5;
std::cout << by_value() << " " << by_ref();
)cpp", {"1 5", "5 5", "1 1", "5 1"}, "1 5",
                "[n] copies n when the lambda is made. [&n] refers to n itself, so it sees the later change."),
            snippet(R"cpp(
std::vector<int> v = {7, 8, 9};
auto it = std::find(v.begin(), v.end(), 8);
std::cout << it - v.begin();
)cpp", {"1", "2", "8", no_compile}, "1",
                "find() returns an iterator to the first match, and subtracting begin() gives how far along it is: index 1."),
            snippet(R"cpp(
void show(int) { std::cout << "int "; }
void show(double) { std::cout << "double "; }
void show(const std::string&) { std::cout << "string "; }

int main() {
    show(1);
    show(1.0);
    show(std::string("1"));
}
)cpp", {"int double string", "int int string", "double double string", no_compile}, "int double string",
                "The compiler picks the overload by the argument's type: 1 is an int and 1.0 is a double."),
            snippet(R"cpp(
std::cout << -7 / 2 << " " << -7 % 2;
)cpp", {"-3 -1", "-4 1", "-3 1", "-4 -1"}, "-3 -1",
                "Integer division cuts toward zero, and the remainder takes the sign of the left side."),
            snippet(R"cpp(
int a[5] = {1, 2};
std::cout << a[1] + a[4] << " " << sizeof(a) / sizeof(a[0]);
)cpp", {"2 5", "2 2", "1 5", undefined_behavior}, "2 5",
                "An array with too few initializers fills the rest with zeros, so a[4] is 0. sizeof gives the whole array's bytes, and dividing by one item's gives its length."),
        }},
        {"hard", {
            snippet(R"cpp(
struct Guard {
    std::string name;
    Guard(std::string n) : name(n) { std::cout << "+" << name << " "; }
    ~Guard() { std::cout << "-" << name << " "; }
};

int main() {
    Guard a("a");
    Guard b("b");
}
)cpp", {"+a +b -b -a", "+a +b -a -b", "+a -a +b -b", "+a +b"}, "+a +b -b -a",
                "Objects are destroyed automatically at the end of their scope, in reverse order of creation. That's RAII."),
            snippet(R"cpp(
struct Animal {
    virtual ~Animal() = default;
    virtual std::string speak() { return "..."; }
    std::string name() { return "animal"; }
};

struct Dog : Animal {
    std::string speak() override { return "Woof"; }
    std::string name() { return "dog"; }
};

int main() {
    Dog d;
    Animal& pet = d;
    std::cout << pet.speak() << " " << pet.name();
}
)cpp", {"Woof animal", "Woof dog", "... animal", "... dog"}, "Woof animal",
                "A virtual function is chosen by the object's real type. A non-virtual one is chosen by the reference's type, here Animal."),
            snippet(R"cpp(
struct Animal {
    virtual ~Animal() = default;
    virtual std::string speak() const { return "..."; }
};

struct Dog : Animal {
    std::string speak() const override { return "Woof"; }
};

void hear(Animal a) {
    std::cout << a.speak();
}

int main() {
    hear(Dog{});
}
)cpp", {"...", "Woof", no_compile, undefined_behavior}, "...",
                "hear() takes an Animal by value, so only the Animal part of the Dog is copied. That's object slicing, and the Dog is gone."),
            snippet(R"cpp(
auto a = std::make_unique<int>(7);
auto b = std::move(a);
std::cout << (a == nullptr) << " " << *b;
)cpp", {"1 7", "0 7", "1 0", no_compile}, "1 7",
                "A unique_ptr has one owner. std::move hands ownership to b and leaves a holding nullptr."),
            refused(R"cpp(
auto a = std::make_unique<int>(7);
auto b = a;
std::cout << *b;
)cpp", {"7", "0", undefined_behavior, no_compile},
                "A unique_ptr can't be copied, because then two would own the same object: its copy constructor is deleted. std::move(a) would compile.", "C2280"),
            snippet(R"cpp(
auto a = std::make_shared<int>(1);
auto b = a;
{
    auto c = a;
    std::cout << a.use_count() << " ";
}
std::cout << a.use_count();
)cpp", {"3 2", "3 3", "2 1", "1 1"}, "3 2",
                "Each copy of a shared_ptr adds to the count. c is destroyed at its closing brace, taking the count back to 2."),
            snippet(R"cpp(
template <typename T>
T twice(T value) {
    return value + value;
}

int main() {
    std::cout << twice(21) << " " << twice(std::string("ab"));
}
)cpp", {"42 abab", "42 ab2", "2121 abab", no_compile}, "42 abab",
                "The compiler stamps out one version of the template for each type used: int adds numbers, and std::string's + joins them."),
            snippet(R"cpp(
template <typename T>
std::string kind() { return "other"; }

template <>
std::string kind<int>() { return "int"; }

int main() {
    std::cout << kind<int>() << " " << kind<char>();
}
)cpp", {"int other", "int int", "other other", no_compile}, "int other",
                "The template<> version replaces the template for int alone. char falls back on the general one."),
            refused(R"cpp(
std::cout << std::max(1, 2.5);
)cpp", {"2.5", "2", "1", no_compile},
                "std::max takes two of the same type T, and here T can't be both int and double. std::max<double>(1, 2.5) would compile.", "C2672"),
            snippet(R"cpp(
int say(const char* name) {
    std::cout << name << " ";
    return 0;
}

struct Pair {
    int a;
    int b;
    Pair() : b(say("b")), a(say("a")) {}
};

int main() {
    Pair p;
}
)cpp", {"a b", "b a", "a", "b"}, "a b",
                "Members are always initialized in the order they're declared in the class, whatever order the constructor lists them in."),
            snippet(R"cpp(
std::vector<bool> flags = {false, false};
auto flag = flags[0];
flag = true;
std::cout << flags[0];
)cpp", {"1", "0", no_compile, undefined_behavior}, "1",
                "vector<bool> packs its items into bits, so [] returns a stand-in object, not a bool. auto copies the stand-in, which still refers to the bit."),
            snippet(R"cpp(
struct Gem {
    Gem() = default;
    Gem(const Gem&) { std::cout << "copy "; }
    Gem(Gem&&) noexcept { std::cout << "move "; }
};

int main() {
    Gem a;
    Gem b = a;
    Gem c = std::move(a);
}
)cpp", {"copy move", "move move", "copy copy", "move copy"}, "copy move",
                "a has a name, so Gem b = a copies it. std::move(a) marks it as free to take from, which picks the move constructor."),
            snippet(R"cpp(
struct Guard {
    ~Guard() { std::cout << "clean "; }
};

void risky() {
    Guard g;
    throw std::runtime_error("boom");
    std::cout << "after ";
}

int main() {
    try {
        risky();
    } catch (const std::exception& e) {
        std::cout << e.what();
    }
}
)cpp", {"clean boom", "boom clean", "after clean boom", "boom"}, "clean boom",
                "As an exception leaves a function, the stack unwinds and g's destructor runs, all before the catch block starts."),
            snippet(R"cpp(
int n = 0;
auto tick = [n]() mutable { return ++n; };
tick();
tick();
std::cout << tick() << " " << n;
)cpp", {"3 0", "3 3", "1 0", no_compile}, "3 0",
                "[n] gives the lambda its own copy, and mutable lets it change that copy, which it keeps between calls. The outer n stays 0."),
            snippet(R"cpp(
std::vector<double> v = {1.5, 2.5};
std::cout << std::accumulate(v.begin(), v.end(), 0);
)cpp", {"4", "3", "4.0", no_compile}, "3",
                "The running total has the type of the starting value, and 0 is an int: 0 + 1.5 is cut to 1, then 1 + 2.5 is cut to 3. Starting from 0.0 would give 4."),
            snippet(R"cpp(
std::vector<int> v = {0, 1, 2, 3, 4, 5};
auto squares = v | std::views::filter([](int x) { return x % 2 == 0; })
                 | std::views::transform([](int x) { return x * x; });
for (int n : squares)
    std::cout << n << " ";
)cpp", {"0 4 16", "4 16", "1 9 25", "0 2 4"}, "0 4 16",
                "filter keeps the even numbers 0, 2 and 4, then transform squares them. Views do their work only as the loop asks."),
            snippet(R"cpp(
struct Torch {
    Torch() { std::cout << "lit"; }
};

int main() {
    Torch t();
}
)cpp", {"lit", "Nothing", no_compile, undefined_behavior}, "Nothing",
                "The most vexing parse: Torch t(); declares a function named t that returns a Torch, so no Torch is made. Torch t; or Torch t{}; would light it."),
            snippet(R"cpp(
const std::string& r = std::string("a") + "b";
std::cout << r;
)cpp", {"ab", "a", undefined_behavior, no_compile}, "ab",
                "A temporary normally dies at the end of its line, but one bound directly to a const reference lives as long as the reference does."),
            snippet(R"cpp(
struct Coin {
    int value;
    Coin operator+(const Coin& other) const { return {value + other.value}; }
    bool operator<(const Coin& other) const { return value < other.value; }
};

int main() {
    Coin a{2}, b{3};
    std::cout << (a + b).value << " " << (a < b);
}
)cpp", {"5 1", "5 true", "23 1", no_compile}, "5 1",
                "Operators can be overloaded: a + b calls a.operator+(b), making a Coin worth 5. a < b is true, which prints as 1."),
            undefined(R"cpp(
int* p = new int(5);
delete p;
std::cout << *p;
)cpp", {"5", "0", undefined_behavior, no_compile},
                "delete gives the memory back, but p still holds its address, now dangling. Reading through it is undefined behavior, even if it happens to print 5.",
                "heap-use-after-free"),
        }},
    };
    const auto found = levels.find(level);
    if (found == levels.end()) throw std::runtime_error("no such level: " + level);
    return found->second;
}

// One bonus riddle for each dragon, a step harder than its level's own questions.
const Question& dragon_question(const std::string& level, const std::string& path) {
    static const std::map<std::pair<std::string, std::string>, Question> dragons = {
        {{"easy", "cave"}, snippet(R"cpp(
int a = 5;
int b = a++;
int c = ++a;
std::cout << a << " " << b << " " << c;
)cpp", {"7 5 7", "6 5 6", "7 6 7", "7 5 6"}, "7 5 7",
            "a++ hands back the old value and then adds 1, so b is 5. ++a adds 1 first, so c and a are both 7.")},
        {{"medium", "cave"}, snippet(R"cpp(
int a = 1, b = 2;
const int* p = &a;
p = &b;
b = 3;
std::cout << *p;
)cpp", {"3", "2", "1", no_compile}, "3",
            "const int* promises only not to change the value through p. p itself can point elsewhere, and b can still change on its own.")},
        {{"hard", "cave"}, snippet(R"cpp(
template <typename... Ts>
auto sum(Ts... values) {
    return (values + ...);
}

int main() {
    std::cout << sum(1, 2.5, 3);
}
)cpp", {"6.5", "6", "5.5", no_compile}, "6.5",
            "(values + ...) is a fold expression: 1 + (2.5 + 3). auto works out the result's type, a double.")},
        {{"easy", "forest"}, snippet(R"cpp(
char c = 'A';
std::cout << c + 1 << " " << char(c + 1);
)cpp", {"66 B", "B B", "A1 B", "66 66"}, "66 B",
            "Arithmetic turns a char into an int, so c + 1 is the number 66. Casting it back to char prints it as a letter.")},
        {{"medium", "forest"}, snippet(R"cpp(
std::string word = "gem";
int index = -1;
if (index < word.size())
    std::cout << "inside";
else
    std::cout << "outside";
)cpp", {"inside", "outside", no_compile, undefined_behavior}, "outside",
            "size() is unsigned, so -1 converts to unsigned for the comparison, becoming a huge number. That's well defined, and rarely what you meant.")},
        {{"hard", "forest"}, snippet(R"cpp(
struct Root { Root() { std::cout << "R "; } };
struct Leaf { Leaf() { std::cout << "L "; } };

struct Tree : Root {
    Leaf leaf;
    Tree() { std::cout << "T "; }
};

int main() {
    Tree t;
}
)cpp", {"R L T", "T R L", "L R T", "R T L"}, "R L T",
            "Building an object goes base class first, then its members, and the constructor's own body last.")},
        {{"easy", "castle"}, snippet(R"cpp(
double result = 7 / 2 * 2.0;
std::cout << result;
)cpp", {"6", "7", "6.0", "3.5"}, "6",
            "Left to right: 7 / 2 is integer division, giving 3. Then 3 * 2.0 is 6, and a whole double prints with no decimal point.")},
        {{"medium", "castle"}, snippet(R"cpp(
std::vector<int> v = {1, 2, 3, 4, 5, 6};
v.erase(std::remove_if(v.begin(), v.end(),
                       [](int x) { return x % 2 == 0; }),
        v.end());
std::cout << v.size() << " " << v.back();
)cpp", {"3 5", "6 6", "3 6", "6 5"}, "3 5",
            "remove_if() only shuffles the keepers forward and says where they end. erase() then really shortens the vector, leaving 1, 3 and 5.")},
        {{"hard", "castle"}, snippet(R"cpp(
void safe() noexcept {
    throw std::runtime_error("boom");
}

int main() {
    try {
        safe();
    } catch (...) {
        std::cout << "caught";
    }
}
)cpp", {"caught", "boom", "Nothing", terminates}, terminates,
            "noexcept is a promise. An exception trying to leave a noexcept function never reaches any catch: the program is ended on the spot.")},
    };
    return dragons.at({level, path});
}

// The final boss's nine: the hardest questions in the game. Some are undefined behavior, and some only
// look it, so the answer can't simply be guessed.
const std::vector<Question>& boss_questions() {
    static const std::vector<Question> boss = {
        snippet(R"cpp(
struct Base {
    Base() { std::cout << describe() << " "; }
    virtual ~Base() = default;
    virtual std::string describe() const { return "base"; }
};

struct Child : Base {
    std::string name = "field";
    Child() { std::cout << describe(); }
    std::string describe() const override { return name; }
};

int main() {
    Child c;
}
)cpp", {"base field", "field field", "base base", undefined_behavior}, "base field",
            "While Base's constructor runs, the object is still only a Base, so the virtual call stays in Base. By the time Child's constructor runs, it's a Child."),
        snippet(R"cpp(
struct Base {
    virtual ~Base() = default;
    virtual void hit(int power = 1) { std::cout << "base " << power; }
};

struct Boss : Base {
    void hit(int power = 99) override { std::cout << "boss " << power; }
};

int main() {
    Boss boss;
    Base& b = boss;
    b.hit();
}
)cpp", {"boss 1", "boss 99", "base 1", "base 99"}, "boss 1",
            "The function is chosen at run time, by the real object. Its default arguments are chosen at compile time, by the reference's type, Base."),
        snippet(R"cpp(
void say(bool) { std::cout << "bool"; }
void say(const std::string&) { std::cout << "string"; }

int main() {
    say("hello");
}
)cpp", {"bool", "string", no_compile, undefined_behavior}, "bool",
            "A string literal becomes a pointer, and a pointer converts to bool by a built-in conversion. That beats std::string's, which is user-defined."),
        snippet(R"cpp(
struct Node {
    std::shared_ptr<Node> next;
    ~Node() { std::cout << " freed"; }
};

int main() {
    auto a = std::make_shared<Node>();
    auto b = std::make_shared<Node>();
    a->next = b;
    b->next = a;
    std::cout << a.use_count();
}
)cpp", {"2", "2 freed freed", "1 freed freed", undefined_behavior}, "2",
            "a and b keep each other alive. When main ends each count only falls to 1, so neither Node is ever destroyed. std::weak_ptr breaks such a cycle."),
        snippet(R"cpp(
struct Gem {
    Gem() = default;
    Gem(const Gem&) { std::cout << "copy"; }
    Gem(Gem&&) noexcept { std::cout << "move"; }
};

int main() {
    const Gem a{};
    Gem b = std::move(a);
}
)cpp", {"copy", "move", no_compile, "Nothing"}, "copy",
            "std::move only casts. Casting a const object gives a const Gem&&, which can't bind to Gem&&, but can bind to const Gem&. So it silently copies."),
        undefined(R"cpp(
unsigned u = 0;
u = u - 1;
int i = INT_MAX;
i = i + 1;
std::cout << (u > 0) << " " << (i < 0);
)cpp", {"1 1", "0 1", "1 0", undefined_behavior},
            "u - 1 is fine: unsigned arithmetic wraps around. But signed overflow is undefined behavior, so INT_MAX + 1 voids the whole program.",
            "signed-integer-overflow"),
        undefined(R"cpp(
const std::string& pick(const std::string& s) {
    return s;
}

int main() {
    const std::string& r = pick(std::string(30, 'x') + "y");
    std::cout << r.back();
}
)cpp", {"y", "x", no_compile, undefined_behavior},
            "A temporary's life is extended only when it's bound directly to the reference. Here it dies at the end of the line, leaving r dangling.",
            "dangling-temporary"),
        undefined(R"cpp(
std::vector<int> v = {1, 2, 3};
for (int x : v) {
    if (x == 1)
        v.push_back(4);
    std::cout << x;
}
)cpp", {"123", "1234", "1", undefined_behavior},
            "push_back() can move the vector's items to new memory, and it always invalidates end(), so the loop's hidden iterators are left pointing at nothing.",
            "heap-use-after-free"),
        undefined(R"cpp(
struct Base {
    ~Base() { std::cout << "~Base "; }
};

struct Child : Base {
    std::string name = "child";
    ~Child() { std::cout << "~Child "; }
};

int main() {
    Base* p = new Child;
    delete p;
}
)cpp", {"~Base", "~Child ~Base", no_compile, undefined_behavior},
            "Deleting a Child through a Base pointer is undefined behavior unless Base's destructor is virtual. It often just prints ~Base and leaks, which is what makes it so dangerous.",
            "new-delete-type-mismatch"),
    };
    return boss;
}

}  // namespace templaria
