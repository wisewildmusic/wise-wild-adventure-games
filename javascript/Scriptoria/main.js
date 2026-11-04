// The Lost Promise of Scriptoria: a text adventure with JavaScript challenges, written in JavaScript.
//
// The website (site/compiled_game.py) starts this program whenever it needs the game. It sends one JSON
// request on standard input and reads one JSON answer from standard output:
//
//     {"command": "info"}        the game's settings, paths, scenes and wording
//     {"command": "replay", ...} a quest played through to where it stands (replay() in game.js)
//     {"command": "questions"}   every question, so their answers can be checked by running them
//
// The program keeps nothing between runs. A quest is its random seed plus the moves made so far, and
// every replay plays it again from the start, which always ends in the same place.
//
// This is the program on this PC, run by Node.js. On the server, main-quickjs.js does the same job for QuickJS,
// and those two are the only files that know what they're running on. The rest of the game is plain JavaScript.
import { readFileSync } from "node:fs";

import { answer } from "./answers.js";

try {
  // JSON is built into the language, so unlike the C++ game this one needs no reader or writer of its own.
  // The answer is made whole before anything is written, so a failure part way can't send half of one.
  const request = JSON.parse(readFileSync(0, "utf8"));
  process.stdout.write(JSON.stringify(answer(request)));
} catch (error) {
  console.error(error.message);
  process.exitCode = 2;
}
