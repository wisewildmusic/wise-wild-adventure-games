#include "Answers.hpp"

#include <string>

namespace templaria {
namespace {

void write_prompt(json::Writer& json, const std::optional<Prompt>& prompt) {
    if (!prompt) {
        json.null();
        return;
    }
    const auto* challenge = std::get_if<Challenge>(&*prompt);
    json.begin_object();
    json.key("kind").string(challenge ? "question" : "choice");
    json.key("moves").begin_array();
    for (const std::string& move : prompt_moves(*prompt)) json.string(move);
    json.end_array();
    json.key("options").begin_array();
    if (challenge) {
        for (std::size_t i = 0; i < challenge->options.size(); ++i) {
            json.begin_array();
            json.string(letters[i]);
            json.string(challenge->options[i]);
            json.end_array();
        }
    } else {
        for (const std::string& option : std::get<Choice>(*prompt).options) json.string(option);
    }
    json.end_array();
    if (challenge) {
        json.key("challenger").string(challenge->challenger);
        json.key("prompt").string(challenge->question->prompt);
        json.key("code").optional_string(challenge->question->code);
    }
    json.end_object();
}

void write_question(json::Writer& json, const Question& question) {
    json.begin_object();
    json.key("prompt").string(question.prompt);
    json.key("code").optional_string(question.code);
    json.key("options").begin_array();
    for (const std::string& option : question.options) json.string(option);
    json.end_array();
    json.key("answer").string(question.answer);
    json.key("explain").string(question.explain);
    json.key("compileError").optional_string(question.compile_error);
    json.key("undefined").optional_string(question.undefined);
    json.end_object();
}

}  // namespace

void write_info(json::Writer& json) {
    json.begin_object();
    json.key("gameVersion").number(rules::game_version);
    json.key("questionCounts").begin_object();
    for (const auto& [version, count] : rules::question_counts()) json.key(std::to_string(version)).number(count);
    json.end_object();
    json.key("levels").begin_array();
    for (const Level& level : rules::levels()) {
        json.begin_object();
        json.key("key").string(level.key);
        json.key("lives").number(level.lives);
        json.key("multiplier").number(level.multiplier);
        json.key("topics").string(level.topics);
        json.end_object();
    }
    json.end_array();
    json.key("paths").begin_array();
    for (const GamePath& path : rules::paths()) {
        json.begin_object();
        json.key("key").string(path.key);
        json.key("label").string(path.label);
        json.key("name").string(path.name);
        json.end_object();
    }
    json.end_array();
    json.key("scenes").begin_object();
    for (const auto& [key, scene] : rules::scenes()) {
        json.key(key).begin_array();
        json.string(scene.banner);
        json.string(scene.picture);
        json.string(scene.description);
        json.end_array();
    }
    json.end_object();
    json.key("dragonMove").string(rules::dragon_move);
    json.key("dragonPoints").number(rules::dragon_points);
    json.key("bossMove").string(rules::boss_move);
    json.key("bossPoints").number(rules::boss_points);
    json.key("texts").begin_object();
    for (const auto& [key, text] : rules::texts()) json.key(key).string(text);
    json.key("intro").begin_array();
    for (const std::string& paragraph : rules::intro()) json.string(paragraph);
    json.end_array();
    json.end_object();
    json.end_object();
}

void write_quest(json::Writer& json, const Quest& quest) {
    json.begin_object();
    json.key("scene").string(quest.scene);
    json.key("result").optional_string(quest.result);
    json.key("player").begin_object();
    json.key("name").string(quest.name);
    json.key("difficulty").string(quest.difficulty);
    json.key("lives").number(quest.lives);
    json.key("score").number(quest.score);
    json.key("inventory").begin_array();
    for (const std::string& relic : quest.inventory) json.string(relic);
    json.end_array();
    json.end_object();
    json.key("log").begin_array();
    for (const auto& [kind, text] : quest.log) {
        json.begin_array();
        json.string(kind);
        json.string(text);
        json.end_array();
    }
    json.end_array();
    json.key("asked").begin_array();
    for (const int number : quest.asked) json.number(number);
    json.end_array();
    json.key("path").optional_string(quest.path);
    json.key("dragon").optional_string(quest.dragon);
    json.key("boss").optional_string(quest.boss);
    const Dragon* dragon = quest.dragon_awaits();
    json.key("dragonAwaits").optional_string(dragon ? std::optional(dragon->scene) : std::nullopt);
    json.key("bossAwaits").boolean(quest.boss_awaits());
    json.key("prompt");
    write_prompt(json, quest.prompt);
    json.end_object();
}

void write_questions(json::Writer& json) {
    json.begin_object();
    json.key("levels").begin_object();
    for (const Level& level : rules::levels()) {
        json.key(level.key).begin_array();
        for (const Question& question : level_questions(level.key)) write_question(json, question);
        json.end_array();
    }
    json.end_object();
    json.key("dragons").begin_array();
    for (const Dragon& dragon : rules::dragons()) {
        json.begin_object();
        json.key("level").string(dragon.level);
        json.key("path").string(dragon.path);
        json.key("scene").string(dragon.scene);
        json.key("question");
        write_question(json, dragon_question(dragon.level, dragon.path));
        json.end_object();
    }
    json.end_array();
    json.key("boss").begin_array();
    for (const Question& question : boss_questions()) write_question(json, question);
    json.end_array();
    json.end_object();
}

}  // namespace templaria
