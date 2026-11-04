#include "Game.hpp"

#include <algorithm>

#include "Generator.hpp"
#include "Story.hpp"

namespace templaria {

std::vector<std::string> prompt_moves(const Prompt& prompt) {
    std::vector<std::string> moves;
    if (const auto* choice = std::get_if<Choice>(&prompt)) {
        for (std::size_t number = 1; number <= choice->options.size(); ++number)
            moves.push_back(std::to_string(number));
    } else {
        const std::size_t count = std::get<Challenge>(prompt).options.size();
        moves.assign(letters.begin(), letters.begin() + count);
    }
    return moves;
}

Quest::Quest(const QuestRequest& request)
    : rng(request.seed),
      name(request.name),
      difficulty(request.difficulty),
      lives(rules::level(request.difficulty).lives),
      score(request.carried),
      carried(request.carried),
      only_path(request.only_path),
      skip_questions(request.skip_questions.begin(), request.skip_questions.end()),
      version(request.version),
      is_final(request.is_final) {}

const Dragon* Quest::dragon_awaits() const {
    if (result == "win" && !prompt && !dragon && !boss) return rules::find_dragon(difficulty, *path);
    return nullptr;
}

bool Quest::boss_awaits() const { return is_final && result == "win" && !prompt && !boss; }

// Its log holds what happened after the last move. C++20's coroutines stand in for the console game's
// input(): the story co_yields a prompt and carries on at the next move. After a win, the dragon's move
// wakes the bonus dragon and the next move answers its riddle. A final quest (one that completes every
// path on every level) can then face the boss: the boss's move, then the answer.
Quest replay(const QuestRequest& request) {
    Quest quest(request);
    Generator<Prompt> game = start_game(quest);
    quest.prompt = game.next();
    for (const std::string& move : request.moves) {
        if (move == rules::dragon_move && quest.dragon_awaits()) {
            game = dragon_battle(quest);
            quest.log.clear();
            quest.prompt = game.next();
            continue;
        }
        if (move == rules::boss_move && quest.boss_awaits()) {
            game = boss_battle(quest);
            quest.log.clear();
            quest.prompt = game.next();
            continue;
        }
        if (!quest.prompt) break;
        const std::vector<std::string> accepted = prompt_moves(*quest.prompt);
        if (std::ranges::find(accepted, move) == accepted.end()) break;
        quest.log.clear();
        quest.move = move;
        quest.prompt = game.next();
    }
    return quest;
}

}  // namespace templaria
