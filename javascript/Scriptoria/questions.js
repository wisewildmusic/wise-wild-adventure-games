// All 78 questions. A snippet is a template literal tagged with String.raw (here `js`), a JavaScript way of
// writing text that runs over several lines and is full of quotes, with nothing to escape. Only a backtick or
// a ${ would need care, and the one riddle with those in it is written as an ordinary string.
//
// As the game's start page says, every riddle is a script run just as it stands by Node.js, in sloppy mode
// unless it says "use strict". tools/check-js-questions.py runs every one and checks each answer against what
// really happens. An answer naming an error means the script dies of that error, uncaught, printing nothing.
const js = String.raw;

const PRINTS = "What does this code print?";

/** A template literal starts and ends on lines of its own, so that it can be read in the source: those two
    line ends aren't part of the snippet. */
function tidy(source) {
  return source.replace(/\r/g, "").replace(/^\n/, "").replace(/\n$/, "");
}

function snippet(source, options, answer, explain) {
  return { prompt: PRINTS, code: tidy(source), options, answer, explain };
}

function ask(prompt, options, answer, explain) {
  return { prompt, code: null, options, answer, explain };
}

export const levelQuestions = {
  easy: [
    snippet(js`
let x = 5;
x = x + 2;
console.log(x);
`, ["5", "7", "52", "x + 2"], "7",
      "x starts at 5, then x + 2 (which is 7) is stored back into x."),
    ask("Which of these is a valid JavaScript variable name?",
      ["2ndPlace", "my-score", "$player_name", "class"], "$player_name",
      "Names can't start with a digit, can't contain '-', and can't be a reserved word such as 'class'. They can contain $ and _, though."),
    snippet(js`
const fruits = ["apple", "banana", "cherry"];
console.log(fruits[1]);
`, ["apple", "banana", "cherry", "undefined"], "banana",
      "Array indexes start at 0, so index 1 is the second item."),
    snippet(js`
console.log(typeof 42);
`, ["number", "integer", "int", "string"], "number",
      "JavaScript has one everyday type for numbers: whole numbers and decimals alike are all 'number'."),
    snippet(js`
const word = "cat";
word[0] = "b";
console.log(word);
`, ["bat", "cat", "bcat", "TypeError"], "cat",
      "Strings can't be changed in place. In sloppy mode the assignment is quietly ignored; in strict mode it would be a TypeError."),
    snippet(js`
for (let i = 0; i < 3; i++) {
  console.log(i);
}
`, ["0 1 2", "1 2 3", "0 1 2 3", "1 2"], "0 1 2",
      "i starts at 0 and the loop stops as soon as i < 3 is false."),
    snippet(js`
function greet(name) {
  return "Hi " + name;
}
console.log(greet("Ada"));
`, ["Hi Ada", "Hi name", "greet Ada", "undefined"], "Hi Ada",
      "The argument \"Ada\" is passed into the name parameter and joined onto \"Hi \"."),
    ask("Which keyword declares a variable that can never be assigned a new value?",
      ["var", "let", "const", "static"], "const",
      "A const always refers to the same value. If that value is an object or an array, its contents can still change."),
    snippet(js`
const items = [1, 2, 3];
items.push(4);
console.log(items.length);
`, ["3", "4", "5", "TypeError"], "4",
      "const only stops items being assigned a new array. The array itself can still change, and push() puts one item on the end."),
    snippet(js`
console.log(7 > 3 && 2 > 5);
`, ["true", "false", "0", "1"], "false",
      "&& is only true when both sides are, and 2 > 5 isn't."),
    snippet('const name = "Ada";\nconsole.log(`Hi ${name}!`);',
      ["Hi Ada!", "Hi ${name}!", "Hi name!", "SyntaxError"], "Hi Ada!",
      "Inside backticks, ${...} is replaced by its value. Inside ordinary quotes, it would just be those characters."),
    snippet(js`
console.log(10 / 4);
`, ["2", "2.5", "3", "2 remainder 2"], "2.5",
      "There's no separate whole-number division: / always gives the full result. Math.floor(10 / 4) would give 2."),
    snippet(js`
console.log(17 % 5);
`, ["3", "2", "3.4", "12"], "2",
      "% gives the remainder of a division: 17 is 3 fives (15) with 2 left over."),
    snippet(js`
const name = "Castle";
console.log(name.length);
`, ["5", "6", "7", "undefined"], "6",
      "length counts the characters: C-a-s-t-l-e is 6. It's a property, not a method, so it has no parentheses."),
    snippet(js`
console.log("5" + 3);
`, ["8", "53", "5 3", "TypeError"], "53",
      "If either side of + is a string, + joins rather than adds, so 3 is turned into \"3\"."),
    snippet(js`
const x = 3;
if (x > 5) {
  console.log("big");
} else if (x > 2) {
  console.log("medium");
} else {
  console.log("small");
}
`, ["big", "medium", "small", "medium small"], "medium",
      "x > 5 is false, so JavaScript checks the else if: 3 > 2 is true, and the last else is skipped."),
    snippet(js`
let total = 0;
for (const n of [2, 4, 6]) {
  total += n;
}
console.log(total);
`, ["6", "12", "246", "0"], "12",
      "for...of hands over each item in turn, and each is added to total: 2 + 4 + 6 = 12."),
    snippet(js`
const lives = 3;
lives = 2;
console.log(lives);
`, ["3", "2", "TypeError", "SyntaxError"], "TypeError",
      "Assigning to a const is allowed to parse, but it fails when it runs: TypeError: Assignment to constant variable."),
    snippet(js`
let x;
console.log(x);
`, ["0", "null", "undefined", "ReferenceError"], "undefined",
      "A variable that has been declared but not given a value holds undefined."),
    snippet(js`
const nums = [1, 2, 3];
console.log(nums[3]);
`, ["3", "undefined", "null", "RangeError"], "undefined",
      "Reading past the end of an array isn't an error. There's nothing there, so you simply get undefined."),
  ],
  medium: [
    snippet(js`
console.log(1 == "1", 1 === "1");
`, ["true true", "true false", "false true", "false false"], "true false",
      "== converts its two sides to the same type before comparing. === doesn't: a number and a string are never the same."),
    snippet(js`
const word = "scriptoria";
console.log(word.slice(1, 4));
`, ["scr", "cri", "crip", "ript"], "cri",
      "slice(1, 4) starts at index 1 and stops just before index 4. The second number is where to stop, not how many to take."),
    snippet(js`
const scores = { ana: 90 };
console.log(scores.cal, Object.keys(scores).length);
`, ["undefined 1", "undefined 2", "null 1", "TypeError"], "undefined 1",
      "Reading a missing property isn't an error, and it doesn't add the property. You just get undefined."),
    snippet(js`
const n = 1;
switch (n) {
  case 1: console.log("one");
  case 2: console.log("two");
  case 3: console.log("three"); break;
  default: console.log("other");
}
`, ["one", "one two", "one two three", "one two three other"], "one two three",
      "A case without a break falls through into the next one. The break after three stops it."),
    snippet(js`
const nums = [10, 9, 1];
nums.sort();
console.log(nums.join(" "));
`, ["1 9 10", "10 9 1", "1 10 9", "9 10 1"], "1 10 9",
      "With nothing to compare by, sort() compares items as strings, and \"10\" comes before \"9\". sort((a, b) => a - b) sorts them as numbers."),
    snippet(js`
function power(number, exponent = 2) {
  return number ** exponent;
}
console.log(power(3));
`, ["6", "9", "27", "NaN"], "9",
      "exponent wasn't passed, so it takes its default of 2, and ** raises 3 to that power."),
    snippet(js`
const nums = [1, 2, 3];
const doubled = nums.map(n => n * 2);
console.log(nums[0], doubled[0]);
`, ["1 2", "2 2", "1 1", "2 1"], "1 2",
      "map() builds a new array from what the function returns, and leaves the original alone."),
    snippet(js`
function change(value) {
  value = 5;
}
let x = 10;
change(x);
console.log(x);
`, ["5", "10", "undefined", "0"], "10",
      "value is a parameter of its own that starts with a copy of x. Assigning to it doesn't touch x."),
    snippet(js`
function rename(player) {
  player.name = "Grace";
}
const hero = { name: "Ada" };
rename(hero);
console.log(hero.name);
`, ["Ada", "Grace", "undefined", "TypeError"], "Grace",
      "player and hero are two names for one object, so a change made through either one shows through both."),
    snippet(js`
function makeCounter() {
  let count = 0;
  return () => ++count;
}
const next = makeCounter();
next();
console.log(next());
`, ["0", "1", "2", "undefined"], "2",
      "The arrow function is a closure: it keeps count alive after makeCounter() has returned, and each call adds to the same one."),
    snippet(js`
const total = [1, 2, 3, 4]
  .filter(n => n % 2 === 0)
  .reduce((sum, n) => sum + n, 0);
console.log(total);
`, ["4", "6", "10", "0"], "6",
      "filter() keeps the even numbers, 2 and 4, and reduce() adds them up, starting from 0."),
    snippet(js`
console.log(typeof null, typeof undefined);
`, ["null undefined", "object undefined", "undefined undefined", "object object"], "object undefined",
      "typeof null being \"object\" is a bug from JavaScript's first days. So much code came to rely on it that it can never be fixed."),
    snippet(js`
console.log(x);
var x = 5;
`, ["5", "undefined", "null", "ReferenceError"], "undefined",
      "A var's declaration is hoisted to the top of its function or script, but its value isn't assigned until that line runs."),
    snippet(js`
console.log(x);
let x = 5;
`, ["5", "undefined", "null", "ReferenceError"], "ReferenceError",
      "A let is hoisted too, but using it before its line is an error. The stretch before it is called the temporal dead zone."),
    snippet(js`
const values = [0, "", "0", null, [], NaN];
console.log(values.filter(Boolean).length);
`, ["1", "2", "3", "4"], "2",
      "0, \"\", null and NaN are falsy. A non-empty string is truthy, even \"0\", and so is every array, even an empty one."),
    snippet(js`
const lives = 0;
console.log(lives || 3, lives ?? 3);
`, ["0 0", "3 0", "0 3", "3 3"], "3 0",
      "|| falls back on anything falsy, including 0. ?? falls back only on null and undefined, so 0 stays."),
    snippet(js`
const [first, , third = 9, fourth = 8] = [1, 2, undefined, null];
console.log(first, third, fourth);
`, ["1 9 null", "1 undefined null", "1 9 8", "1 2 null"], "1 9 null",
      "The empty slot skips the 2. A default is used only for undefined, so third gets 9, while null is a value and fourth keeps it."),
    snippet(js`
const a = { x: 1, inner: { y: 2 } };
const b = { ...a };
b.x = 10;
b.inner.y = 20;
console.log(a.x, a.inner.y);
`, ["1 2", "1 20", "10 2", "10 20"], "1 20",
      "Spread makes a shallow copy. b gets its own x, but a.inner and b.inner are one and the same object."),
    snippet(js`
const hero = { pet: null };
console.log(hero.pet?.name, hero.pet.name);
`, ["null null", "undefined null", "undefined undefined", "TypeError"], "TypeError",
      "?. stops safely at null and gives undefined, but the second has no ?., and reading a property of null throws before console.log is ever called."),
    snippet(js`
console.log(parseInt("42px"), Number("42px"));
`, ["42 42", "42 NaN", "NaN NaN", "NaN 42"], "42 NaN",
      "parseInt() reads as far as it can and ignores the rest. Number() takes the whole string or nothing, and gives NaN."),
  ],
  hard: [
    snippet(js`
const owl = {
  name: "Athena",
  hoot() { return this.name; },
};
const hoot = owl.hoot;
console.log(owl.hoot(), hoot());
`, ["Athena Athena", "Athena undefined", "undefined undefined", "TypeError"], "Athena undefined",
      "this is decided by how a function is called. hoot() is called on nothing, so in sloppy mode this is the global object, which has no name."),
    snippet(js`
class Owl {
  name = "Athena";
  arrow = () => this.name;
  regular() { return this?.name; }
}
const { arrow, regular } = new Owl();
console.log(arrow(), regular());
`, ["Athena Athena", "Athena undefined", "undefined Athena", "TypeError"], "Athena undefined",
      "An arrow function keeps the this of where it was made. A method pulled off its object loses its this, and code in a class is always strict, so it's undefined."),
    snippet(js`
const base = { legs: 4 };
const cat = Object.create(base);
cat.sound = "meow";
console.log(cat.legs, Object.keys(cat).length, "legs" in cat);
`, ["4 1 true", "4 2 true", "undefined 1 false", "4 1 false"], "4 1 true",
      "legs is found by following the prototype chain, and in follows the chain too. Object.keys() lists only an object's own properties."),
    snippet(js`
const base = { count: 1, list: [] };
const a = Object.create(base);
a.count++;
a.list.push("x");
console.log(base.count, base.list.length);
`, ["1 0", "1 1", "2 1", "2 0"], "1 1",
      "a.count++ reads 1 from the prototype, then writes a new count on a itself. a.list.push() writes nothing on a: it changes the one array they share."),
    snippet(js`
class Animal {
  sound = "...";
  constructor() { console.log(this.sound); }
}
class Dog extends Animal {
  sound = "Woof";
}
new Dog();
`, ["...", "Woof", "undefined", "TypeError"], "...",
      "A class's fields are set just after its super() returns. While Animal's constructor runs, Dog's sound isn't there yet."),
    snippet(js`
class Animal {}
class Dog extends Animal {
  constructor() {
    this.legs = 4;
    super();
  }
}
new Dog();
console.log("woof");
`, ["woof", "TypeError", "ReferenceError", "SyntaxError"], "ReferenceError",
      "A derived class has no this until super() returns. Touching it any sooner is a ReferenceError when the constructor runs."),
    snippet(js`
class Vault {
  #gold = 10;
  peek() { return this.#gold; }
}
const v = new Vault();
console.log(v.gold, v.peek());
`, ["10 10", "undefined 10", "undefined undefined", "SyntaxError"], "undefined 10",
      "#gold is truly private, and the # is part of its name. v.gold is just some other property, one that doesn't exist."),
    ask("Which are the three states a Promise can be in?",
      ["pending, fulfilled, rejected", "waiting, running, done", "open, closed, broken", "new, resolved, finished"],
      "pending, fulfilled, rejected",
      "A Promise starts out pending, and settles only once, as fulfilled or rejected. After that it never changes."),
    snippet(js`
function* count() {
  yield 1;
  yield 2;
  return 3;
}
console.log([...count()].join(" "));
`, ["1 2", "1 2 3", "3", "1"], "1 2",
      "Spread and for...of take what a generator yields, and stop when it's done. The value it returns is left out."),
    snippet(js`
function* talk() {
  const a = yield "first";
  const b = yield a + "!";
  return b;
}
const g = talk();
g.next("ignored");
console.log(g.next("hi").value, g.next("bye").value);
`, ["first hi!", "hi! bye", "hi bye", "undefined hi!"], "hi! bye",
      "What you pass to next() becomes the value of the yield the generator is stopped at. The first next() has no yield to answer, so its value is lost. This game itself runs on that."),
    snippet(js`
const fns = [];
for (var i = 0; i < 3; i++) {
  fns.push(() => i);
}
console.log(fns[0](), fns[2]());
`, ["0 2", "3 3", "2 2", "0 0"], "3 3",
      "There's only one var i, and every arrow function closes over it. By the time they're called, the loop has left it at 3. With let, each pass gets its own i."),
    snippet(js`
setTimeout(() => console.log("timeout"), 0);
Promise.resolve().then(() => console.log("promise"));
console.log("sync");
`, ["sync promise timeout", "sync timeout promise", "timeout promise sync", "promise sync timeout"], "sync promise timeout",
      "The script finishes first. Then the microtask queue, where promises wait, is emptied before the event loop takes its next task, the timer."),
    snippet(js`
async function getLives() {
  return 3;
}
console.log(typeof getLives(), typeof getLives().then);
`, ["number undefined", "object function", "function function", "object undefined"], "object function",
      "An async function always returns a Promise, which is an object with a then() method. The 3 comes out only through then() or await."),
    snippet(js`
async function quest() {
  console.log("a");
  await null;
  console.log("b");
}
quest();
console.log("c");
`, ["a b c", "a c b", "c a b", "c b a"], "a c b",
      "An async function runs at once, right up to its first await. There it hands back control, and the rest waits in the microtask queue."),
    snippet(js`
Promise.reject(new Error("no"))
  .then(() => console.log("then"))
  .catch(() => console.log("catch"))
  .then(() => console.log("after"));
`, ["then after", "catch", "catch after", "then catch after"], "catch after",
      "A rejection skips each then() until a catch() handles it. The catch() returns normally, so its promise is fulfilled, and the chain carries on."),
    snippet(js`
Promise.all([Promise.resolve(1), Promise.reject("no"), Promise.resolve(3)])
  .then(values => console.log("ok", values.length))
  .catch(reason => console.log("failed", reason));
`, ["ok 3", "ok 2", "failed no", "failed 3"], "failed no",
      "Promise.all() rejects as soon as any one of its promises does, with that reason. Promise.allSettled() would wait for all three."),
    snippet(js`
function f() {
  try {
    return "try";
  } finally {
    console.log("finally");
  }
}
console.log(f());
`, ["try", "finally", "try finally", "finally try"], "finally try",
      "return works out its value, then finally runs before the function really hands it back, and so before the outer console.log gets it."),
    snippet(js`
const m = new Map();
m.set(1, "number");
m.set("1", "string");
const o = {};
o[1] = "number";
o["1"] = "string";
console.log(m.size, Object.keys(o).length);
`, ["1 1", "2 2", "2 1", "1 2"], "2 1",
      "A Map keeps its keys as they are, so 1 and \"1\" are two keys. An object's keys are strings (or symbols), so o[1] and o[\"1\"] are one."),
    snippet(js`
function who() { return this.name; }
const bound = who.bind({ name: "first" });
console.log(bound.call({ name: "second" }));
`, ["first", "second", "undefined", "TypeError"], "first",
      "bind() makes a new function whose this is fixed for good. Even call() can't change it."),
    snippet(js`
const hero = { name: "Ada", secret: undefined, level: NaN, save() {} };
console.log(JSON.stringify(hero));
`, ['{"name":"Ada","level":null}', '{"name":"Ada","secret":null,"level":null}', '{"name":"Ada","level":NaN}', '{"name":"Ada"}'],
      '{"name":"Ada","level":null}',
      "JSON has no undefined or functions, so properties holding those are left out. It has no NaN either, and that one becomes null."),
  ],
};

const DRAGON_QUESTIONS = {
  "easy cave": snippet(js`
console.log(typeof NaN, typeof []);
`, ["NaN array", "number object", "number array", "undefined object"], "number object",
    "NaN means Not a Number, yet its type is number. An array is a kind of object: Array.isArray() is how to tell them apart."),
  "medium cave": snippet(js`
console.log([NaN].includes(NaN), [NaN].indexOf(NaN));
`, ["true 0", "true -1", "false -1", "false 0"], "true -1",
    "NaN is the one value not equal to itself. indexOf() uses ===, so it never finds it. includes() was made later, to a rule that treats NaN as NaN."),
  "hard cave": snippet(js`
Promise.resolve().then(() => {
  console.log("a");
  setTimeout(() => console.log("b"));
  Promise.resolve().then(() => console.log("c"));
});
setTimeout(() => console.log("d"));
`, ["a b c d", "a c d b", "d a c b", "a c b d"], "a c d b",
    "Microtasks run until there are none left, even ones added along the way, so c follows a. Only then come the timers, in the order they were set."),
  "easy forest": snippet(js`
console.log("5" * "2", "5" + "2", "5" - 2);
`, ["10 52 3", "52 52 52", "10 10 3", "NaN 52 NaN"], "10 52 3",
    "* and - only work on numbers, so they turn strings into numbers. + also joins strings, and if either side is a string, that's what it does."),
  "medium forest": snippet(js`
function outer() {
  let x = 1;
  function inner() {
    x++;
    return x;
  }
  x = 10;
  return inner;
}
console.log(outer()());
`, ["2", "11", "10", "undefined"], "11",
    "A closure holds on to the variable itself, not a copy of its value when the function was made. By the time inner() runs, x is 10."),
  "hard forest": snippet(js`
class Tree {
  static count = 0;
  constructor() { Tree.count++; }
}
class Oak extends Tree {}
new Oak();
new Oak();
console.log(Oak.count, Object.hasOwn(Oak, "count"));
`, ["2 false", "2 true", "0 false", "undefined false"], "2 false",
    "A class's prototype is the class it extends, so Oak finds the static count on Tree. There's only the one, and Oak has none of its own."),
  "easy castle": snippet(js`
const a = [1, 2];
const b = [1, 2];
console.log(a == b, a[0] === b[0]);
`, ["false true", "true true", "true false", "false false"], "false true",
    "Objects and arrays compare by identity, not contents. a and b look alike, but they're two arrays. Their first items are both plain 1s."),
  "medium castle": snippet(js`
const nums = ["1", "2", "3"].map(parseInt);
console.log(nums.join(" "));
`, ["1 2 3", "1 NaN NaN", "NaN NaN NaN", "1 2 NaN"], "1 NaN NaN",
    "map() passes each item and its index, and parseInt() takes that index as a number base: base 0 means the default, base 1 is invalid, and 3 isn't a digit in base 2."),
  "hard castle": snippet(js`
"use strict";
const door = Object.freeze({ key: "old", locks: [] });
door.locks.push("new");
try {
  door.key = "new";
} catch (error) {
  console.log(error.name);
}
console.log(door.key, door.locks.length);
`, ["TypeError old 1", "TypeError old 0", "new 1", "old 1"], "TypeError old 1",
    "Strict mode turns writing to a frozen object into a TypeError. But freezing is shallow: door.locks can't be replaced, yet the array in it can still change."),
};

export function dragonQuestion(level, path) {
  return DRAGON_QUESTIONS[`${level} ${path}`];
}

// The final boss's nine: the hardest questions in the game, on JavaScript's darkest corners.
export const bossQuestions = [
  snippet(js`
console.log([] == ![], [] + [] === "", typeof ([] + {}));
`, ["true true string", "false true string", "false false object", "true false object"], "true true string",
    "![] is false, because every array is truthy. Then == turns [] into \"\" and both sides into 0, so an array equals its own opposite. + turns both sides into strings."),
  snippet(js`
async function a() {
  console.log(1);
  await b();
  console.log(2);
}
async function b() {
  console.log(3);
}
a();
Promise.resolve().then(() => console.log(4));
console.log(5);
`, ["1 3 5 2 4", "1 3 2 5 4", "1 3 5 4 2", "1 5 3 2 4"], "1 3 5 2 4",
    "b() runs at once, inside a(). The await on it then goes into the microtask queue ahead of the then() below it, and both wait for the script to finish."),
  snippet(js`
async function slow() {
  return Promise.resolve("x");
}
slow().then(() => console.log("slow"));
Promise.resolve()
  .then(() => console.log("one"))
  .then(() => console.log("two"))
  .then(() => console.log("three"));
`, ["slow one two three", "one slow two three", "one two slow three", "one two three slow"], "one two slow three",
    "An async function that returns a promise has to wait for it, which takes three trips through the microtask queue. return await would take fewer."),
  snippet(js`
function f() {
  return
  {
    ok: true
  };
}
console.log(f());
`, ["{ ok: true }", "undefined", "true", "SyntaxError"], "undefined",
    "A line break right after return ends the statement: JavaScript inserts a semicolon for you. The object below it is never reached, and parses as a block with a label."),
  snippet(js`
const o = { b: 1, 2: 1, a: 1, 1: 1 };
console.log(Object.keys(o).join(""));
`, ["b2a1", "12ba", "ab12", "12ab"], "12ba",
    "Keys that look like array indexes come first, in rising order. All the others follow in the order they were added."),
  snippet(js`
const a = [1, , 3];
let seen = 0;
a.forEach(() => seen++);
console.log(a.length, seen, 1 in a);
`, ["3 2 false", "3 3 true", "2 2 false", "3 3 false"], "3 2 false",
    "The extra comma leaves a hole. It still counts toward length, but there's no item at index 1, not even an undefined, and forEach() skips right over it."),
  snippet(js`
function* g() {
  try {
    yield 1;
    yield 2;
  } finally {
    yield "cleanup";
  }
}
const it = g();
it.next();
console.log(it.return("done").value, it.next().value, it.next().done);
`, ["cleanup done true", "done undefined true", "done cleanup true", "cleanup undefined true"], "cleanup done true",
    "return() acts as if a return were at the yield, so finally runs, and a yield in there stops it again. The next next() finishes it, and only then does \"done\" come out."),
  snippet(js`
const weird = {
  valueOf() { return 42; },
  toString() { return "str"; },
};
console.log(weird + "", String(weird), weird * 2);
`, ["42 str 84", "str str 84", "42 42 84", "str 42 NaN"], "42 str 84",
    "+ asks for a primitive with no preference, which tries valueOf() first. String() prefers toString(), and * wants a number."),
  snippet(js`
console.log(null == 0, null >= 0, undefined == 0, undefined >= 0);
`, ["false true false false", "true true false false", "false false false false", "false true true true"], "false true false false",
    "== has its own rule: null equals only undefined. >= turns its sides into numbers: null becomes 0, so 0 >= 0 is true, and undefined becomes NaN, which compares false with everything."),
];
