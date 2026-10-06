# Backyard Patrol

You are Biscuit, a dog with one job: keep the backyard safe. Squirrels hop the
fence and make off with the flowers, gophers tunnel in from below, and when
night falls a raccoon comes sniffing around the trash cans. Atari 2600 looks,
single-screen arcade play, running entirely inside your terminal.

<p align="center">
<img width="568" height="422" alt="backyard_patrol" src="https://github.com/user-attachments/assets/28fbff47-217a-49f3-8a12-8f457811652e" />
</p>

```bash
./play.sh
```

or `python3 -m patrol` from this folder. Needs Python 3 (ships with macOS) and
a terminal at least 64 columns by 24 rows. A 256-colour terminal gives the full
palette; 8-colour terminals still work. Hold a key to keep running; a fast
key-repeat rate in your OS settings makes the dog feel snappier.

## The game

The yard is one screen: a fence on three sides, the house along the bottom with
a back door and a lit kitchen window, a tree in the corner, your doghouse, two
trash cans and four flowerbeds with three flowers each. Twelve flowers. When
they are all gone, the game is over.

- **Barking.** Space barks. Every intruder inside the bark's reach (a wide
  oval around the dog) turns tail and runs for the fence. Each bark spends one
  breath from the BARK meter in the HUD. Run out and all you can do is wheeze.
- **Treats.** The owner tosses biscuits (`o=o`) out of the kitchen window every
  so often, more often when you are out of breath. Catch one to recharge two
  breaths. Squirrels and raccoons like biscuits too, and a biscuit left lying
  around does not stay around.
- **Tackling.** Running straight into an intruder chases it off as well, for a
  bonus, and it always works. Barking is for when you cannot get there in time.
- **Squirrels** come over the back fence, down the tree or along the sides,
  zigzag to a flowerbed, dig up a flower and run for the nearest fence with it.
  Scare a squirrel while it is carrying something and it drops it. Walk over a
  dropped flower to replant it in the nearest bed with room.
- **Gophers** tunnel in. You can see the mound moving across the lawn, and the
  dirt trail behind it. Underground they cannot hear you, so stand on the mound
  to dig them out, or wait until they surface in a flowerbed and bark. Gophers
  do not leave on their own: they eat one flower after another until chased.
- **Raccoons** show up on every third day, at night (the lawn goes dark), and
  occasionally sneak in during the day later on. They go for treats first, then
  the trash cans, then the flowers. One bark only makes a raccoon hiss and back
  off; bark again, or tackle it. If it reaches a trash can it tips it over, which
  costs you points and leaves a mess until morning.
- **Days.** Each day sends a set number of intruders. When they have all been
  chased or have escaped, the day ends: bonus points for every flower still
  standing, one breath back, and the owner replants one flower. Later days are
  faster, with more and bolder intruders.

The high score is saved to `highscore.json` in this folder.

## Controls

| Key | Action |
| --- | --- |
| Arrows / WASD | Run |
| Space / F / B | Bark |
| P | Pause |
| ? | How to play |
| Q / Esc | Quit (asks first) |

## Layout

```
patrol/
  constants.py   layout, tuning, palette, sprites, block font, owner chatter
  world.py       the yard: flowerbeds, tree, doghouse, trash cans, house
  entities.py    Dog, Bed, TrashCan, Squirrel, Gopher, Raccoon, Item, Bark, particles
  render.py      curses drawing: HUD, yard, sprites, bark rings, overlays
  engine.py      game loop, input, dog movement, barking, critter AI, days, scoring
  __main__.py    entry point
highscore.json   created after your first game
```

Tuning lives at the top of `constants.py`: the dog's speed, the bark's reach
and meter size, how often treats come, and how fast each critter moves and
digs. Day scaling is in `day_scale` and `work_scale` in `engine.py`. To move a
flowerbed, edit `BEDS` in `world.py`.
