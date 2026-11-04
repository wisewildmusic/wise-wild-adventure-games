#pragma once

#include <cstdint>
#include <optional>
#include <random>
#include <set>
#include <string>
#include <utility>
#include <variant>
#include <vector>

#include "Questions.hpp"
#include "Rules.hpp"

namespace templaria {

/// A seeded source of random numbers that gives the same numbers on every compiler, so a saved quest
/// replays the same wherever it's run. std::mt19937's numbers are fixed by the standard, but
/// std::uniform_int_distribution's and std::shuffle's are not: Microsoft's library and GNU's give
/// different results. So the numbers are cut down to size here by hand.
class Rng {
public:
    explicit Rng(long long seed) : engine_(static_cast<std::uint32_t>(seed)) {}

    /// A whole number from 0 up to bound - 1, each equally likely.
    int next(int bound) {
        const auto range = static_cast<std::uint32_t>(bound);
        const std::uint32_t too_low = (0u - range) % range;  // 2^32 mod range: the numbers to throw away
        std::uint32_t number;
        do {
            number = static_cast<std::uint32_t>(engine_());
        } while (number < too_low);
        return static_cast<int>(number % range);
    }

private:
    std::mt19937 engine_;
};

/// A Fisher-Yates shuffle, written out for the same reason.
template <typename T>
void shuffle(Rng& rng, std::vector<T>& items) {
    for (int i = static_cast<int>(items.size()) - 1; i > 0; --i)
        std::swap(items[i], items[rng.next(i + 1)]);
}

inline const std::vector<std::string> letters = {"a", "b", "c", "d"};

/// A menu: the explorer picks an option (moves "1", "2", ...).
struct Choice {
    std::vector<std::string> options;
};

/// A challenge: the explorer picks an answer (moves "a" to "d").
struct Challenge {
    std::string challenger;
    const Question* question;
    std::vector<std::string> options;
};

/// What the game is waiting for: a menu of choices, or a C++ challenge.
using Prompt = std::variant<Choice, Challenge>;

std::vector<std::string> prompt_moves(const Prompt& prompt);

/// Everything that defines a quest: replaying it always gives the same result.
struct QuestRequest {
    std::string name;
    std::string difficulty;
    long long seed = 0;
    std::vector<std::string> moves;
    int carried = 0;
    std::optional<std::string> only_path;
    std::vector<int> skip_questions;
    int version = rules::game_version;
    bool is_final = false;
};

/// One explorer's quest: their progress, the scene they're in, what happened since their last move,
/// and what the game is waiting for now.
struct Quest {
    explicit Quest(const QuestRequest& request);

    // With the same seed, the same shuffles on every replay.
    Rng rng;

    std::string name;
    std::string difficulty;
    int lives;
    int score;
    std::vector<std::string> inventory;
    std::vector<int> deck;

    int carried;
    std::optional<std::string> only_path;
    std::set<int> skip_questions;
    int version;
    bool is_final;

    std::vector<int> asked;             // question numbers asked, in order
    std::optional<std::string> path;    // the path it went down, once chosen
    std::optional<std::string> dragon;  // the bonus dragon: "won" or "lost" once answered
    std::optional<std::string> boss;    // the final boss: "won" or "lost" once answered

    std::string scene = "start";
    std::vector<std::pair<std::string, std::string>> log;
    std::optional<Prompt> prompt;       // empty once the quest (or a battle) is over
    std::optional<std::string> result;  // "win" or "lose" once the quest is over

    std::string move;     // the explorer's latest move, for the story to read
    bool passed = false;  // how the latest challenge went

    const Dragon* dragon_awaits() const;
    bool boss_awaits() const;

    void banner(std::string new_scene) { scene = std::move(new_scene); }
    void narrate(std::string text) { log.emplace_back("story", std::move(text)); }
    void note(std::string kind, std::string text) { log.emplace_back(std::move(kind), std::move(text)); }
};

/// Plays a quest from the start with the moves made so far, and returns it as it stands now.
Quest replay(const QuestRequest& request);

}  // namespace templaria
