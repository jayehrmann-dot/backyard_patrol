"""Game loop, input, the dog, barking, critter AI, treats, days and scoring."""
import curses
import json
import math
import os
import random
import time
from collections import deque

from .constants import (
    FPS, TICK, FENCE_Y, LAWN_TOP, LAWN_BOT, FENCE_L, FENCE_R, LAWN_LEFT, LAWN_RIGHT,
    DOG_VX, DOG_VY, MOVE_HOLD, BARK_MAX, BARK_RX, BARK_RY, BARK_COOLDOWN, BARK_RING_TICKS,
    BARK_REGEN, TREAT_BARK, TREAT_EVERY, TREAT_HUNGRY_EVERY, TREAT_AIR, TREAT_LIFE, FLOWER_LIFE,
    SQUIRREL_DIG, GOPHER_EAT, RACCOON_DIG, RACCOON_RAID, RACCOON_STUN, POP_STUN, FULL_BELLY,
    BANNER_TICKS, SCORE, WOOF, HEART,
    LINES_TREAT, LINES_SQUIRREL, LINES_GOPHER, LINES_RACCOON, LINES_LOST, LINES_STOLEN,
    LINES_DAY, LINES_NIGHT, LINES_IDLE,
)
from .world import World, TREE_SPAWN, TOSS_FROM, DOG_START
from .entities import (
    Dog, Squirrel, Gopher, Raccoon, Item, Bark, Particle, FloatText,
    clamp, sign, dist, overlap, rects_overlap,
)

HIGH_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "highscore.json")

KEYS_UP = (curses.KEY_UP, ord("w"), ord("W"), ord("k"), ord("K"))
KEYS_DOWN = (curses.KEY_DOWN, ord("s"), ord("S"), ord("j"), ord("J"))
KEYS_LEFT = (curses.KEY_LEFT, ord("a"), ord("A"), ord("h"), ord("H"))
KEYS_RIGHT = (curses.KEY_RIGHT, ord("d"), ord("D"), ord("l"), ord("L"))
KEYS_BARK = (ord(" "), ord("f"), ord("F"), ord("b"), ord("B"))
ESC = 27


class Game:
    def __init__(self, stdscr, renderer=None):
        self.stdscr = stdscr
        if renderer is None:
            from .render import Renderer
            renderer = Renderer(stdscr)
        self.r = renderer
        self.rng = random.Random()
        self.world = World()
        self.high = self.load_high()
        self.running = True
        self.mode = "title"
        self.prev_mode = "title"
        self.tick = 0
        self.title_t = 0
        self.messages = deque(maxlen=2)
        self.msg_expire = 0
        self.reset_state()

    # ------------------------------------------------------------ setup
    def reset_state(self):
        self.score = 0
        self.day = 0
        self.night = False
        self.world.reset()
        self.dog = Dog(*DOG_START)
        self.critters = []
        self.items = []
        self.barks = []
        self.particles = []
        self.texts = []
        self.mess = []
        self.quota = {"squirrel": 0, "gopher": 0, "raccoon": 0}
        self.spawned = {"squirrel": 0, "gopher": 0, "raccoon": 0}
        self.spawn_t = 0
        self.treat_t = self.rng.randint(*TREAT_EVERY)
        self.banner_t = 0
        self.banner = ""
        self.idle_t = FPS * 12
        self.escaped = 0
        self.chased = 0
        self.messages.clear()

    def load_high(self):
        try:
            with open(HIGH_PATH) as f:
                return int(json.load(f).get("high", 0))
        except (OSError, ValueError):
            return 0

    def save_high(self):
        if self.score > self.high:
            self.high = self.score
        try:
            with open(HIGH_PATH, "w") as f:
                json.dump({"high": self.high}, f)
        except OSError:
            pass

    # ------------------------------------------------------------ messages
    def say(self, text, kind="msg", secs=5):
        self.messages.append((text, kind))
        self.msg_expire = self.tick + int(secs * FPS)
        self.idle_t = FPS * 15

    def chatter(self, lines, kind="msg", secs=4, chance=1.0):
        if self.rng.random() <= chance:
            self.say(self.rng.choice(lines), kind, secs)

    def flowers_left(self):
        return self.world.flowers()

    def intruders_left(self):
        return sum(self.quota.values()) - sum(self.spawned.values()) + len(self.critters)

    # ------------------------------------------------------------ main loop
    def run(self):
        self.stdscr.nodelay(True)
        self.stdscr.keypad(True)
        try:
            curses.curs_set(0)
        except curses.error:
            pass
        next_t = time.time()
        while self.running:
            self.handle_input()
            self.step()
            self.r.draw(self)
            next_t += TICK
            delay = next_t - time.time()
            if delay > 0:
                time.sleep(delay)
            else:
                next_t = time.time()

    def step(self):
        """One simulation tick (also used headless by the tests)."""
        self.tick += 1
        if self.mode == "title":
            self.title_t += 1
        elif self.mode in ("play", "clear"):
            self.update()
        if self.messages and self.tick > self.msg_expire:
            self.messages.clear()

    def handle_input(self):
        while True:
            k = self.stdscr.getch()
            if k == -1:
                break
            if k == curses.KEY_RESIZE:
                continue
            getattr(self, "keys_" + self.mode)(k)

    # ------------------------------------------------------------ key handlers
    def keys_title(self, k):
        if k in (ord("n"), ord("N"), 10, 13, ord(" ")):
            self.start_new()
        elif k == ord("?"):
            self.prev_mode = "title"
            self.mode = "help"
        elif k in (ord("q"), ord("Q"), ESC):
            self.running = False

    def keys_help(self, k):
        if k != -1:
            self.mode = self.prev_mode

    def keys_pause(self, k):
        if k in (ord("p"), ord("P"), ESC, ord(" ")):
            self.mode = "play"
        elif k in (ord("q"), ord("Q")):
            self.mode = "quit"
        elif k == ord("?"):
            self.prev_mode = "pause"
            self.mode = "help"

    def keys_quit(self, k):
        if k in (ord("y"), ord("Y")):
            self.save_high()
            self.running = False
        elif k != -1:
            self.mode = "play"

    def keys_gameover(self, k):
        if k in (ord("n"), ord("N"), 10, 13, ord(" ")):
            self.start_new()
        elif k in (ord("q"), ord("Q"), ESC):
            self.running = False

    def keys_clear(self, k):
        self.keys_play(k)

    def keys_play(self, k):
        d = self.dog
        if k in KEYS_UP:
            d.my, d.my_t = -1, MOVE_HOLD
        elif k in KEYS_DOWN:
            d.my, d.my_t = 1, MOVE_HOLD
        elif k in KEYS_LEFT:
            d.mx, d.mx_t, d.facing = -1, MOVE_HOLD, -1
        elif k in KEYS_RIGHT:
            d.mx, d.mx_t, d.facing = 1, MOVE_HOLD, 1
        elif k in KEYS_BARK:
            self.bark()
        elif k in (ord("p"), ord("P")):
            self.mode = "pause"
        elif k == ord("?"):
            self.prev_mode = "play"
            self.mode = "help"
        elif k in (ord("q"), ord("Q"), ESC):
            self.mode = "quit"

    # ------------------------------------------------------------ game flow
    def start_new(self):
        self.reset_state()
        self.mode = "play"
        self.say("Owner: Biscuit, you're on patrol. Keep the squirrels out!", "msg_good", 6)
        self.start_day(1)

    def start_day(self, n):
        self.day = n
        self.night = n % 3 == 0
        self.quota = {
            "squirrel": min(3 + n, 14),
            "gopher": min(n // 2, 5),
            "raccoon": (1 + n // 6) if self.night else (1 if n >= 5 and self.rng.random() < 0.25 else 0),
        }
        self.spawned = {"squirrel": 0, "gopher": 0, "raccoon": 0}
        self.spawn_t = BANNER_TICKS + 15
        self.banner = "DAY %d" % n
        self.banner_t = BANNER_TICKS
        self.mode = "play"
        for c in self.world.cans:
            c.tipped = False
        self.mess = []
        if n > 1:
            self.chatter(LINES_NIGHT if self.night else LINES_DAY, "msg_alert" if self.night else "msg", 5)

    def day_cleared(self):
        flowers = self.flowers_left()
        bonus = 20 * self.day * flowers
        self.add_score(bonus)
        self.banner = "DAY %d DONE" % self.day
        self.banner_t = BANNER_TICKS
        self.mode = "clear"
        self.dog.bark = min(BARK_MAX, self.dog.bark + 1)
        regrown = ""
        room = self.world.beds_with_room()
        if room:
            bed = self.rng.choice(room)
            bed.slots[self.rng.choice(bed.empty())] = True
            regrown = " One flower replanted."
        self.say("Yard secured! %d flowers safe, bonus %d.%s" % (flowers, bonus, regrown), "msg_good", 5)

    def add_score(self, n):
        self.score = max(0, self.score + n)

    def game_over(self, why):
        self.mode = "gameover"
        self.banner = why
        self.save_high()

    # ------------------------------------------------------------ the dog
    def update_dog(self):
        d = self.dog
        w = self.world
        if d.bark_cool > 0:
            d.bark_cool -= 1
        if d.woof_t > 0:
            d.woof_t -= 1
        d.regen_t -= 1
        if d.regen_t <= 0:
            d.regen_t = BARK_REGEN
            if d.bark < BARK_MAX:
                d.bark += 1
        nx, ny = d.x, d.y
        if d.mx_t > 0:
            d.mx_t -= 1
            nx = d.x + d.mx * DOG_VX
        if d.my_t > 0:
            d.my_t -= 1
            ny = d.y + d.my * DOG_VY
        nx = clamp(nx, LAWN_LEFT, LAWN_RIGHT - d.w + 1)
        ny = clamp(ny, LAWN_TOP, LAWN_BOT - d.h + 1)
        if not w.blocked(int(nx), int(d.y), d.w, d.h):
            d.x = nx
        if not w.blocked(int(d.x), int(ny), d.w, d.h):
            d.y = ny
        if d.moving():
            d.anim += 1
            if self.tick % 5 == 0:
                tx = d.x + d.w if d.facing < 0 else d.x - 1
                self.particles.append(Particle(tx, d.y + 1, -d.facing * 0.2, 0.0, 6, "·", "dust"))

    def bark(self):
        d = self.dog
        if d.bark_cool > 0 or self.mode not in ("play", "clear"):
            return
        if d.bark <= 0:
            d.bark_cool = 12
            d.woof_t = 10
            d.woof = "...wheeze"
            self.say("Out of breath! Catch a treat to recharge your bark.", "msg_alert", 3)
            return
        d.bark -= 1
        d.bark_cool = BARK_COOLDOWN
        d.woof_t = 12
        d.woof = self.rng.choice(WOOF)
        cx, cy = d.cx(), d.cy()
        self.barks.append(Bark(cx, cy))
        for c in list(self.critters):
            if not c.scareable():
                continue
            dx = (c.cx() - cx) / BARK_RX
            dy = (c.cy() - cy) / BARK_RY
            if dx * dx + dy * dy <= 1.0:
                self.scare(c, "bark")

    # ------------------------------------------------------------ scaring things off
    def scare(self, c, how):
        if c.kind == "raccoon" and how == "bark":
            c.hits += 1
            if c.hits < c.needed:
                c.stun_t = RACCOON_STUN
                away = sign(c.cx() - self.dog.cx()) or 1
                c.x = clamp(c.x + away * 3, LAWN_LEFT, LAWN_RIGHT - c.w + 1)
                self.texts.append(FloatText(c.x + 1, c.y - 1, "HISS!", "msg_alert"))
                self.say("The raccoon hisses back! Bark again, or tackle it.", "msg_alert", 3)
                return
        pts = SCORE[c.kind] + (SCORE["tackle_bonus"] if how == "tackle" else 0)
        self.add_score(pts)
        self.chased += 1
        self.texts.append(FloatText(c.cx() - 2, c.y - 1, "+%d" % pts, "hud_gold"))
        self.drop_carried(c)
        self.flee(c)
        self.puff(c.cx(), c.cy(), 5)
        lines = {"squirrel": LINES_SQUIRREL, "gopher": LINES_GOPHER, "raccoon": LINES_RACCOON}[c.kind]
        self.chatter(lines, "msg_good", 3, chance=0.45 if c.kind == "squirrel" else 0.8)

    def drop_carried(self, c):
        if c.carrying == "flower":
            it = Item("flower", int(c.cx()), int(c.y), FLOWER_LIFE, c.flower_color)
            self.items.append(it)
            self.say("It dropped the flower! Grab it and bring it back to a bed.", "msg_good", 4)
        elif c.carrying == "treat":
            it = Item("treat", int(c.cx()) - 1, int(c.y), TREAT_LIFE)
            self.items.append(it)
        c.carrying = None

    def flee(self, c):
        self.release_goal(c)
        c.state = "flee"
        c.target = self.nearest_edge(c)
        c.stun_t = 0

    def pop(self, c):
        """The dog dug out a tunnelling gopher."""
        c.state = "popped"
        c.stun_t = POP_STUN
        self.release_goal(c)
        self.add_score(SCORE["pop"])
        self.chased += 1
        self.texts.append(FloatText(c.cx() - 2, c.y - 1, "+%d" % SCORE["pop"], "hud_gold"))
        self.puff(c.cx(), c.y, 8, "dirt")
        self.say("You dug the gopher right out of its tunnel!", "msg_good", 3)

    def release_goal(self, c):
        if c.want == "flower" and c.bed is not None and c.slot is not None:
            c.bed.shake[c.slot] = 0
        c.want = None
        c.bed = None
        c.slot = None
        c.item = None
        c.can = None

    def nearest_edge(self, c):
        opts = [
            ((c.x, FENCE_Y - 1), (c.y - FENCE_Y) * 2.0),
            ((FENCE_L - c.w, c.y), c.x - FENCE_L),
            ((FENCE_R + 1, c.y), FENCE_R - c.x),
        ]
        opts.sort(key=lambda o: o[1])
        return opts[0][0]

    def at_edge(self, c):
        return c.y <= FENCE_Y or c.x + c.w - 1 <= FENCE_L or c.x >= FENCE_R

    # ------------------------------------------------------------ spawning
    def day_scale(self):
        return min(1.5, 1.0 + 0.04 * self.day)

    def work_scale(self):
        return max(0.55, 1.0 - 0.05 * self.day)

    def update_spawns(self):
        if self.banner_t > 0:
            return
        self.spawn_t -= 1
        if self.spawn_t > 0:
            return
        if len(self.critters) >= min(2 + self.day // 2, 6):
            return
        kinds = [k for k in ("squirrel", "gopher", "raccoon") if self.spawned[k] < self.quota[k]]
        if not kinds:
            return
        weights = {"squirrel": 5, "gopher": 2, "raccoon": 1}
        pool = [k for k in kinds for _ in range(weights[k])]
        kind = self.rng.choice(pool)
        self.spawned[kind] += 1
        self.spawn_t = max(50, 150 - self.day * 8)
        self.spawn(kind)

    def spawn(self, kind):
        rng = self.rng
        side = rng.random()
        if kind == "squirrel":
            if side < 0.3:
                c = Squirrel(TREE_SPAWN[0], TREE_SPAWN[1])
            elif side < 0.75:
                c = Squirrel(rng.randint(3, 56), FENCE_Y)
            elif side < 0.875:
                c = Squirrel(FENCE_L - 2, rng.randint(2, 15))
            else:
                c = Squirrel(FENCE_R, rng.randint(2, 15))
        elif kind == "gopher":
            if side < 0.5:
                c = Gopher(rng.randint(3, 56), FENCE_Y)
            elif side < 0.75:
                c = Gopher(FENCE_L - 2, rng.randint(2, 17))
            else:
                c = Gopher(FENCE_R, rng.randint(2, 17))
            self.say("Something is tunnelling under the lawn...", "msg_alert", 3)
        else:
            if side < 0.5:
                c = Raccoon(FENCE_L - 5, rng.randint(2, 15))
            else:
                c = Raccoon(FENCE_R, rng.randint(2, 15))
            c.needed = c.needed + (1 if self.day >= 9 else 0)
            self.say("A raccoon slinks over the fence. It isn't scared of one bark.", "msg_alert", 4)
        c.facing = 1 if c.x < 30 else -1
        self.critters.append(c)

    # ------------------------------------------------------------ critter goals
    def landed_treats(self):
        return [i for i in self.items if i.kind == "treat" and i.landed()]

    def choose_goal(self, c):
        self.release_goal(c)
        treats = self.landed_treats()
        if c.kind == "squirrel":
            near = [t for t in treats if dist(t.cx(), t.cy(), c.cx(), c.cy()) < 26]
            if near and self.rng.random() < 0.6:
                return self.goal_treat(c, near[0])
            return self.goal_flower(c)
        if c.kind == "gopher":
            return self.goal_flower(c)
        # the raccoon: treats first, then the trash cans, then the flowers
        if treats:
            return self.goal_treat(c, treats[0])
        cans = [k for k in self.world.cans if not k.tipped]
        if cans:
            k = self.rng.choice(cans)
            c.want, c.can = "can", k
            c.target = (k.x - c.w + 1 if c.cx() < k.cx() else k.x + k.w, k.y)
            c.state = "go"
            return True
        return self.goal_flower(c)

    def goal_treat(self, c, t):
        c.want, c.item = "treat", t
        c.target = (t.x + 1 - c.w // 2, t.y - (c.h - 1))
        c.state = "go"
        return True

    def goal_flower(self, c):
        beds = self.world.beds_with_flowers()
        if not beds:
            c.state = "leave"
            c.target = self.nearest_edge(c)
            return False
        # prefer nearby beds, but not always
        beds.sort(key=lambda b: dist(b.cx(), b.cy(), c.cx(), c.cy()))
        bed = beds[0] if self.rng.random() < 0.6 or len(beds) == 1 else self.rng.choice(beds[1:])
        slot = self.rng.choice(bed.present())
        c.want, c.bed, c.slot = "flower", bed, slot
        c.target = (bed.slot_x(slot) - c.w // 2, bed.y + 1)
        c.state = "go"
        return True

    def goal_valid(self, c):
        if c.want == "flower":
            return c.bed is not None and c.bed.slots[c.slot]
        if c.want == "treat":
            return c.item in self.items
        if c.want == "can":
            return c.can is not None and not c.can.tipped
        return False

    # ------------------------------------------------------------ critter movement
    def move_toward(self, c, target, speed):
        sx, sy = speed
        tx, ty = target
        dx, dy = tx - c.x, ty - c.y
        if abs(dx) > 0.3:
            c.facing = sign(dx)
        c.x += clamp(dx, -sx, sx)
        c.y += clamp(dy, -sy, sy)
        return abs(dx) <= sx and abs(dy) <= sy

    def scaled(self, speed):
        s = self.day_scale()
        return (speed[0] * s, speed[1] * s)

    def leave_trail(self, c):
        hx, hy = c.head()
        if LAWN_LEFT <= hx <= LAWN_RIGHT and LAWN_TOP <= hy <= LAWN_BOT:
            if not c.trail or (c.trail[-1][0], c.trail[-1][1]) != (hx, hy):
                c.trail.append([hx, hy, 90])
        for t in c.trail:
            t[2] -= 1
        c.trail = [t for t in c.trail if t[2] > 0]

    def update_critter(self, c):
        c.anim += 1
        if c.kind == "gopher":
            self.leave_trail(c)
        if c.stun_t > 0:
            c.stun_t -= 1
            if c.stun_t == 0 and c.state == "popped":
                self.flee(c)
            return

        if c.state == "flee":
            self.move_toward(c, c.target, self.scaled(c.flee_speed))
            if self.at_edge(c):
                self.critters.remove(c)
            return

        if c.state == "leave":
            self.move_toward(c, c.target, self.scaled(c.speed))
            if self.at_edge(c):
                self.escape(c)
            return

        if c.state == "enter":
            self.choose_goal(c)

        if c.state == "go":
            if not self.goal_valid(c):
                if not self.choose_goal(c):
                    return
            target = c.target
            if c.kind == "squirrel":
                # squirrels zigzag until they are close
                if dist(c.x, c.y, target[0], target[1]) > 9:
                    c.hop_t -= 1
                    if c.hop_t <= 0:
                        c.hop_t = 10
                        c.jx = self.rng.choice((-5, 0, 5))
                        c.jy = self.rng.choice((-2, 0, 2))
                    target = (target[0] + c.jx, target[1] + c.jy)
            if self.move_toward(c, target, self.scaled(c.speed)) and target == c.target:
                self.arrive(c)
            return

        if c.state == "work":
            if not self.goal_valid(c):
                self.choose_goal(c)
                return
            c.work_t -= 1
            if c.want == "flower":
                c.bed.shake[c.slot] = 2
            if c.work_t <= 0:
                self.finish_work(c)

    def arrive(self, c):
        c.x, c.y = float(c.target[0]), float(c.target[1])
        c.x = clamp(c.x, LAWN_LEFT, LAWN_RIGHT - c.w + 1)
        c.y = clamp(c.y, LAWN_TOP, LAWN_BOT - c.h + 1)
        if c.want == "treat":
            t = c.item
            if t in self.items:
                self.items.remove(t)
            self.release_goal(c)
            if c.kind == "squirrel":
                c.carrying = "treat"
                c.state = "leave"
                c.target = self.nearest_edge(c)
                self.chatter(LINES_STOLEN, "msg_alert", 4)
            else:
                self.say("The raccoon ate your treat. Sneaky little thief.", "msg_alert", 4)
                self.choose_goal(c)
            return
        c.state = "work"
        ws = self.work_scale()
        if c.want == "can":
            c.work_t = int(RACCOON_RAID * ws)
        elif c.kind == "squirrel":
            c.work_t = int(SQUIRREL_DIG * ws)
        elif c.kind == "gopher":
            c.work_t = int(GOPHER_EAT * ws)
            self.puff(c.cx(), c.y, 6, "dirt")
            self.say("A gopher surfaced in the flowerbed!", "msg_alert", 3)
        else:
            c.work_t = int(RACCOON_DIG * ws)

    def finish_work(self, c):
        if c.want == "can":
            k = c.can
            k.tipped = True
            for i in range(7):
                self.mess.append((k.x - 2 + self.rng.randint(0, 6), k.y + 1 + self.rng.randint(0, 1)))
            self.add_score(SCORE["mess"])
            self.texts.append(FloatText(k.x - 1, k.y - 1, "%d" % SCORE["mess"], "hud_red"))
            self.say("CRASH! The raccoon tipped the trash can. What a mess.", "msg_alert", 4)
            self.puff(k.cx(), k.cy(), 8, "mess")
            self.choose_goal(c)
            return
        bed, slot = c.bed, c.slot
        bed.slots[slot] = False
        bed.shake[slot] = 0
        color = bed.color
        self.release_goal(c)
        if c.kind == "squirrel":
            c.carrying = "flower"
            c.flower_color = color
            c.state = "leave"
            c.target = self.nearest_edge(c)
            self.say("A squirrel pulled up a flower! Don't let it over the fence!", "msg_alert", 4)
        else:
            self.puff(c.cx(), c.y, 6, color)
            c.eaten += 1
            self.say("The %s ate a flower." % c.kind, "msg_alert", 3)
            self.chatter(LINES_LOST, "msg_alert", 4, chance=0.5)
            if not self.check_garden():
                return
            if c.eaten >= FULL_BELLY:
                c.state = "leave"
                c.target = self.nearest_edge(c)
                self.say("The %s waddles off, full. For now." % c.kind, "msg", 3)
            else:
                self.choose_goal(c)

    def escape(self, c):
        if c in self.critters:
            self.critters.remove(c)
        if c.carrying == "flower":
            self.escaped += 1
            self.say("The squirrel got away with a flower!", "msg_alert", 4)
            self.chatter(LINES_LOST, "msg_alert", 4, chance=0.6)
            self.check_garden()
        elif c.carrying == "treat":
            self.say("There goes your biscuit, over the fence.", "msg_alert", 3)

    def check_garden(self):
        if self.flowers_left() <= 0:
            self.game_over("THE GARDEN IS GONE")
            return False
        return True

    # ------------------------------------------------------------ treats and flowers
    def update_items(self):
        self.treat_t -= 1
        if self.treat_t <= 0 and self.mode == "play" and not any(i.kind == "treat" for i in self.items):
            self.toss_treat()
        for it in list(self.items):
            if it.air > 0:
                it.air -= 1
                if it.air == 0:
                    self.puff(it.cx(), it.y, 3, "dust")
                continue
            it.life -= 1
            if it.life <= 0:
                self.items.remove(it)
                if it.kind == "flower":
                    self.say("The dropped flower wilted.", "msg", 3)
                else:
                    self.say("A crow swooped in and took the biscuit.", "msg", 3)

    def toss_treat(self):
        w = self.world
        for _ in range(40):
            x = self.rng.randint(4, LAWN_RIGHT - 6)
            y = self.rng.randint(3, LAWN_BOT - 1)
            if w.free(x, y, 3, 1):
                break
        else:
            return
        it = Item("treat", x, y, TREAT_LIFE)
        it.toss(TOSS_FROM[0], TOSS_FROM[1], TREAT_AIR)
        self.items.append(it)
        hungry = self.dog.bark <= 1
        self.treat_t = self.rng.randint(*(TREAT_HUNGRY_EVERY if hungry else TREAT_EVERY))
        self.chatter(LINES_TREAT, "msg_good", 4)

    def collect(self, it):
        d = self.dog
        if it in self.items:
            self.items.remove(it)
        if it.kind == "treat":
            before = d.bark
            d.bark = min(BARK_MAX, d.bark + TREAT_BARK)
            self.add_score(SCORE["treat"])
            self.texts.append(FloatText(d.x, d.y - 1, "CRUNCH +%d" % SCORE["treat"], "treat"))
            for i in range(4):
                self.particles.append(Particle(d.cx() - 2 + i, d.y - 1, 0.0, -0.15, 14, HEART, "heart"))
            if d.bark > before:
                self.say("Crunch! Bark recharged (%d/%d)." % (d.bark, BARK_MAX), "msg_good", 3)
            else:
                self.say("Crunch! Bark already full. Still delicious.", "msg_good", 3)
        else:
            room = self.world.beds_with_room()
            if room:
                room.sort(key=lambda b: dist(b.cx(), b.cy(), d.cx(), d.cy()))
                bed = room[0]
                bed.slots[self.rng.choice(bed.empty())] = True
                self.puff(bed.cx(), bed.y, 5, bed.color)
            self.add_score(SCORE["flower_back"])
            self.texts.append(FloatText(d.x, d.y - 1, "+%d" % SCORE["flower_back"], "hud_gold"))
            self.say("Good dog! Flower replanted.", "msg_good", 3)

    # ------------------------------------------------------------ contact
    def contacts(self):
        d = self.dog
        for it in list(self.items):
            if it.landed() and overlap(d, it):
                self.collect(it)
        for c in list(self.critters):
            if c.kind == "gopher" and c.state == "go":
                hx, hy = c.head()
                if rects_overlap(d.rect(), (hx, hy, 1, 1)):
                    self.pop(c)
                continue
            if c.scareable() and overlap(d, c):
                self.scare(c, "tackle")

    # ------------------------------------------------------------ effects
    def puff(self, x, y, n, color="dust"):
        for _ in range(n):
            a = self.rng.random() * math.tau
            sp = self.rng.uniform(0.1, 0.5)
            self.particles.append(Particle(x, y, math.cos(a) * sp * 1.6, math.sin(a) * sp * 0.5,
                                           self.rng.randint(6, 14), self.rng.choice("·∘*"), color))

    def update_barks(self):
        for b in list(self.barks):
            b.t += 1
            if b.t > BARK_RING_TICKS:
                self.barks.remove(b)

    def update_particles(self):
        for p in list(self.particles):
            p.life -= 1
            p.x += p.vx
            p.y += p.vy
            if p.life <= 0:
                self.particles.remove(p)
        for t in list(self.texts):
            t.life -= 1
            if t.life % 6 == 0:
                t.y -= 1
            if t.life <= 0:
                self.texts.remove(t)

    # ------------------------------------------------------------ update
    def update(self):
        if self.banner_t > 0:
            self.banner_t -= 1
        self.update_dog()
        self.update_barks()
        self.update_items()
        self.update_particles()
        if self.mode == "clear":
            if self.banner_t <= 0:
                self.start_day(self.day + 1)
            return
        self.update_spawns()
        for c in list(self.critters):
            if c in self.critters:
                self.update_critter(c)
        if self.mode != "play":
            return
        self.contacts()
        self.check_day_end()
        self.idle_chatter()

    def check_day_end(self):
        if self.banner_t > 0:
            return
        if all(self.spawned[k] >= self.quota[k] for k in self.quota) and not self.critters:
            self.day_cleared()

    def idle_chatter(self):
        self.idle_t -= 1
        if self.idle_t <= 0 and not self.messages:
            self.idle_t = FPS * 14
            self.say(self.rng.choice(LINES_IDLE), "msg", 5)
