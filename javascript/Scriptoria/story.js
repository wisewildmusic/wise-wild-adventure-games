// The adventure itself. Each part of the story is a generator function. `yield` hands the page a prompt and
// stops right there, and the value of the yield is the explorer's move, when it comes. `yield*` walks through
// a smaller part of the story, and its value is what that part returned: askQuestion() and faceChallenge()
// return whether the explorer got through.
import { shuffle } from "./random.js";
import { bossQuestions, dragonQuestion, levelQuestions } from "./questions.js";
import * as rules from "./rules.js";

// ------------------------------------------------------------------
// Helpers
// ------------------------------------------------------------------

function choose(...options) {
  return { kind: "choice", options };
}

function addPoints(q, basePoints, reason) {
  const points = basePoints * rules.level(q.difficulty).multiplier;
  q.score += points;
  q.note("points", `+${points} points (${reason})`);
}

/** Takes away one life. Returns true if the explorer still has lives left. */
function loseLife(q) {
  q.lives--;
  q.note("life", q.lives > 0 ? `You lose a life! Lives remaining: ${q.lives}` : "You have no lives left!");
  return q.lives > 0;
}

function collectRelic(q, relic) {
  q.inventory.push(relic);
  q.note("relic", `You found a relic: ${relic}!`);
}

/** The next question from the explorer's deck, reshuffling when it runs out. A path not taken yet starts
    with a deck of the questions the level's earlier paths didn't ask. A quest asks at most 6, so a level's
    20 questions are enough for all three paths. */
function drawQuestion(q) {
  if (q.deck.length === 0) {
    const every = Array.from({ length: rules.QUESTION_COUNTS[q.version] }, (_, number) => number);
    const unasked = q.asked.length === 0 ? every.filter((number) => !q.skipQuestions.has(number)) : [];
    q.deck = shuffle(q.rng, unasked.length > 0 ? unasked : every);
  }
  const number = q.deck.pop();
  q.asked.push(number);
  return levelQuestions[q.difficulty][number];
}

/** Asks one JavaScript question: the next from the deck, or `given` (a dragon's or the boss's). Returns true
    if the answer is right, and earns `points`. */
function* askQuestion(q, challenger, given = null, points = rules.CORRECT_ANSWER_POINTS, reason = "correct answer") {
  const question = given ?? drawQuestion(q);
  const options = shuffle(q.rng, [...question.options]);

  const move = yield { kind: "question", challenger, question, options };

  const correctLetter = rules.LETTERS[options.indexOf(question.answer)];
  const passed = move === correctLetter;
  if (passed) {
    q.note("correct", "Correct!");
    addPoints(q, points, reason);
  } else {
    q.note("wrong", `${correctLetter}) ${question.answer}`);
  }
  q.note("why", question.explain);
  return passed;
}

/** Asks questions until one is answered correctly. Each wrong answer costs a life. Returns false if the
    explorer runs out of lives. */
function* faceChallenge(q, challenger) {
  while (true) {
    if (yield* askQuestion(q, challenger)) return true;
    if (!loseLife(q)) return false;
    q.note("info", `${challenger} gives you another chance...`);
  }
}

function gameOver(q, message) {
  q.narrate(message);
  q.banner("game_over");
  q.result = "lose";
}

function victory(q) {
  q.banner("victory");
  q.narrate(
    "The vault door swings open with a groan. Inside, resting on a pedestal of black stone, sits the legendary " +
      "Golden Promise, a glowing orb in a serpent's coils, pending since the day it was made. It resolves at your " +
      `touch. Congratulations, ${q.name}! Your name will be carved among the great coders of Scriptoria.`,
  );
  addPoints(q, rules.TREASURE_POINTS, "found the promise");
  for (const relic of q.inventory) addPoints(q, rules.RELIC_POINTS, `relic: ${relic}`);
  addPoints(q, rules.LIFE_POINTS * q.lives, `lives remaining: ${q.lives}`);
  q.result = "win";
}

// ------------------------------------------------------------------
// The temple and the end of the quest
// ------------------------------------------------------------------

function* templeVault(q) {
  q.banner("temple");
  q.narrate(
    "Torches burst into flame as you enter the temple's great hall. At the far end stands the vault, held shut by " +
      "two locks, Resolve and Reject, each in the coils of a stone serpent: trophies, they say, taken from a rival " +
      "language that never did get into the browser. Beside the path sits a small jeweled chest with a riddle carved " +
      "into its lid. Solving it would earn you a rare relic, but a wrong answer will cost you a life.",
  );
  const move = yield choose("Try to open the jeweled chest", "Ignore the chest and head for the vault");
  if (move === "1") {
    if (yield* askQuestion(q, "The Jeweled Chest")) {
      q.narrate("Click! The lid springs open, revealing a ring set with a blazing citrine, as yellow as the realm's own banner.");
      collectRelic(q, "Citrine Ring");
    } else {
      if (!loseLife(q)) {
        gameOver(q, "A dart coated in sleeping venom shoots from the lock. You doze off just steps away from the promise, pending forever...");
        return;
      }
      q.narrate("A tiny dart shoots from the lock and stings your hand. The chest stays shut.");
    }
  } else {
    q.narrate("You leave the chest alone. Not everything that looks callable should be called.");
  }

  q.narrate("You approach the vault door. The eyes of the stone serpents begin to glow.");
  for (const lock of ["Resolve", "Reject"]) {
    if (!(yield* faceChallenge(q, `The ${lock} Lock`))) {
      gameOver(q, `${lock} failed. The serpent's eyes flash red and the vault seals itself forever. The promise remains lost.`);
      return;
    }
    q.note("info", `The ${lock} Lock slides open!`);
  }
  victory(q);
}

// ------------------------------------------------------------------
// The forest
// ------------------------------------------------------------------

function* streamRoute(q) {
  q.banner("waterfall");
  q.narrate(
    "You follow the stream until it plunges over a cliff in a roaring waterfall, the Bubbling Falls, where everything " +
      "that happens down below rises back up through every level above it, unless someone stops it. The water swirls, " +
      "rises, and takes the shape of a towering figure: the Bubbling Spirit. \"None may pass until they have been " +
      "handled,\" it booms.",
  );
  if (!(yield* faceChallenge(q, "The Bubbling Spirit"))) {
    gameOver(q, "\"Unhandled,\" says the Bubbling Spirit. A great wave sweeps you downstream, far away from the promise.");
    return;
  }

  q.narrate("The Bubbling Spirit bows and places a shimmering pearl in your hand.");
  collectRelic(q, "Bubble Pearl");
  q.narrate(
    "It points a watery finger at a dark gap hidden behind the falls. Nearby, a fallen log covered in slick green moss " +
      "stretches across the gorge. It looks like a quicker way across, and nothing on it checks what you're doing until " +
      "it's far too late.",
  );
  const move = yield choose("Slip behind the falls, as the Bubbling Spirit showed you", "Cross the gorge on the mossy log");
  if (move === "1") {
    addPoints(q, rules.WISE_CHOICE_POINTS, "wise choice");
    q.narrate("Behind the curtain of water, a hidden tunnel leads you straight to the steps of an ancient temple.");
    yield* templeVault(q);
    return;
  }
  gameOver(q, "Halfway across, your boot slips on the moss. No error, no warning: you just tumble into the rapids and are carried far from the promise. Somewhere behind you, the Bubbling Spirit sighs.");
}

function* treeRoute(q) {
  q.banner("tree");
  q.narrate(
    "You climb branch by branch, each one inherited from the branch below, looking up the chain until you break " +
      "through the mist at the very top, where the chain ends in null. Far to the east, a golden temple roof glints " +
      "above the jungle. A great grey owl lands beside you and blinks. \"Hoo! I am the Owl of this, and who I am depends " +
      "entirely on who's calling. Only those who think like a programmer may learn the safe way down.\"",
  );
  if (!(yield* faceChallenge(q, "The Owl of this"))) {
    gameOver(q, "The owl ruffles its feathers and flies away, and this is suddenly undefined. As you reach after it, the branch beneath you snaps...");
    return;
  }

  q.narrate("\"Well reasoned!\" hoots the owl, and it plucks a feather for you.");
  collectRelic(q, "Bound Feather");
  q.narrate(
    "\"Now listen closely. The swamp below is the shortest way to the temple, but like ==, it asks no questions, treats " +
      "anything as anything, and swallows the careless. The vines are slower, but strict.\"",
  );
  const move = yield choose("Swing along the vines toward the temple", "Climb down and take the swamp shortcut");
  if (move === "1") {
    addPoints(q, rules.WISE_CHOICE_POINTS, "wise choice");
    q.narrate("Vine by vine, you swing through the canopy like a jungle acrobat and land softly on the temple steps.");
    yield* templeVault(q);
    return;
  }
  gameOver(q, "Three steps into the swamp, the mud grabs your boots. It looked like solid ground. It looked equal to solid ground. You should have listened to the owl!");
}

function* forestPath(q) {
  q.banner("forest");
  q.narrate(
    "Towering trees close in around you, and every path through them opens onto another path inside it, and another " +
      "inside that, each one waiting to be called back. Strings of old code hang from the branches, indented further " +
      "and further to the right. To your left, a stream murmurs through the ferns, its surface alive with bubbles that " +
      "rise and rise. To your right stands the Prototype Tree, so tall its top disappears into the mist, every branch " +
      "inherited from the one below it. From up there, you could see for miles.",
  );
  const move = yield choose("Follow the stream", "Climb the Prototype Tree");
  yield* move === "1" ? streamRoute(q) : treeRoute(q);
}

// ------------------------------------------------------------------
// The caverns
// ------------------------------------------------------------------

function* frozenDoor(q) {
  q.banner("glyph");
  q.narrate(
    "You weave between the pits until the tunnel ends at a massive stone door, frozen shut: no one may add to it, change " +
      "it or take anything away. Glowing letters crawl across its surface and rearrange themselves into lines of JavaScript.",
  );
  if (!(yield* faceChallenge(q, "The Frozen Door"))) {
    gameOver(q, "The letters flash red. With a deep rumble the tunnel behind you seals shut, and your torch flickers out...");
    return;
  }

  q.narrate("The letters flash gold and the door grinds open. A small carved tablet falls from the wall at your feet.");
  collectRelic(q, "Frozen Tablet");
  q.narrate(
    "Beyond the door the tunnel splits in two. From the left drifts warm air and a faint golden glow. The right tunnel " +
      "is cold, its walls marked with fresh, deep claw scratches, and something in there is growling.",
  );
  const move = yield choose("Take the left tunnel toward the golden glow", "Take the right tunnel past the claw marks");
  if (move === "1") {
    addPoints(q, rules.WISE_CHOICE_POINTS, "wise choice");
    q.narrate("The golden glow grows brighter with every step until you emerge at the heart of an ancient temple.");
    yield* templeVault(q);
    return;
  }
  gameOver(q, "The claw marks belong to a very large, very grumpy cave bear, and nothing here is going to catch you. You flee all the way back to the entrance, your quest in ruins.");
}

function* pitOfUndefined(q) {
  q.banner("dark");
  q.narrate(
    "You creep forward in total darkness, one hand on the cold, damp wall, reaching for a next step you never checked " +
      "was there. There is nothing there at all. You tumble into a pit!",
  );
  if (!loseLife(q)) {
    gameOver(q, "TypeError: Cannot read properties of undefined. The pit is far too deep to climb out of without light. Your quest ends here, in the dark.");
    return;
  }

  yield choose("Climb out of the pit");
  q.narrate(
    "Bruised but alive, you claw your way out and crawl back to the entrance. This time you light the torch. Lesson " +
      "learned: check before you reach! In its glow you can see the floor is riddled with pits.",
  );
  yield* frozenDoor(q);
}

function* cavePath(q) {
  q.banner("cave");
  q.narrate(
    "Cold air flows from the mouth of the Event Loop Caverns. The one long tunnel inside bends back on itself and comes " +
      "around again, and again, and whatever is waiting down here gets its turn only when the tunnel is clear. Just " +
      "inside, you find an old torch and a flint. Lighting it would help you see, but the light might also wake whatever " +
      "is hissing in the dark...",
  );
  const move = yield choose("Light the torch", "Proceed in the dark");
  if (move === "1") {
    addPoints(q, rules.WISE_CHOICE_POINTS, "wise choice");
    q.narrate(
      "The torch flares to life. Good thing, too: the floor ahead is riddled with deep pits, and someone has scratched " +
        "\"undefined\" beside each one. The hissing, you realize, is only wind whistling through cracks in the rock.",
    );
    yield* frozenDoor(q);
    return;
  }
  yield* pitOfUndefined(q);
}

// ------------------------------------------------------------------
// The castle
// ------------------------------------------------------------------

function* sameOriginGate(q) {
  q.banner("gate");
  q.narrate(
    "Golden griffins glare down from tattered banners as you reach the gate. The iron portcullis is raised, but as you " +
      "step beneath it a ghostly knight in rusted armor drifts out of the stone. \"Halt! You are of another origin. None " +
      "may pass without the proper headers.\"",
  );
  if (!(yield* faceChallenge(q, "The Same-Origin Knight"))) {
    gameOver(q, "\"Blocked by CORS policy,\" says the knight, and the portcullis crashes down. You are left outside in the dark, far from the promise.");
    return;
  }

  q.narrate("The knight lowers its sword and presses a cold silver ring into your palm. \"Access-Control-Allow-Origin,\" it says, with some effort.");
  collectRelic(q, "Allow-Origin Signet");
  q.banner("hall");
  q.narrate(
    "Beyond the gate lies the Hall of Hoisting, its arches broken and open to the sky. Everything ever declared in this " +
      "castle has been hoisted to the top of the hall, while its value was left behind. Torches flicker beside the throne " +
      "at the top of the steps: declared, but empty, undefined until someone reaches that line. Behind it, a narrow " +
      "passage glows with a faint golden light. To one side, a grand staircase climbs into the dark, its steps cracked " +
      "and crumbling, each one carved with the words document.write.",
  );
  const move = yield choose("Take the glowing passage behind the throne", "Climb the crumbling grand staircase");
  if (move === "1") {
    addPoints(q, rules.WISE_CHOICE_POINTS, "wise choice");
    q.narrate("The passage winds down beneath the castle and comes out on the steps of an ancient temple.");
    yield* templeVault(q);
    return;
  }
  gameOver(q, "Halfway up, the staircase gives way beneath your feet. Nobody has repaired it in decades, and nobody has dared take it down. You tumble down in a cloud of dust, and Castle Mocha keeps its secrets.");
}

function* ramparts(q) {
  q.banner("ramparts");
  q.narrate(
    "You climb onto the Ramparts of Rejection, where whatever falls, falls until somebody catches it. The moon hangs over " +
      "a sea of mist and the wind howls between the towers. On the wall ahead crouches a stone gargoyle. As you come near, " +
      "its eyes crack open and glow. \"Answer me, climber. I reject most of those who come here, and there is no one below " +
      "to catch them.\"",
  );
  if (!(yield* faceChallenge(q, "The Rejecting Gargoyle"))) {
    gameOver(q, "The gargoyle rejects you, and over the edge you go. No .catch() waits below. Uncaught (in promise), you vanish into the mist.");
    return;
  }

  q.narrate("The gargoyle grinds out a laugh and drops a glittering stone from its claw.");
  collectRelic(q, "Settled Stone");
  q.banner("gallery");
  q.narrate(
    "The ramparts lead into a tall tower and up to a moonlit gallery. Far below the balustrade, a golden temple roof " +
      "glints through the mist. Ivy as thick as rope hangs over the edge, and a spiral stair winds down inside the tower.",
  );
  const move = yield choose("Take the spiral stair down inside the tower", "Climb down the ivy from the gallery");
  if (move === "1") {
    addPoints(q, rules.WISE_CHOICE_POINTS, "wise choice");
    q.narrate("Round and round you go, down and down, like a call stack unwinding, until a small door at the foot of the tower opens beside the temple steps.");
    yield* templeVault(q);
    return;
  }
  gameOver(q, "The ivy is older than the DOM. It tears loose with a snap, and you drop into the mist far below.");
}

function* castlePath(q) {
  q.banner("castle");
  q.narrate(
    "A winding stone trail climbs out of the mist to the ruins of Castle Mocha, thrown up in just ten days by a single " +
      "mason, and renamed twice since. Torches still burn along the way, and the whole of the web still stands on its " +
      "foundations, cracks and all, because nobody dares take out a single stone. The trail ends at the Same-Origin Gate. " +
      "Beside it, a crumbling stair climbs the outer wall toward the ramparts.",
  );
  const move = yield choose("Follow the torches to the Same-Origin Gate", "Climb the crumbling stair to the ramparts");
  yield* move === "1" ? sameOriginGate(q) : ramparts(q);
}

const PATH_STORIES = { forest: forestPath, cave: cavePath, castle: castlePath };

// ------------------------------------------------------------------
// The start
// ------------------------------------------------------------------

export function* startGame(q) {
  q.banner("start");
  let chosen;
  if (q.onlyPath) {
    // A winner going back for a path they didn't take, score and all.
    const path = rules.PATHS.find((candidate) => candidate.key === q.onlyPath);
    const fresh = q.skipQuestions.size === 0 ? "" : ", where new riddles await";
    q.narrate(
      `Welcome back, ${q.name}! You return to the edge of Scriptoria with ${q.carried} points from your last quest, ` +
        `wondering what waits down the way you didn't take. This time you turn toward ${path.sight}${fresh}.`,
    );
    yield choose(path.label);
    chosen = path;
  } else {
    const threePaths =
      "the Callback Forest, where every path opens onto another path inside it; the Event Loop Caverns, whose one long " +
      "tunnel always comes back around; and a torch-lit trail that climbs to the ruins of Castle Mocha.";
    if (q.carried > 0) {
      // A winner carrying their score up to the next level.
      q.narrate(
        `Welcome back, ${q.name}! You return to the edge of Scriptoria with ${q.carried} points from your last quest. ` +
          "Word of your success has reached the guardians, and their riddles will be harder this time. Three paths lie " +
          `before you once more: ${threePaths}`,
      );
    } else {
      q.narrate(
        `Welcome, ${q.name}! You arrive at the edge of Scriptoria with nothing but a backpack and a vague sense that it ` +
          `will all be fine at runtime. Three paths lie before you: ${threePaths}`,
      );
    }
    const move = yield choose(...rules.PATHS.map((path) => path.label));
    chosen = rules.PATHS[Number(move) - 1];
  }
  q.path = chosen.key;
  yield* PATH_STORIES[chosen.key](q);
}

// ------------------------------------------------------------------
// The bonus dragons, and the final boss
// ------------------------------------------------------------------

/** The bonus after a win: the riddle of the dragon of this path and level. Right, a share of its treasure;
    wrong, nothing lost. The quest stays won whatever the answer. */
export function* dragonBattle(q) {
  const dragon = rules.findDragon(q.difficulty, q.path);
  const [banner] = rules.SCENES[dragon.scene];
  const { lair } = rules.PATHS.find((path) => path.key === q.path);
  q.banner(dragon.scene);
  q.narrate(
    `${lair} There, coiled around an overflowing treasure chest, sleeps the ${banner.slice("The ".length)}, its scales ` +
      `${dragon.scales}. As you creep closer, one great eye slides open. "A riddle, little coder," it rumbles. "Answer ` +
      `well, and a share of my treasure is yours. Answer badly, and run."`,
  );
  const question = dragonQuestion(q.difficulty, q.path);
  if (yield* askQuestion(q, banner, question, rules.DRAGON_POINTS, "the dragon's treasure")) {
    q.dragon = "won";
    q.narrate("The dragon rumbles a deep laugh and nudges its chest toward you with its snout. You fill your pockets with treasure and slip away.");
  } else {
    q.dragon = "lost";
    q.narrate("The dragon snorts a cloud of smoke, and you flee, empty-handed but unharmed.");
  }
}

/** The final boss, for a winner who has completed every path on every level: one of the nine ultimate
    questions, picked at random. Right: the title of JavaScript Master and BOSS_POINTS besides. Wrong: all is
    lost, the score falls to zero. */
export function* bossBattle(q) {
  q.banner("boss");
  q.narrate(
    "You have walked every path in Scriptoria. As you leave the temple for the last time, the ground shudders and the " +
      "jungle falls silent, as if it were waiting to hear back. Out of the black water rises the thing the Golden Promise " +
      "was forged to defeat: a vast stepped pyramid of cracked stone, yellow light bleeding through its seams, each level " +
      "carved with a function called from inside the one below it, each one closed off with its own });. Two great clawed " +
      "arms drag themselves out of the jungle, wound in glowing chains that end in scraps of parchment: function () {, and " +
      "nothing after it. Old curses flutter from the vines all around: undefined is not a function, [object Object], " +
      "Uncaught (in promise). Above a cracked yellow JS, a fanged mouth splits the stone, and over it opens one burning " +
      "yellow eye. \"Every path, every level,\" it grinds. \"You thought a promise could flatten me? I am every callback " +
      "ever nested inside another. I am what your language was, and what it becomes again the moment you grow careless. " +
      "One question remains. Answer it, and you are a JavaScript Master. Fail, and you will wait forever for me to call " +
      "you back.\"",
  );
  const question = bossQuestions[q.rng.next(bossQuestions.length)];
  if (yield* askQuestion(q, rules.BOSS_NAME, question, rules.BOSS_POINTS, "JavaScript Master")) {
    q.boss = "won";
    q.narrate(
      "The great eye blinks. The chains fall slack, and one by one the levels of the pyramid slide back into line, until " +
        "all that's left is a single flat row of stones, each one awaiting the last. \"Flattened,\" it sighs, and the yellow " +
        "light goes out. From this day on, the coders of Scriptoria will know you by your new title.",
    );
    q.note("relic", "You are a JavaScript Master!");
  } else {
    q.boss = "lost";
    q.score = 0;
    q.narrate(
      "\"err,\" says the pyramid, which is always the first thing it says, and the last. Every coin, relic and point you " +
        "carried is swallowed into a callback that will never be called. You wake at the edge of Scriptoria with nothing " +
        "but a backpack and a vague sense that it will all be fine at runtime.",
    );
    q.note("life", "All is lost! Your score falls to 0.");
  }
}
