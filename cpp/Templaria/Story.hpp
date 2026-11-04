#pragma once

#include "Game.hpp"
#include "Generator.hpp"

namespace templaria {

Generator<Prompt> start_game(Quest& q);
Generator<Prompt> dragon_battle(Quest& q);
Generator<Prompt> boss_battle(Quest& q);

}  // namespace templaria
