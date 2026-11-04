"""Checks the AI game (site/neuralia.py), the one whose questions aren't all code:

- Every level has 60 questions: all 40 terms of AI (neuralia.TERMS), each once and in order, then 20 more.
- Every question is well made: four different options, the answer among them, and an explanation that names its term.
- Nothing is asked twice in the game, and no answer gives itself away by always being the longest.
- Every question with "runs" set is run with Python, and what it prints must be its answer. So is every dragon's and
  boss's that has it.
- The road is as long as it says: every route to the treasure has exactly neuralia.TRIALS trials. Each is played through,
  including the choices that cost a life or end the quest, and every scene it names exists, with a picture.
- A whole run asks every question: three paths on each of three levels, carried on as app.py carries them, reach all 60 on
  each level (so all 40 terms) with no repeats before that, then nine dragons and the boss. Its three heads ask in turn, each
  from its own questions: all three right is a win, and a wrong answer to any one of them ends it and loses everything.
- Replaying the same seed and moves gives the same quest.

    python check-ai-questions.py
"""
import contextlib
import io
import random
import sys
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent / "site"
sys.path.insert(0, str(SITE))
import neuralia  # noqa: E402

problems = []


def problem(text):
    problems.append(text)


def check_question(where, question):
    options = question["options"]
    if len(options) != 4 or len(set(options)) != 4:
        problem(f"{where}: needs four different options: {options}")
    if question["answer"] not in options:
        problem(f"{where}: the answer isn't among the options")
    words = {question["term"].lower(), question["term"].lower().replace("-", " ")}
    text = " ".join([question["prompt"], question["explain"], question["answer"]]).lower().replace("-", " ")
    if not any(word.replace("-", " ") in text for word in words):
        problem(f"{where}: its explanation never names {question['term']!r}")
    if not question["explain"].strip():
        problem(f"{where}: no explanation")
    if question.get("runs"):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            exec(question["code"], {})
        if out.getvalue().strip() != question["answer"]:
            problem(f"{where}: printed {out.getvalue().strip()!r}, but the answer is {question['answer']!r}")


def check_bank():
    every_prompt = {}
    longest = visibly = total = ran = 0
    if len(set(neuralia.TERMS)) != 40:
        problem(f"{len(set(neuralia.TERMS))} different terms, not 40")
    for level, questions in neuralia.QUESTIONS.items():
        if len(questions) != neuralia.QUESTION_COUNTS[neuralia.GAME_VERSION]:
            problem(f"{level}: {len(questions)} questions")
        terms = [question["term"] for question in questions[:len(neuralia.TERMS)]]
        if terms != neuralia.TERMS:
            missing = set(neuralia.TERMS) - set(terms)
            problem(f"{level}: the first 40 aren't the 40 terms in order (missing: {sorted(missing)}, got {terms})")
    specials = [(f"dragon {key}", dragon["question"]) for key, dragon in neuralia.DRAGONS.items()]
    specials += [(f"boss {number}", question) for number, question in enumerate(neuralia.BOSS_QUESTIONS)]
    numbered = [(f"{level} {number}", question) for level, questions in neuralia.QUESTIONS.items()
                for number, question in enumerate(questions)]
    for where, question in numbered + specials:
        check_question(where, question)
        ran += bool(question.get("runs"))
        key = (question["prompt"], question.get("code"))
        if key in every_prompt:
            problem(f"{where}: the same question as {every_prompt[key]}")
        every_prompt[key] = where
        lengths = [len(option) for option in question["options"]]
        if max(lengths) > 3 * min(lengths) and len(question["answer"]) == max(lengths) and min(lengths) > 12:
            problem(f"{where}: the answer is much the longest option")
        total += 1
        others = [len(option) for option in question["options"] if option != question["answer"]]
        longest += len(question["answer"]) > max(others)
        visibly += len(question["answer"]) > max(others) * 1.1 and len(question["answer"]) > 25  # (not a term's name)
    if list(neuralia.BOSS_HEADS) != ["Model Collapse", "Hallucinations", "Fact Erosion"]:
        problem(f"the boss's heads are {list(neuralia.BOSS_HEADS)}")
    for head, questions in neuralia.BOSS_HEADS.items():
        if len(questions) != 6:
            problem(f"{head}: {len(questions)} questions, not 6")
    print(f"{total} questions: {len(numbered)} on the levels, {len(neuralia.DRAGONS)} dragons, "
          f"{len(neuralia.BOSS_QUESTIONS)} for the boss's three heads. {ran} of them run as Python.")
    print(f"The right answer is the longest option in {longest} of {total} ({100 * longest // total}%; 25% is chance), "
          f"and visibly the longest in {visibly}.")
    if longest > total * 0.35 or visibly > total * 0.05:
        problem("the right answer is too often the longest, so length gives it away")


def right_move(quest):
    """The letter of the right answer to the question the quest is waiting on."""
    question = quest_question(quest)
    for letter, option in quest.prompt.options:
        if option == question["answer"]:
            return letter
    raise AssertionError("no right answer on offer")


def quest_question(quest):
    if quest.scene.startswith("dragon-"):
        return neuralia.DRAGONS[(quest.player["difficulty"], quest.path)]["question"]
    if quest.scene == "boss":
        return next(q for q in neuralia.BOSS_QUESTIONS if q["prompt"] == quest.prompt.prompt and q.get("code") == quest.prompt.code)
    return neuralia.QUESTIONS[quest.player["difficulty"]][quest.asked[-1]]


def wrong_move(quest):
    return next(letter for letter, option in quest.prompt.options if option != quest_question(quest)["answer"])


class Walker:
    """Plays a quest move by move through replay(), as the site does."""

    def __init__(self, level, seed, carried=0, only_path=None, skip=(), final=False):
        self.args = ("Tester", level, seed)
        self.options = dict(carried=carried, only_path=only_path, skip_questions=skip, final=final)
        self.moves = []
        self.quest = self.now()

    def now(self):
        return neuralia.replay(*self.args, self.moves, **self.options)

    def move(self, move):
        self.moves.append(move)
        self.quest = self.now()
        return self.quest

    def play(self, choices, on_question=right_move):
        """Answers everything rightly (or as `on_question` says) and takes the numbered choices in order, then the
        second choice wherever there is one. Stops at the end of the quest. Returns the scenes seen."""
        choices = iter(choices)
        scenes = []
        while self.quest.prompt is not None:
            scenes.append(self.quest.scene)
            if self.quest.prompt.kind == "choice":
                move = next(choices, "2")
                self.move(move if self.quest.prompt.accepts(move) else "1")
            else:
                self.move(on_question(self.quest))
        scenes.append(self.quest.scene)
        return scenes


def check_scene_pictures(scenes):
    pictures = SITE / "static" / "img" / "adventure"
    for scene in set(scenes):
        banner, picture, description = neuralia.SCENES[scene]
        if not (pictures / picture).exists():
            problem(f"scene {scene}: no picture {picture}")


# The choices that lead to the treasure, by route: (path, the choices taken, chest last: 2 walks past it).
ROUTES = {
    "river": ["1", "1", "1", "1", "2"],
    "tree": ["1", "2", "1", "1", "2"],
    "cave, lit": ["2", "1", "1", "1", "2"],
    "cave, dark": ["2", "2", "1", "1", "1", "2"],
    "gate": ["3", "1", "1", "1", "2"],
    "ramparts": ["3", "2", "1", "1", "2"],
}


def check_routes():
    all_scenes = set()
    for level in neuralia.DIFFICULTY_SETTINGS:
        for name, choices in ROUTES.items():
            walker = Walker(level, 7)
            scenes = walker.play(choices)
            all_scenes.update(scenes)
            quest = walker.quest
            if quest.result != "win":
                problem(f"{level} {name}: ended {quest.result}, not a win")
            if quest.trials != neuralia.TRIALS or len(quest.asked) != neuralia.TRIALS:
                problem(f"{level} {name}: {quest.trials} trials and {len(quest.asked)} questions, not {neuralia.TRIALS}")
            if len(set(quest.asked)) != len(quest.asked):
                problem(f"{level} {name}: a question repeated")
    print(f"All {len(ROUTES)} routes on all 3 levels: {neuralia.TRIALS} trials each, to the treasure.")

    # Every choice that isn't the wise one: it must cost a life or end the quest, never do nothing or crash.
    tested = 0
    for name, base in ROUTES.items():
        for position in range(1, len(base)):
            changed = base[:position] + ["2"] + base[position:]
            walker = Walker("easy", 3)
            all_scenes.update(walker.play(changed))
            quest = walker.quest
            tested += 1
            if quest.result not in ("win", "lose"):
                problem(f"{name}: odd result {quest.result!r} with choices {changed}")
            if quest.result == "lose" and quest.scene != "game_over":
                problem(f"{name}: lost, but on scene {quest.scene} with choices {changed}")
    print(f"{tested} other sets of choices played through, to a win or a game over.")

    # Running out of lives everywhere: every guardian's failure message, and every poor choice on the last life.
    outcomes = 0
    for level in neuralia.DIFFICULTY_SETTINGS:
        for name, choices in ROUTES.items():
            for seed in range(40):
                walker = Walker(level, seed)
                rng = random.Random(seed)
                # Wrong answers at random, so the lives run out at a different place each time.
                odds = rng.random()
                moves = iter(choices + ["1"] * 20)
                while walker.quest.prompt is not None:
                    if walker.quest.prompt.kind == "choice":
                        walker.move(next(moves))
                    else:
                        walker.move(wrong_move(walker.quest) if rng.random() < odds else right_move(walker.quest))
                all_scenes.add(walker.quest.scene)
                outcomes += 1
                if walker.quest.result not in ("win", "lose"):
                    problem(f"{level} {name} seed {seed}: ended {walker.quest.result!r}")
    print(f"{outcomes} quests with wrong answers at random all ended properly.")

    # Poor choices on the last life: they must end the quest there and then.
    for name, choices in (("river", ["1", "1", "1", "2"]), ("tree", ["1", "2", "1", "2"]), ("cave", ["2", "1", "1", "2"]),
                          ("gate", ["3", "1", "1", "2"]), ("ramparts", ["3", "2", "1", "2"])):
        walker = Walker("hard", 11)
        wrong_left = neuralia.DIFFICULTY_SETTINGS["hard"]["lives"] - 1
        moves = iter(choices)
        while walker.quest.prompt is not None:
            if walker.quest.prompt.kind == "choice":
                walker.move(next(moves))
            elif wrong_left:
                wrong_left -= 1
                walker.move(wrong_move(walker.quest))
            else:
                walker.move(right_move(walker.quest))
        if walker.quest.result != "lose" or walker.quest.scene != "game_over":
            problem(f"{name}: a poor choice on the last life gave {walker.quest.result} on {walker.quest.scene}")
    print("A poor choice on the last life ends the quest on every route that has one.")

    check_scene_pictures(all_scenes)
    unseen = set(neuralia.SCENES) - all_scenes - {"start", "boss"} - {d["scene"] for d in neuralia.DRAGONS.values()}
    if unseen:
        problem(f"scenes never reached: {sorted(unseen)}")


def check_whole_run(answers):
    """Three paths on each of three levels, carried on as app.py does it, then the boss, whose heads are answered
    rightly or wrongly as `answers` says (it stops at the first wrong one)."""
    score = 0
    terms_met = {level: set() for level in neuralia.DIFFICULTY_SETTINGS}
    dragons = set()
    stages = [(level, path) for level in neuralia.DIFFICULTY_SETTINGS for path in neuralia.PATHS]
    choices = {"forest": ["1", "1", "1", "2"], "cave": ["1", "1", "1", "2"], "castle": ["1", "1", "1", "2"]}
    skip, previous_level, walker, asked_total = [], None, None, 0
    for number, (level, path) in enumerate(stages):
        if level != previous_level:
            skip = []
        previous_level = level
        final = number == len(stages) - 1
        walker = Walker(level, 1000 + number, carried=score, only_path=path, skip=list(skip), final=final)
        walker.play(["1"] + choices[path])
        quest = walker.quest
        if quest.result != "win":
            problem(f"run: {level} {path} ended {quest.result}")
        questions = neuralia.QUESTIONS[level]
        for asked in quest.asked:
            terms_met[level].add(questions[asked]["term"])
        before = len(skip)
        if set(quest.asked) & set(skip) and before + len(set(quest.asked)) < len(questions):
            problem(f"run: {level} {path} repeated a question before all were asked")
        skip += quest.asked
        asked_total += len(quest.asked)
        # The dragon, then the next quest takes the score.
        walker.move(neuralia.DRAGON_MOVE)
        dragons.add(walker.quest.scene)
        walker.move(right_move(walker.quest))
        score = walker.quest.player["score"]
    for level, met in terms_met.items():
        missing = set(neuralia.TERMS) - met
        if missing:
            problem(f"run: {level} never met these terms: {sorted(missing)}")
        asked = {question["term"] for question in neuralia.QUESTIONS[level]}
        if asked - met:
            problem(f"run: {level} left out {sorted(asked - met)}")
    if len(dragons) != 9:
        problem(f"run: met {len(dragons)} dragons")
    # The boss.
    if not walker.quest.boss_awaits():
        problem("run: the boss doesn't await after every path on every level")
    walker.move(neuralia.BOSS_MOVE)
    if walker.quest.scene != "boss":
        problem("run: the boss's scene didn't come up")
    before = walker.quest.player["score"]
    heads = list(neuralia.BOSS_HEADS)
    for number, right in enumerate(answers):
        if walker.quest.prompt is None or walker.quest.prompt.challenger != heads[number]:
            problem(f"run: head {number + 1} should be asking now: {heads[number]}")
        if quest_question(walker.quest)["answer"] not in [option for _, option in walker.quest.prompt.options]:
            problem(f"run: {heads[number]}'s question isn't its own")
        if quest_question(walker.quest) not in neuralia.BOSS_HEADS[heads[number]]:
            problem(f"run: {heads[number]} asked another head's question")
        walker.move(right_move(walker.quest) if right else wrong_move(walker.quest))
    quest = walker.quest
    beaten = all(answers)
    if quest.prompt is not None:
        problem("run: the boss is still asking after it should have finished")
    if beaten and (quest.boss != "won" or quest.player["score"] != before + neuralia.BOSS_POINTS * 3):
        problem(f"run: beating the boss gave {quest.boss} and {quest.player['score']}")
    if not beaten and (quest.boss != "lost" or quest.player["score"] != 0):
        problem(f"run: losing to the boss gave {quest.boss} and {quest.player['score']}")
    if quest.boss_awaits() or quest.dragon_awaits():
        problem("run: something still awaits after the boss")
    print(f"A whole run, {'beating the boss' if beaten else f'losing to head {len(answers)}'}: {asked_total} questions on the "
          f"road, plus 9 dragons and {len(answers)} from the boss. Score before the boss: {before}. Every term met on every level.")


def check_replay():
    walker = Walker("medium", 99)
    walker.play(ROUTES["river"])
    again = neuralia.replay("Tester", "medium", 99, walker.moves)
    if again.asked != walker.quest.asked or again.player["score"] != walker.quest.player["score"]:
        problem("replaying the same moves gave a different quest")
    print(f"Replaying {len(walker.moves)} moves gives the same quest.")


check_bank()
check_routes()
check_whole_run([True, True, True])
check_whole_run([False])
check_whole_run([True, False])
check_whole_run([True, True, False])
check_replay()
if problems:
    print(f"\n{len(problems)} PROBLEMS:")
    for line in problems:
        print(" -", line)
    sys.exit(1)
print("\nAll good.")
