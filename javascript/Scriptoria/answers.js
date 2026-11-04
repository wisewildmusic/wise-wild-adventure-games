// What the program says back to the website: plain objects, in the shape site/compiled_game.py reads.
import { promptMoves, replay } from "./game.js";
import { bossQuestions, dragonQuestion, levelQuestions } from "./questions.js";
import * as rules from "./rules.js";
import { LETTERS } from "./rules.js";

function promptAnswer(prompt) {
  if (!prompt) return null;
  if (prompt.kind === "choice") {
    return { kind: "choice", moves: promptMoves(prompt), options: prompt.options };
  }
  return {
    kind: "question",
    moves: promptMoves(prompt),
    options: prompt.options.map((option, i) => [LETTERS[i], option]),
    challenger: prompt.challenger,
    prompt: prompt.question.prompt,
    code: prompt.question.code,
  };
}

function questAnswer(quest) {
  return {
    scene: quest.scene,
    result: quest.result,
    player: {
      name: quest.name,
      difficulty: quest.difficulty,
      lives: quest.lives,
      score: quest.score,
      inventory: quest.inventory,
    },
    log: quest.log,
    asked: quest.asked,
    path: quest.path,
    dragon: quest.dragon,
    boss: quest.boss,
    dragonAwaits: quest.dragonAwaits()?.scene ?? null,
    bossAwaits: quest.bossAwaits(),
    prompt: promptAnswer(quest.prompt),
  };
}

function infoAnswer() {
  return {
    gameVersion: rules.GAME_VERSION,
    questionCounts: rules.QUESTION_COUNTS,
    levels: rules.LEVELS,
    paths: rules.PATHS.map(({ key, label, name }) => ({ key, label, name })),
    scenes: rules.SCENES,
    dragonMove: rules.DRAGON_MOVE,
    dragonPoints: rules.DRAGON_POINTS,
    bossMove: rules.BOSS_MOVE,
    bossPoints: rules.BOSS_POINTS,
    texts: { ...rules.TEXTS, intro: rules.INTRO },
  };
}

function questionsAnswer() {
  return {
    levels: levelQuestions,
    dragons: rules.DRAGONS.map(({ level, path, scene }) => ({
      level,
      path,
      scene,
      question: dragonQuestion(level, path),
    })),
    boss: bossQuestions,
  };
}

const COMMANDS = {
  info: infoAnswer,
  replay: (request) => questAnswer(replay(request)),
  questions: questionsAnswer,
};

export function answer(request) {
  // (Object.hasOwn, so that a command such as "toString" isn't found on Object's prototype.)
  if (!Object.hasOwn(COMMANDS, request.command)) throw new Error("Unknown command");
  return COMMANDS[request.command](request);
}
