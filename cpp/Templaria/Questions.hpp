#pragma once

#include <optional>
#include <string>
#include <vector>

namespace templaria {

/// A C++ challenge: its options, the correct one (which must match an option exactly) and a short
/// explanation. tools/check-cpp-questions.py compiles and runs every snippet and checks each answer
/// against what really happens, using these two for the answers a program can't print:
///   compile_error  when the answer is that the snippet doesn't compile: MSVC's error code for it
///   undefined      when the answer is undefined behavior: what the sanitizers must catch it doing
struct Question {
    std::string prompt;
    std::optional<std::string> code;
    std::vector<std::string> options;
    std::string answer;
    std::string explain;
    std::optional<std::string> compile_error;
    std::optional<std::string> undefined;
};

const std::vector<Question>& level_questions(const std::string& level);
const Question& dragon_question(const std::string& level, const std::string& path);
const std::vector<Question>& boss_questions();

}  // namespace templaria
