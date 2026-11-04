#pragma once

#include "Game.hpp"
#include "Json.hpp"

// The program's JSON answers.
namespace templaria {

void write_info(json::Writer& json);
void write_quest(json::Writer& json, const Quest& quest);
void write_questions(json::Writer& json);

}  // namespace templaria
