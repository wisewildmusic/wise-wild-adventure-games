// A quest, and replay(), which plays one through from the start.
import { Rng } from "./random.js";
import * as rules from "./rules.js";
import { bossBattle, dragonBattle, startGame } from "./story.js";

/** The moves a prompt accepts: "1", "2", ... for a menu of choices, "a" to "d" for a challenge. */
export function promptMoves(prompt) {
  return prompt.kind === "choice"
    ? prompt.options.map((_, i) => String(i + 1))
    : rules.LETTERS.slice(0, prompt.options.length);
}

/** One explorer's quest: their progress, the scene they're in, what happened since their last move,
    and what the game is waiting for now. */
class Quest {
  constructor({ name, difficulty, seed, carried, onlyPath, skipQuestions, version, final }) {
    this.rng = new Rng(seed); // with the same seed, the same shuffles on every replay
    this.name = name;
    this.difficulty = difficulty;
    this.lives = rules.level(difficulty).lives;
    this.score = carried;
    this.inventory = [];
    this.deck = [];

    this.carried = carried;
    this.onlyPath = onlyPath;
    this.skipQuestions = new Set(skipQuestions);
    this.version = version;
    this.final = final;

    this.asked = []; // question numbers asked, in order
    this.path = null; // the path it went down, once chosen
    this.dragon = null; // the bonus dragon: "won" or "lost" once answered
    this.boss = null; // the final boss: "won" or "lost" once answered

    this.scene = "start";
    this.log = [];
    this.prompt = null; // null once the quest (or a battle) is over
    this.result = null; // "win" or "lose" once the quest is over
  }

  dragonAwaits() {
    if (this.result === "win" && !this.prompt && !this.dragon && !this.boss) {
      return rules.findDragon(this.difficulty, this.path);
    }
    return null;
  }

  bossAwaits() {
    return Boolean(this.final) && this.result === "win" && !this.prompt && !this.boss;
  }

  banner(scene) {
    this.scene = scene;
  }

  narrate(text) {
    this.log.push(["story", text]);
  }

  note(kind, text) {
    this.log.push([kind, text]);
  }
}

/**
 * Plays a quest from the start with the moves made so far, and returns it as it stands now. Its log holds
 * what happened after the last move.
 *
 * JavaScript's generators stand in for the console game's input(). The story yields a prompt and stops
 * right there, in the middle of whatever it was doing, and game.next(move) carries it on with the move as
 * the value of that yield. After a win, the dragon's move wakes the bonus dragon and the next move answers
 * its riddle. A final quest (one that completes every path on every level) can then face the boss: the
 * boss's move, then the answer.
 */
export function replay(request) {
  const quest = new Quest(request);
  let game = startGame(quest);
  quest.prompt = game.next().value ?? null;
  for (const move of request.moves) {
    if (move === rules.DRAGON_MOVE && quest.dragonAwaits()) {
      game = dragonBattle(quest);
    } else if (move === rules.BOSS_MOVE && quest.bossAwaits()) {
      game = bossBattle(quest);
    } else if (!quest.prompt || !promptMoves(quest.prompt).includes(move)) {
      break;
    }
    quest.log = [];
    quest.prompt = game.next(move).value ?? null;
  }
  return quest;
}
