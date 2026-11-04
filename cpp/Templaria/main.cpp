// The Lost Pointer of Templaria: a text adventure with C++ challenges, written in C++.
//
// The website (site/compiled_game.py) starts this program whenever it needs the game. It sends one JSON
// request on standard input and reads one JSON answer from standard output:
//
//     {"command": "info"}        the game's settings, paths, scenes and wording
//     {"command": "replay", ...} a quest played through to where it stands (replay() in Game.cpp)
//     {"command": "questions"}   every question, so their answers can be checked by running them
//
// The program keeps nothing between runs. A quest is its random seed plus the moves made so far, and
// every replay plays it again from the start, which always ends in the same place.
#include <exception>
#include <iostream>
#include <iterator>
#include <sstream>
#include <string>

#include "Answers.hpp"
#include "Game.hpp"
#include "Json.hpp"

namespace {

templaria::QuestRequest quest_request(const json::Value& root) {
    templaria::QuestRequest request;
    request.name = root.at("name").as_string();
    request.difficulty = root.at("difficulty").as_string();
    request.seed = root.at("seed").as_integer();
    for (const json::Value& move : root.at("moves").items()) request.moves.push_back(move.as_string());
    request.carried = static_cast<int>(root.at("carried").as_integer());
    if (const json::Value& only = root.at("onlyPath"); !only.is_null()) request.only_path = only.as_string();
    for (const json::Value& number : root.at("skipQuestions").items())
        request.skip_questions.push_back(static_cast<int>(number.as_integer()));
    request.version = static_cast<int>(root.at("version").as_integer());
    request.is_final = root.at("final").as_bool();
    return request;
}

}  // namespace

int main() {
    try {
        const std::string input{std::istreambuf_iterator<char>(std::cin), std::istreambuf_iterator<char>()};
        const json::Value root = json::Value::parse(input);
        const std::string& command = root.at("command").as_string();

        // Everything goes to a buffer first, so a failure part way can't send half an answer.
        std::ostringstream answer;
        json::Writer writer(answer);
        if (command == "info") {
            templaria::write_info(writer);
        } else if (command == "replay") {
            templaria::write_quest(writer, templaria::replay(quest_request(root)));
        } else if (command == "questions") {
            templaria::write_questions(writer);
        } else {
            std::cerr << "Unknown command\n";
            return 2;
        }
        std::cout << answer.str();
    } catch (const std::exception& error) {
        std::cerr << error.what() << '\n';
        return 2;
    }
    return 0;
}
