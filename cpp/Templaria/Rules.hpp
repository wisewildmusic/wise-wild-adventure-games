#pragma once

#include <map>
#include <string>
#include <utility>
#include <vector>

namespace templaria {

struct Level {
    std::string key;
    int lives;
    int multiplier;
    std::string topics;
};

struct GamePath {
    std::string key;
    std::string label;
    std::string name;
    std::string sight;
    std::string lair;
};

struct Scene {
    std::string banner;
    std::string picture;
    std::string description;
};

struct Dragon {
    std::string level;
    std::string path;
    std::string scene;
    std::string scales;
};

/// The game's settings and wording. Pictures are shared with the Python game, in the site's
/// static/img/adventure folder, apart from the Final Door's and the final boss's.
namespace rules {

// Change game_version when the questions change. A quest keeps the version it started on and is always
// replayed with that version's questions: the first question_counts()[version] of each level's list
// (new questions only ever go on the end).
inline constexpr int game_version = 1;

// Base point values. Each one is multiplied by the difficulty multiplier.
inline constexpr int correct_answer_points = 10;
inline constexpr int wise_choice_points = 5;
inline constexpr int relic_points = 15;
inline constexpr int treasure_points = 50;
inline constexpr int life_points = 10;
inline constexpr int dragon_points = 30;
inline constexpr int boss_points = 100;

inline constexpr const char* dragon_move = "dragon";
inline constexpr const char* boss_move = "boss";
inline constexpr const char* boss_name = "Undefined Behavior";

// Each of these is made the first time it's asked for, so nothing can use one before it's built,
// whichever file asks first. (Plain globals in different files would risk the "static initialization
// order fiasco".)
const std::map<int, int>& question_counts();
const std::vector<Level>& levels();
const Level& level(const std::string& key);
const std::vector<GamePath>& paths();
const std::map<std::string, Scene>& scenes();
const std::vector<Dragon>& dragons();
const Dragon* find_dragon(const std::string& level, const std::string& path);
const std::vector<std::string>& intro();
const std::map<std::string, std::string>& texts();

}  // namespace rules
}  // namespace templaria
