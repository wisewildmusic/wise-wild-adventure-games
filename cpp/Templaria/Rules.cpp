#include "Rules.hpp"

#include <algorithm>
#include <stdexcept>

namespace templaria::rules {

const std::map<int, int>& question_counts() {
    static const std::map<int, int> counts = {{1, 20}};
    return counts;
}

const std::vector<Level>& levels() {
    static const std::vector<Level> all = {
        {"easy", 3, 1, "variables, types, arrays, if/else, simple loops"},
        {"medium", 2, 2, "pointers, references, strings, containers, functions, scope"},
        {"hard", 1, 3, "classes, RAII, templates, smart pointers, move semantics"},
    };
    return all;
}

const Level& level(const std::string& key) {
    const auto found = std::ranges::find(levels(), key, &Level::key);
    if (found == levels().end()) throw std::runtime_error("no such level: " + key);
    return *found;
}

// The three ways into Templaria, in the order the first choice offers them.
const std::vector<GamePath>& paths() {
    static const std::vector<GamePath> all = {
        {"forest", "Explore the Template Forest", "the Template Forest",
         "the Template Forest, where every tree grows from the same pattern",
         "On your way back through the Template Forest, a glint of gold catches your eye in a mossy hollow."},
        {"cave", "Enter the Heap Caverns", "the Heap Caverns",
         "the Heap Caverns, where whatever is left behind stays forever",
         "On your way back out of the Heap Caverns, a glint of gold catches your eye in a side cave."},
        {"castle", "Climb to the Ruins of Castle Cfront", "the Ruins of Castle Cfront",
         "the torch-lit trail that climbs to the ruins of Castle Cfront",
         "On your way back through Castle Cfront, a glint of gold catches your eye through a doorway: "
         "a forgotten treasury."},
    };
    return all;
}

const std::map<std::string, Scene>& scenes() {
    static const std::map<std::string, Scene> all = {
        {"start", {"The Lost Pointer of Templaria", "title.webp",
                   "A moonlit jungle valley wrapped in mist, a golden temple glowing on a far hilltop"}},
        {"forest", {"The Template Forest", "forest.webp",
                    "Sunbeams falling through towering trees onto a stream, ferns and one giant mossy tree"}},
        {"waterfall", {"The Falls of cout", "waterfall.webp",
                       "A roaring waterfall crashing into a green pool between mossy cliffs, a fallen log high across the gorge"}},
        {"tree", {"The Diamond Tree", "tree.webp",
                  "A great owl on a mossy branch above a sea of mist at sunrise, a golden temple glinting in the distance"}},
        {"cave", {"The Heap Caverns", "cave.webp",
                  "A dark cave mouth framed by carved stone serpents, a torch burning beside it"}},
        {"dark", {"The Segfault Pit", "pit.webp",
                  "A deep pit in the floor of a rocky tunnel, the cave entrance glowing far behind"}},
        {"glyph", {"The Final Door", "glyph-door-cpp.webp",
                   "A massive stone door glowing with lines of C++ code, fire bowls burning on either side"}},
        {"castle", {"The Ruins of Castle Cfront", "castle.webp",
                    "A ruined castle on a misty hilltop under a full moon, torches lighting the stone path that winds up to it"}},
        {"gate", {"The Private Gate", "castle-gate.webp",
                  "A great arched gate with a raised iron portcullis, griffin banners and blazing torches on ivy-covered walls"}},
        {"hall", {"The Hall of Pure Virtuals", "great-hall.webp",
                  "A ruined great hall of broken gothic arches, torches flickering beside an empty throne at the top of worn steps"}},
        {"ramparts", {"The Ramparts of noexcept", "ramparts.webp",
                      "Torch-lit battlements under a full moon, stone towers rising above a misty valley"}},
        {"gallery", {"The Moonlit Gallery", "gallery.webp",
                     "A stone gallery high in a tower, ivy twisting around its pillars, the full moon over a misty valley beyond the balustrade"}},
        {"temple", {"The Temple of the Golden Pointer", "temple.webp",
                    "A torch-lit temple hall leading to a golden vault door guarded by two stone serpents, a jeweled chest by the path"}},
        {"victory", {"The Pointer Is Yours!", "treasure.webp",
                     "The Golden Pointer: a glowing golden orb wrapped by a serpent, on a stone pedestal among gold and gems"}},
        {"dragon-emerald", {"The Emerald Dragon", "dragon-emerald.webp",
                            "A green dragon asleep in a cave, curled around an open treasure chest full of gold and emeralds"}},
        {"dragon-ember", {"The Ember Dragon", "dragon-ember.webp",
                          "A red dragon asleep in a fiery cave around a treasure chest of gold and rubies, a sword and a crown beside it"}},
        {"dragon-frost", {"The Frost Dragon", "dragon-frost.webp",
                          "A blue dragon asleep in an ice cave, its treasure chest full of gold and glowing sapphires"}},
        {"dragon-pearl", {"The Pearl Dragon", "dragon-pearl.webp",
                          "A white dragon asleep in a sunlit forest beside a treasure chest of gold, diamonds and a silver crown"}},
        {"dragon-amethyst", {"The Amethyst Dragon", "dragon-amethyst.webp",
                             "A purple dragon coiled around a treasure chest of gold and glowing amethysts in a violet forest"}},
        {"dragon-autumn", {"The Autumn Dragon", "dragon-autumn.webp",
                           "A copper dragon asleep among autumn leaves beside a treasure chest of gold and a golden goblet"}},
        {"dragon-gold", {"The Golden Dragon", "dragon-gold.webp",
                         "A golden dragon asleep on a heap of gold coins beside a treasure chest in a torch-lit castle hall"}},
        {"dragon-silver", {"The Silver Dragon", "dragon-silver.webp",
                           "A silver dragon asleep in a castle hall beside a chest of silver and diamonds, a knight's helmet and a sword"}},
        {"dragon-shadow", {"The Shadow Dragon", "dragon-shadow.webp",
                           "A black dragon asleep in a castle hall around a chest of gold and rubies, a jeweled crown at its feet"}},
        {"boss", {boss_name, "undefined-behavior.webp",
                  "A horned colossus that can't settle on a shape, half cracked stone and half glitching purple static, "
                  "with one blue eye and one magenta, winged imps pouring from its nostrils, broken chains of glowing "
                  "arrows trailing from its arms and a cracked blue C++ emblem on its chest, among floating stones "
                  "stamped 0xDEADBEEF and upside-down torches in a ruined temple under blue lightning, with signs "
                  "reading delete p; delete p;, *nullptr, INT_MAX+1, a[size] and Segmentation fault (core dumped) "
                  "hanging from it"}},
        {"game_over", {"Segmentation Fault", "game-over.webp",
                       "A burnt-out torch and a lost compass on rocky ground under a blood-red sky"}},
    };
    return all;
}

const std::vector<Dragon>& dragons() {
    static const std::vector<Dragon> all = {
        {"easy", "cave", "dragon-emerald", "green as moss"},
        {"medium", "cave", "dragon-ember", "glowing like hot coals"},
        {"hard", "cave", "dragon-frost", "glittering with ice"},
        {"easy", "forest", "dragon-pearl", "white as moonlight"},
        {"medium", "forest", "dragon-amethyst", "a deep, shimmering purple"},
        {"hard", "forest", "dragon-autumn", "the color of falling leaves"},
        {"easy", "castle", "dragon-gold", "as bright as the coins beneath it"},
        {"medium", "castle", "dragon-silver", "gleaming like polished armor"},
        {"hard", "castle", "dragon-shadow", "as black as a moonless night"},
    };
    return all;
}

const Dragon* find_dragon(const std::string& level, const std::string& path) {
    const auto found = std::ranges::find_if(dragons(), [&](const Dragon& d) { return d.level == level && d.path == path; });
    return found == dragons().end() ? nullptr : &*found;
}

const std::vector<std::string>& intro() {
    static const std::vector<std::string> paragraphs = {
        "Long ago, the first coders of Templaria forged their greatest treasure, the Golden Pointer, which has "
        "never once dangled, and then they lost track of it, as coders of Templaria will. It lies somewhere in "
        "this wild land, where nothing cleans up after you. Its guardians still test every traveler, with riddles "
        "in the language of the realm: C++.",
        "One law holds throughout Templaria: every riddle is standard C++20, with the headers it needs already "
        "included. Plain statements run inside main(), and a riddle that shows its own main() is the whole program.",
        "Answer wisely and choose your path carefully. Every wrong answer costs you a life, and some choices lead "
        "to certain doom...",
    };
    return paragraphs;
}

// The page's own words for this game, by the same keys as the Python game's (pythonia.TEXTS).
const std::map<std::string, std::string>& texts() {
    static const std::map<std::string, std::string> all = {
        {"title", "The Lost Pointer of Templaria"},
        {"language", "C++"},
        {"found", "Found the pointer"},
        {"master", "C++ Master"},
        {"lost_to_boss", "Lost to Undefined Behavior"},
        {"hall_note", "Walk every path on every level to face Undefined Behavior."},
        {"boss_offer_title", "The final challenge: Undefined Behavior"},
        {"boss_offer",
         "You have walked every path on every level, and Undefined Behavior, the thing the standard refuses to "
         "describe, has noticed you. Answer its question, the hardest in all of Templaria, to earn the title of "
         "C++ Master and {points} points."},
        {"boss_warning", "Beware: if you fail, all is lost. Your score falls to zero and you must start over."},
        {"boss_button", "Face Undefined Behavior"},
        {"boss_confirm", "Face Undefined Behavior? If you fail, all is lost: your score falls to zero and you must start over."},
        {"boss_won", "You have faced Undefined Behavior and lived. You are a C++ Master!"},
        {"boss_lost", "Undefined Behavior has struck. All is lost: your score is gone, and you must start over."},
        {"conquered_every_path", "Every path on every level: you've explored all of Templaria!"},
        {"conquered_every_level", "Easy, Medium and Hard: you've conquered every level of Templaria!"},
    };
    return all;
}

}  // namespace templaria::rules
