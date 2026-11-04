// The game's settings and wording. Pictures are shared with the Python game, in the site's
// static/img/adventure folder, apart from the Frozen Door's and the final boss's.

// Change GAME_VERSION when the questions change. A quest keeps the version it started on and is always
// replayed with that version's questions: the first QUESTION_COUNTS[version] of each level's list (new
// questions only ever go on the end).
export const GAME_VERSION = 1;
export const QUESTION_COUNTS = { 1: 20 };

// Base point values. Each one is multiplied by the difficulty multiplier.
export const CORRECT_ANSWER_POINTS = 10;
export const WISE_CHOICE_POINTS = 5;
export const RELIC_POINTS = 15;
export const TREASURE_POINTS = 50;
export const LIFE_POINTS = 10;
export const DRAGON_POINTS = 30;
export const BOSS_POINTS = 100;

export const DRAGON_MOVE = "dragon";
export const BOSS_MOVE = "boss";
export const BOSS_NAME = "The Pyramid of Doom";

export const LETTERS = ["a", "b", "c", "d"];

export const LEVELS = [
  { key: "easy", lives: 3, multiplier: 1, topics: "variables, types, strings, arrays, if/else, simple loops" },
  { key: "medium", lives: 2, multiplier: 2, topics: "functions, closures, scope, objects, array methods, == and ===" },
  { key: "hard", lives: 1, multiplier: 3, topics: "this, prototypes, classes, generators, promises, the event loop" },
];

export function level(key) {
  const found = LEVELS.find((candidate) => candidate.key === key);
  if (!found) throw new Error(`no such level: ${key}`);
  return found;
}

// The three ways into Scriptoria, in the order the first choice offers them.
export const PATHS = [
  {
    key: "forest",
    label: "Explore the Callback Forest",
    name: "the Callback Forest",
    sight: "the Callback Forest, where every path opens onto another path inside it",
    lair: "On your way back through the Callback Forest, a glint of gold catches your eye in a mossy hollow.",
  },
  {
    key: "cave",
    label: "Enter the Event Loop Caverns",
    name: "the Event Loop Caverns",
    sight: "the Event Loop Caverns, whose one long tunnel always comes back around",
    lair: "On your way back out of the Event Loop Caverns, a glint of gold catches your eye in a side cave.",
  },
  {
    key: "castle",
    label: "Climb to the Ruins of Castle Mocha",
    name: "the Ruins of Castle Mocha",
    sight: "the torch-lit trail that climbs to the ruins of Castle Mocha",
    lair:
      "On your way back through Castle Mocha, a glint of gold catches your eye through a doorway: " +
      "a forgotten treasury.",
  },
];

// Each scene: its banner, its picture, and a description of the picture for screen readers.
export const SCENES = {
  start: ["The Lost Promise of Scriptoria", "title.webp",
    "A moonlit jungle valley wrapped in mist, a golden temple glowing on a far hilltop"],
  forest: ["The Callback Forest", "forest.webp",
    "Sunbeams falling through towering trees onto a stream, ferns and one giant mossy tree"],
  waterfall: ["The Bubbling Falls", "waterfall.webp",
    "A roaring waterfall crashing into a green pool between mossy cliffs, a fallen log high across the gorge"],
  tree: ["The Prototype Tree", "tree.webp",
    "A great owl on a mossy branch above a sea of mist at sunrise, a golden temple glinting in the distance"],
  cave: ["The Event Loop Caverns", "cave.webp",
    "A dark cave mouth framed by carved stone serpents, a torch burning beside it"],
  dark: ["The Pit of undefined", "pit.webp",
    "A deep pit in the floor of a rocky tunnel, the cave entrance glowing far behind"],
  glyph: ["The Frozen Door", "glyph-door-javascript.webp",
    "A massive stone door glowing with lines of JavaScript code, fire bowls burning on either side"],
  castle: ["The Ruins of Castle Mocha", "castle.webp",
    "A ruined castle on a misty hilltop under a full moon, torches lighting the stone path that winds up to it"],
  gate: ["The Same-Origin Gate", "castle-gate.webp",
    "A great arched gate with a raised iron portcullis, griffin banners and blazing torches on ivy-covered walls"],
  hall: ["The Hall of Hoisting", "great-hall.webp",
    "A ruined great hall of broken gothic arches, torches flickering beside an empty throne at the top of worn steps"],
  ramparts: ["The Ramparts of Rejection", "ramparts.webp",
    "Torch-lit battlements under a full moon, stone towers rising above a misty valley"],
  gallery: ["The Moonlit Gallery", "gallery.webp",
    "A stone gallery high in a tower, ivy twisting around its pillars, the full moon over a misty valley beyond the balustrade"],
  temple: ["The Temple of the Golden Promise", "temple.webp",
    "A torch-lit temple hall leading to a golden vault door guarded by two stone serpents, a jeweled chest by the path"],
  victory: ["The Promise Is Kept!", "treasure.webp",
    "The Golden Promise: a glowing golden orb wrapped by a serpent, on a stone pedestal among gold and gems"],
  "dragon-emerald": ["The Emerald Dragon", "dragon-emerald.webp",
    "A green dragon asleep in a cave, curled around an open treasure chest full of gold and emeralds"],
  "dragon-ember": ["The Ember Dragon", "dragon-ember.webp",
    "A red dragon asleep in a fiery cave around a treasure chest of gold and rubies, a sword and a crown beside it"],
  "dragon-frost": ["The Frost Dragon", "dragon-frost.webp",
    "A blue dragon asleep in an ice cave, its treasure chest full of gold and glowing sapphires"],
  "dragon-pearl": ["The Pearl Dragon", "dragon-pearl.webp",
    "A white dragon asleep in a sunlit forest beside a treasure chest of gold, diamonds and a silver crown"],
  "dragon-amethyst": ["The Amethyst Dragon", "dragon-amethyst.webp",
    "A purple dragon coiled around a treasure chest of gold and glowing amethysts in a violet forest"],
  "dragon-autumn": ["The Autumn Dragon", "dragon-autumn.webp",
    "A copper dragon asleep among autumn leaves beside a treasure chest of gold and a golden goblet"],
  "dragon-gold": ["The Golden Dragon", "dragon-gold.webp",
    "A golden dragon asleep on a heap of gold coins beside a treasure chest in a torch-lit castle hall"],
  "dragon-silver": ["The Silver Dragon", "dragon-silver.webp",
    "A silver dragon asleep in a castle hall beside a chest of silver and diamonds, a knight's helmet and a sword"],
  "dragon-shadow": ["The Shadow Dragon", "dragon-shadow.webp",
    "A black dragon asleep in a castle hall around a chest of gold and rubies, a jeweled crown at its feet"],
  boss: [BOSS_NAME, "pyramid-of-doom.webp",
    "A colossal stepped pyramid of cracked black stone rising from a dark pool in a moonlit jungle, yellow light " +
      "bleeding through its seams, with one burning yellow eye at its peak, a fanged mouth below the eye and a cracked " +
      "yellow JS emblem below that. Its levels are carved in glowing yellow with getUser(id, function (err, user) {, " +
      "getMap(user, function (err, map) { and getPath(map, function (err, path) {, each closed with });. Two clawed " +
      "stone arms reach out, wound in glowing yellow chains that end in tags reading function () {, and parchment signs " +
      "hang around it reading undefined is not a function, [object Object], Uncaught (in promise), NaN === NaN // false " +
      "and typeof null === \"object\""],
  game_over: ["Uncaught TypeError", "game-over.webp",
    "A burnt-out torch and a lost compass on rocky ground under a blood-red sky"],
};

export const DRAGONS = [
  { level: "easy", path: "cave", scene: "dragon-emerald", scales: "green as moss" },
  { level: "medium", path: "cave", scene: "dragon-ember", scales: "glowing like hot coals" },
  { level: "hard", path: "cave", scene: "dragon-frost", scales: "glittering with ice" },
  { level: "easy", path: "forest", scene: "dragon-pearl", scales: "white as moonlight" },
  { level: "medium", path: "forest", scene: "dragon-amethyst", scales: "a deep, shimmering purple" },
  { level: "hard", path: "forest", scene: "dragon-autumn", scales: "the color of falling leaves" },
  { level: "easy", path: "castle", scene: "dragon-gold", scales: "as bright as the coins beneath it" },
  { level: "medium", path: "castle", scene: "dragon-silver", scales: "gleaming like polished armor" },
  { level: "hard", path: "castle", scene: "dragon-shadow", scales: "as black as a moonless night" },
];

export function findDragon(levelKey, path) {
  return DRAGONS.find((dragon) => dragon.level === levelKey && dragon.path === path) ?? null;
}

export const INTRO = [
  "Long ago, the coders of Scriptoria, lost in a forest of callbacks nested inside callbacks, forged their greatest " +
    "treasure: the Golden Promise, which would one day bring back everything they had ever asked for. Then they lost " +
    "track of it, as coders of Scriptoria will. It lies somewhere in this wild land, still pending. Its guardians " +
    "still test every traveler, with riddles in the language of the realm: JavaScript.",
  "One law holds throughout Scriptoria: every riddle is a script run just as it stands by Node.js, loose and " +
    "forgiving unless it says \"use strict\". When one prints several lines, the answers show them side by side. And " +
    "an error that nothing catches ends the script, so an answer may simply name it: TypeError, ReferenceError or " +
    "SyntaxError.",
  "Answer wisely and choose your path carefully. Every wrong answer costs you a life, and some choices lead to " +
    "certain doom...",
];

// The page's own words for this game, by the same keys as the Python game's (pythonia.TEXTS).
export const TEXTS = {
  title: "The Lost Promise of Scriptoria",
  language: "JavaScript",
  found: "Found the promise",
  master: "JavaScript Master",
  lost_to_boss: "Lost to the Pyramid of Doom",
  hall_note: "Walk every path on every level to face the Pyramid of Doom.",
  boss_offer_title: "The final challenge: the Pyramid of Doom",
  boss_offer:
    "You have walked every path on every level, and the Pyramid of Doom, the oldest curse in Scriptoria, has risen " +
    "to take back what you found. Answer its question, the hardest in all of Scriptoria, to earn the title of " +
    "JavaScript Master and {points} points.",
  boss_warning: "Beware: if you fail, all is lost. Your score falls to zero and you must start over.",
  boss_button: "Face the Pyramid of Doom",
  boss_confirm: "Face the Pyramid of Doom? If you fail, all is lost: your score falls to zero and you must start over.",
  boss_won: "You have flattened the Pyramid of Doom. You are a JavaScript Master!",
  boss_lost: "The Pyramid of Doom never called back. All is lost: your score is gone, and you must start over.",
  conquered_every_path: "Every path on every level: you've explored all of Scriptoria!",
  conquered_every_level: "Easy, Medium and Hard: you've conquered every level of Scriptoria!",
};
