// The adventure itself. Each part of the story is a C++20 coroutine: `co_yield` hands the page a prompt,
// and the story carries on from there with the explorer's move in q.move. A range-based for with a
// `co_yield` in it walks through a smaller part of the story. A part that has an outcome leaves it in
// q.passed.
//
// A coroutine outlives the call that started it, so its parameters must too. A reference parameter that
// was bound to a temporary would dangle at the first co_yield, which is why every string here is taken
// by value. The Quest is taken by reference because replay() keeps it alive for the whole story.
#include "Story.hpp"

#include <algorithm>
#include <format>
#include <iterator>
#include <numeric>
#include <string>
#include <vector>

namespace templaria {
namespace {

// ------------------------------------------------------------------
// Helpers
// ------------------------------------------------------------------

template <typename... Options>
Prompt choose(Options... options) {
    return Choice{{std::string(options)...}};
}

void add_points(Quest& q, int base_points, const std::string& reason) {
    const int points = base_points * rules::level(q.difficulty).multiplier;
    q.score += points;
    q.note("points", std::format("+{} points ({})", points, reason));
}

/// Takes away one life. Returns true if the explorer still has lives left.
bool lose_life(Quest& q) {
    --q.lives;
    q.note("life", q.lives > 0 ? std::format("You lose a life! Lives remaining: {}", q.lives) : "You have no lives left!");
    return q.lives > 0;
}

void collect_relic(Quest& q, const std::string& relic) {
    q.inventory.push_back(relic);
    q.note("relic", std::format("You found a relic: {}!", relic));
}

/// The next question from the explorer's deck, reshuffling when it runs out. A path not taken yet starts
/// with a deck of the questions the level's earlier paths didn't ask. A quest asks at most 6, so a
/// level's 20 questions are enough for all three paths.
const Question& draw_question(Quest& q) {
    if (q.deck.empty()) {
        std::vector<int> every(rules::question_counts().at(q.version));
        std::iota(every.begin(), every.end(), 0);
        std::vector<int> unasked;
        if (q.asked.empty())
            std::ranges::copy_if(every, std::back_inserter(unasked), [&](int n) { return !q.skip_questions.contains(n); });
        q.deck = unasked.empty() ? every : unasked;
        shuffle(q.rng, q.deck);
    }
    const int number = q.deck.back();
    q.deck.pop_back();
    q.asked.push_back(number);
    return level_questions(q.difficulty).at(number);
}

/// Asks one C++ question: the next from the deck, or `given` (a dragon's or the boss's). Leaves q.passed
/// true if the answer is right, and earns `points`.
Generator<Prompt> ask_question(Quest& q, std::string challenger, const Question* given = nullptr,
                               int points = rules::correct_answer_points, std::string reason = "correct answer") {
    const Question& question = given ? *given : draw_question(q);
    std::vector<std::string> options = question.options;
    shuffle(q.rng, options);

    co_yield Challenge{challenger, &question, options};

    const std::string& correct_letter = letters[std::ranges::find(options, question.answer) - options.begin()];
    q.passed = q.move == correct_letter;
    if (q.passed) {
        q.note("correct", "Correct!");
        add_points(q, points, reason);
    } else {
        q.note("wrong", std::format("{}) {}", correct_letter, question.answer));
    }
    q.note("why", question.explain);
}

/// Asks questions until one is answered correctly. Each wrong answer costs a life. Leaves q.passed false
/// if the explorer runs out of lives.
Generator<Prompt> face_challenge(Quest& q, std::string challenger) {
    while (true) {
        for (auto& prompt : ask_question(q, challenger)) co_yield prompt;
        if (q.passed) co_return;
        if (!lose_life(q)) co_return;
        q.note("info", std::format("{} gives you another chance...", challenger));
    }
}

void game_over(Quest& q, const std::string& message) {
    q.narrate(message);
    q.banner("game_over");
    q.result = "lose";
}

void victory(Quest& q) {
    q.banner("victory");
    q.narrate(std::format(
        "The vault door swings open with a groan. Inside, resting on a pedestal of black stone, sits the legendary "
        "Golden Pointer, a glowing orb in a serpent's coils, still pointing true after all these years. "
        "Congratulations, {}! Your name will be carved among the great coders of Templaria.", q.name));
    add_points(q, rules::treasure_points, "found the pointer");
    for (const std::string& relic : q.inventory)
        add_points(q, rules::relic_points, std::format("relic: {}", relic));
    add_points(q, rules::life_points * q.lives, std::format("lives remaining: {}", q.lives));
    q.result = "win";
}

// ------------------------------------------------------------------
// The temple and the end of the quest
// ------------------------------------------------------------------

Generator<Prompt> temple_vault(Quest& q) {
    q.banner("temple");
    q.narrate("Torches burst into flame as you enter the temple's great hall. At the far end stands the vault, held "
              "shut by two locks, Compile and Link, each in the coils of a stone serpent: trophies, they say, taken "
              "from a rival language. Beside the path sits a small jeweled chest with a riddle carved into its lid. "
              "Solving it would earn you a rare relic, but a wrong answer will cost you a life.");
    co_yield choose("Try to open the jeweled chest", "Ignore the chest and head for the vault");
    if (q.move == "1") {
        for (auto& prompt : ask_question(q, "The Jeweled Chest")) co_yield prompt;
        if (q.passed) {
            q.narrate("Click! The lid springs open, revealing a ring set with a blazing garnet.");
            collect_relic(q, "Garnet Ring");
        } else {
            if (!lose_life(q)) {
                game_over(q, "A dart coated in sleeping venom shoots from the lock. You doze off just steps away from "
                             "the pointer...");
                co_return;
            }
            q.narrate("A tiny dart shoots from the lock and stings your hand. The chest stays shut.");
        }
    } else {
        q.narrate("You leave the chest alone. Sometimes the wisest move is not to dereference at all.");
    }

    q.narrate("You approach the vault door. The eyes of the stone serpents begin to glow.");
    for (const std::string lock_name : {"Compile", "Link"}) {
        for (auto& prompt : face_challenge(q, std::format("The {} Lock", lock_name))) co_yield prompt;
        if (!q.passed) {
            game_over(q, std::format("{} failed. The serpent's eyes flash red and the vault seals itself forever. The "
                                     "pointer remains lost.", lock_name));
            co_return;
        }
        q.note("info", std::format("The {} Lock slides open!", lock_name));
    }
    victory(q);
}

// ------------------------------------------------------------------
// The forest
// ------------------------------------------------------------------

Generator<Prompt> stream_route(Quest& q) {
    q.banner("waterfall");
    q.narrate("You follow the stream until it plunges over a cliff in a roaring waterfall, the Falls of cout, where "
              "everything in the forest is sent on its way, one chevron at a time. The water swirls, rises, and takes "
              "the shape of a towering figure: the Stream Spirit. \"None may pass until they have been flushed,\" it "
              "booms.");
    for (auto& prompt : face_challenge(q, "The Stream Spirit")) co_yield prompt;
    if (!q.passed) {
        game_over(q, "The Stream Spirit flushes you. A great wave sweeps you downstream, far away from the pointer.");
        co_return;
    }

    q.narrate("The Stream Spirit bows and places a shimmering pearl in your hand.");
    collect_relic(q, "Chevron Pearl");
    q.narrate("It points a watery finger at a dark gap hidden behind the falls. Nearby, a fallen log covered in slick "
              "green moss stretches across the gorge. It looks like a quicker way across, with no bounds checking of "
              "any kind.");
    co_yield choose("Slip behind the falls, as the Stream Spirit showed you", "Cross the gorge on the mossy log");
    if (q.move == "1") {
        add_points(q, rules::wise_choice_points, "wise choice");
        q.narrate("Behind the curtain of water, a hidden tunnel leads you straight to the steps of an ancient temple.");
        for (auto& prompt : temple_vault(q)) co_yield prompt;
        co_return;
    }
    game_over(q, "Halfway across, your boot slips past the end of the moss. You tumble into the rapids and are carried "
                 "far from the pointer. Somewhere behind you, the Stream Spirit sighs.");
}

Generator<Prompt> tree_route(Quest& q) {
    q.banner("tree");
    q.narrate("You climb branch by branch, each one inherited from the branch below, until the two great limbs meet "
              "again and you break through the mist. Far to the east, a golden temple roof glints above the jungle. A "
              "great grey owl lands beside you and blinks. \"Hoo! I am the Virtual Owl, and which of me you meet "
              "depends on who you really are. Only those who think like a programmer may learn the safe way down.\"");
    for (auto& prompt : face_challenge(q, "The Virtual Owl")) co_yield prompt;
    if (!q.passed) {
        game_over(q, "The owl ruffles its feathers and flies away. As you reach after it, the branch beneath you "
                     "snaps...");
        co_return;
    }

    q.narrate("\"Well reasoned!\" hoots the owl, and it plucks a feather for you.");
    collect_relic(q, "Virtual Feather");
    q.narrate("\"Now listen closely. The swamp below is the shortest way to the temple, but like a C-style cast, it "
              "asks no questions, and it swallows the careless. The vines are slow, but type-safe.\"");
    co_yield choose("Swing along the vines toward the temple", "Climb down and take the swamp shortcut");
    if (q.move == "1") {
        add_points(q, rules::wise_choice_points, "wise choice");
        q.narrate("Vine by vine, you swing through the canopy like a jungle acrobat and land softly on the temple "
                  "steps.");
        for (auto& prompt : temple_vault(q)) co_yield prompt;
        co_return;
    }
    game_over(q, "Three steps into the swamp, the mud grabs your boots. The harder you struggle, the deeper you sink, "
                 "and nothing ever comes back out. You should have listened to the owl!");
}

Generator<Prompt> forest_path(Quest& q) {
    q.banner("forest");
    q.narrate("Towering trees close in around you, all grown from one pattern and told apart only by the labels "
              "carved into their bark: Tree<Oak>, Tree<Elm>, Tree<Ash>. Nothing here exists until something asks for "
              "it. To your left, a stream murmurs through the ferns, its ripples like little chevrons flowing "
              "downhill. To your right stands the Diamond Tree, its two great limbs parting and then joining again "
              "far above, so tall its top disappears into the mist. From up there, you could see for miles.");
    co_yield choose("Follow the stream", "Climb the Diamond Tree");
    for (auto& prompt : q.move == "1" ? stream_route(q) : tree_route(q)) co_yield prompt;
}

// ------------------------------------------------------------------
// The caverns
// ------------------------------------------------------------------

Generator<Prompt> final_door(Quest& q) {
    q.banner("glyph");
    q.narrate("You weave between the pits until the tunnel ends at a massive stone door, marked final: nothing may "
              "derive from it, and nothing may pass. Glowing letters crawl across its surface and rearrange themselves "
              "into lines of C++.");
    for (auto& prompt : face_challenge(q, "The Final Door")) co_yield prompt;
    if (!q.passed) {
        game_over(q, "The letters flash red. With a deep rumble the tunnel behind you seals shut, and your torch "
                     "flickers out...");
        co_return;
    }

    q.narrate("The letters flash gold and the door grinds open. A small carved tablet falls from the wall at your "
              "feet.");
    collect_relic(q, "Final Tablet");
    q.narrate("Beyond the door the tunnel splits in two. From the left drifts warm air and a faint golden glow. The "
              "right tunnel is cold, its walls marked with fresh, deep claw scratches, and something in there is "
              "growling.");
    co_yield choose("Take the left tunnel toward the golden glow", "Take the right tunnel past the claw marks");
    if (q.move == "1") {
        add_points(q, rules::wise_choice_points, "wise choice");
        q.narrate("The golden glow grows brighter with every step until you emerge at the heart of an ancient temple.");
        for (auto& prompt : temple_vault(q)) co_yield prompt;
        co_return;
    }
    game_over(q, "The claw marks belong to a very large, very grumpy cave bear, and no destructor is coming to clean "
                 "this up. You flee all the way back to the entrance, your quest in ruins.");
}

Generator<Prompt> segfault_pit(Quest& q) {
    q.banner("dark");
    q.narrate("You creep forward in total darkness, one hand on the cold, damp wall, never once checking what's ahead. "
              "You step onto ground that was never mapped, and you tumble into a pit!");
    if (!lose_life(q)) {
        game_over(q, "Segmentation fault (core dumped). The pit is far too deep to climb out of without light. Your "
                     "quest ends here, in the dark.");
        co_return;
    }

    co_yield choose("Climb out of the pit");
    q.narrate("Bruised but alive, you claw your way out and crawl back to the entrance. This time you light the torch. "
              "Lesson learned: never dereference what you haven't checked! In its glow you can see the floor is "
              "riddled with pits.");
    for (auto& prompt : final_door(q)) co_yield prompt;
}

Generator<Prompt> cave_path(Quest& q) {
    q.banner("cave");
    q.narrate("Cold air flows from the mouth of the Heap Caverns. Everything ever left down here is still here: nobody "
              "cleaned it up, and nobody will. Just inside, you find an old torch and a flint. Lighting it would help "
              "you see, but the light might also wake whatever is hissing in the dark...");
    co_yield choose("Light the torch", "Proceed in the dark");
    if (q.move == "1") {
        add_points(q, rules::wise_choice_points, "wise choice");
        q.narrate("The torch flares to life. Good thing, too: the floor ahead is riddled with deep pits, and someone "
                  "has scratched \"nullptr\" beside each one. The hissing, you realize, is only wind whistling through "
                  "cracks in the rock.");
        for (auto& prompt : final_door(q)) co_yield prompt;
        co_return;
    }
    for (auto& prompt : segfault_pit(q)) co_yield prompt;
}

// ------------------------------------------------------------------
// The castle
// ------------------------------------------------------------------

Generator<Prompt> private_gate(Quest& q) {
    q.banner("gate");
    q.narrate("Golden griffins glare down from tattered banners as you reach the gate. The iron portcullis is raised, "
              "but as you step beneath it a ghostly knight in rusted armor drifts out of the stone. \"Halt! This "
              "castle's members are private, and none may pass but a friend. And I,\" it adds sadly, \"was never "
              "declared anyone's friend.\"");
    for (auto& prompt : face_challenge(q, "The Friendless Knight")) co_yield prompt;
    if (!q.passed) {
        game_over(q, "\"Cannot access private member,\" says the knight, and the portcullis crashes down. You are left "
                     "outside in the dark, far from the pointer.");
        co_return;
    }

    q.narrate("The knight lowers its sword and presses a cold silver ring into your palm. \"Friend,\" it says, trying "
              "out the word.");
    collect_relic(q, "Friend Signet");
    q.banner("hall");
    q.narrate("Beyond the gate lies the Hall of Pure Virtuals, its arches broken and open to the sky: all declarations, "
              "and no one left to implement them. Torches flicker beside an empty throne, its seat carved with a "
              "single = 0. Behind it, a narrow passage glows with a faint golden light. To one side, a grand staircase "
              "climbs into the dark, its steps cracked, crumbling and marked [[deprecated]].");
    co_yield choose("Take the glowing passage behind the throne", "Climb the deprecated grand staircase");
    if (q.move == "1") {
        add_points(q, rules::wise_choice_points, "wise choice");
        q.narrate("The passage winds down beneath the castle and comes out on the steps of an ancient temple.");
        for (auto& prompt : temple_vault(q)) co_yield prompt;
        co_return;
    }
    game_over(q, "Halfway up, the staircase gives way beneath your feet. You were warned, and warnings are so easy to "
                 "ignore. You tumble down in a cloud of dust, and Castle Cfront keeps its secrets.");
}

Generator<Prompt> ramparts(Quest& q) {
    q.banner("ramparts");
    q.narrate("You climb onto the Ramparts of noexcept, where nothing may be thrown, and the penalty for throwing is "
              "immediate termination. The moon hangs over a sea of mist and the wind howls between the towers. On the "
              "wall ahead crouches a stone gargoyle. As you come near, its eyes crack open and glow. \"Answer me, "
              "climber. I have promised not to throw you, and I keep my promises, mostly.\"");
    for (auto& prompt : face_challenge(q, "The noexcept Gargoyle")) co_yield prompt;
    if (!q.passed) {
        game_over(q, "The gargoyle breaks its promise and throws. No handler waits below to catch you, and you are "
                     "terminated somewhere in the mist.");
        co_return;
    }

    q.narrate("The gargoyle grinds out a laugh and drops a glittering stone from its claw.");
    collect_relic(q, "Stone of Unwinding");
    q.banner("gallery");
    q.narrate("The ramparts lead into a tall tower and up to a moonlit gallery. Far below the balustrade, a golden "
              "temple roof glints through the mist. Ivy as thick as rope hangs over the edge, and a spiral stair winds "
              "down inside the tower.");
    co_yield choose("Take the spiral stair down inside the tower", "Climb down the ivy from the gallery");
    if (q.move == "1") {
        add_points(q, rules::wise_choice_points, "wise choice");
        q.narrate("Round and round you go, down and down, like a stack unwinding, until a small door at the foot of the "
                  "tower opens beside the temple steps.");
        for (auto& prompt : temple_vault(q)) co_yield prompt;
        co_return;
    }
    game_over(q, "The ivy is older than C itself. It tears loose with a snap, and you drop into the mist far below.");
}

Generator<Prompt> castle_path(Quest& q) {
    q.banner("castle");
    q.narrate("A winding stone trail climbs out of the mist to the ruins of Castle Cfront, where the first coders of "
              "Templaria turned plain old C into something with classes. Torches still burn along the way, though no "
              "one has maintained this place in decades, and all of Templaria still compiles against it. The trail "
              "ends at the Private Gate. Beside it, a crumbling stair climbs the outer wall toward the ramparts.");
    co_yield choose("Follow the torches to the Private Gate", "Climb the crumbling stair to the ramparts");
    for (auto& prompt : q.move == "1" ? private_gate(q) : ramparts(q)) co_yield prompt;
}

// (Not a coroutine itself, having no co_yield: it just hands back the one that was asked for.)
Generator<Prompt> chosen_path(Quest& q) {
    if (*q.path == "forest") return forest_path(q);
    if (*q.path == "cave") return cave_path(q);
    return castle_path(q);
}

}  // namespace

// ------------------------------------------------------------------
// The start
// ------------------------------------------------------------------

Generator<Prompt> start_game(Quest& q) {
    q.banner("start");
    std::size_t chosen;
    if (q.only_path) {
        // A winner going back for a path they didn't take, score and all.
        const auto& paths = rules::paths();
        const auto path = std::ranges::find(paths, *q.only_path, &GamePath::key);
        const std::string fresh = q.skip_questions.empty() ? "" : ", where new riddles await";
        q.narrate(std::format("Welcome back, {}! You return to the edge of Templaria with {} points from your last "
                              "quest, wondering what waits down the way you didn't take. This time you turn toward {}{}.",
                              q.name, q.carried, path->sight, fresh));
        co_yield choose(path->label);
        chosen = path - paths.begin();
    } else {
        constexpr auto three_paths =
            "the Template Forest, where every tree grows from the same pattern; the Heap Caverns, where whatever is "
            "left behind stays forever; and a torch-lit trail that climbs to the ruins of Castle Cfront.";
        if (q.carried > 0) {
            // A winner carrying their score up to the next level.
            q.narrate(std::format("Welcome back, {}! You return to the edge of Templaria with {} points from your last "
                                  "quest. Word of your success has reached the guardians, and their riddles will be "
                                  "harder this time. Three paths lie before you once more: {}",
                                  q.name, q.carried, three_paths));
        } else {
            q.narrate(std::format("Welcome, {}! You arrive at the edge of Templaria with nothing but a backpack and a "
                                  "strong sense of ownership. Three paths lie before you: {}",
                                  q.name, three_paths));
        }
        std::vector<std::string> labels;
        for (const GamePath& path : rules::paths()) labels.push_back(path.label);
        co_yield Choice{labels};
        chosen = std::stoul(q.move) - 1;
    }
    q.path = rules::paths()[chosen].key;
    for (auto& prompt : chosen_path(q)) co_yield prompt;
}

// ------------------------------------------------------------------
// The bonus dragons, and the final boss
// ------------------------------------------------------------------

/// The bonus after a win: the riddle of the dragon of this path and level. Right, a share of its treasure;
/// wrong, nothing lost. The quest stays won whatever the answer.
Generator<Prompt> dragon_battle(Quest& q) {
    const Dragon& dragon = *rules::find_dragon(q.difficulty, *q.path);
    const std::string& name = rules::scenes().at(dragon.scene).banner;
    q.banner(dragon.scene);
    q.narrate(std::format("{} There, coiled around an overflowing treasure chest, sleeps the {}, its scales {}. As you "
                          "creep closer, one great eye slides open. \"A riddle, little coder,\" it rumbles. \"Answer "
                          "well, and a share of my treasure is yours. Answer badly, and run.\"",
                          std::ranges::find(rules::paths(), *q.path, &GamePath::key)->lair,
                          name.substr(std::string("The ").size()), dragon.scales));
    for (auto& prompt : ask_question(q, name, &dragon_question(q.difficulty, *q.path), rules::dragon_points, "the dragon's treasure"))
        co_yield prompt;
    if (q.passed) {
        q.dragon = "won";
        q.narrate("The dragon rumbles a deep laugh and nudges its chest toward you with its snout. You fill your pockets "
                  "with treasure and slip away.");
    } else {
        q.dragon = "lost";
        q.narrate("The dragon snorts a cloud of smoke, and you flee, empty-handed but unharmed.");
    }
}

/// The final boss, for a winner who has completed every path on every level: one of the nine ultimate
/// questions, picked at random. Right: the title of C++ Master and boss_points besides. Wrong: all is
/// lost, the score falls to zero.
Generator<Prompt> boss_battle(Quest& q) {
    q.banner("boss");
    q.narrate("You have walked every path in Templaria. As you leave the temple for the last time, the torches begin to "
              "burn upside down. The stones under your boots lift off the ground, each one stamped 0xDEADBEEF, and the "
              "sky tears open into static and blue lightning. Something vast pulls itself together out of everything "
              "that was ever read after it was freed: a horned demon that can't settle on a shape, half cracked stone "
              "and half purple static, with one blue eye and one magenta. Broken chains of arrows trail from its arms, "
              "each one pointing at nothing, a cracked C++ burns on its chest, and small winged demons pour from its "
              "nostrils. \"Every path, every level,\" it says, in several voices, not all of them from now. \"I am what happens when the rules are broken. The standard says nothing about me, so "
              "I may do anything at all. One question remains. Answer it, and you are a C++ Master. Fail, and I owe "
              "you no explanation.\"");
    const std::vector<Question>& questions = boss_questions();
    const Question& question = questions[q.rng.next(static_cast<int>(questions.size()))];
    for (auto& prompt : ask_question(q, rules::boss_name, &question, rules::boss_points, "C++ Master")) co_yield prompt;
    if (q.passed) {
        q.boss = "won";
        q.narrate("The demon stops in mid-flicker, and for one moment it has only one shape. \"Well-defined,\" it says, "
                  "as though the word tastes strange. \"Well answered, Master.\" The torches burn upright again. From "
                  "this day on, the coders of Templaria will know you by your new title.");
        q.note("relic", "You are a C++ Master!");
    } else {
        q.boss = "lost";
        q.score = 0;
        q.narrate("The standard places no requirements on what happens next. Every coin, relic and point you carried is "
                  "gone, and it's possible they never existed. You wake at the edge of Templaria with nothing but a "
                  "backpack and a strong sense of ownership.");
        q.note("life", "All is lost! Your score falls to 0.");
    }
}

}  // namespace templaria
