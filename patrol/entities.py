"""Entities: the dog, flowerbeds, critters, treats, bark rings and particles."""
import math

from .constants import (
    BARK_START, BARK_REGEN, SQUIRREL_SPEED, SQUIRREL_FLEE, GOPHER_SPEED, GOPHER_FLEE,
    RACCOON_SPEED, RACCOON_FLEE, RACCOON_BARKS,
)


def clamp(v, lo, hi):
    return lo if v < lo else hi if v > hi else v


def sign(v):
    return (v > 0) - (v < 0)


def dist(ax, ay, bx, by):
    """Distance in 'cell widths'; terminal cells are about twice as tall as wide."""
    return math.hypot(ax - bx, (ay - by) * 2.0)


def rects_overlap(a, b):
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    return ax < bx + bw and bx < ax + aw and ay < by + bh and by < ay + ah


def overlap(a, b):
    return rects_overlap(a.rect(), b.rect())


class Body:
    w = 1
    h = 1

    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)

    def cx(self):
        return self.x + self.w / 2.0

    def cy(self):
        return self.y + self.h / 2.0

    def rect(self):
        return (int(self.x), int(self.y), self.w, self.h)


class Dog(Body):
    w = 6
    h = 2

    def __init__(self, x, y):
        super().__init__(x, y)
        self.facing = 1
        self.mx = 0
        self.my = 0
        self.mx_t = 0
        self.my_t = 0
        self.bark = BARK_START
        self.bark_cool = 0
        self.woof_t = 0
        self.woof = "WOOF!"
        self.anim = 0
        self.regen_t = BARK_REGEN

    def moving(self):
        return self.mx_t > 0 or self.my_t > 0


class Bed:
    """A flowerbed: a row of three flower slots over a row of soil."""
    w = 5
    h = 2

    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color
        self.slots = [True, True, True]
        self.shake = [0, 0, 0]

    def rect(self):
        return (self.x, self.y, self.w, self.h)

    def slot_x(self, i):
        return self.x + 1 + i

    def count(self):
        return sum(1 for s in self.slots if s)

    def present(self):
        return [i for i, s in enumerate(self.slots) if s]

    def empty(self):
        return [i for i, s in enumerate(self.slots) if not s]

    def cx(self):
        return self.x + 2.5

    def cy(self):
        return self.y + 1.0


class TrashCan:
    w = 3
    h = 2

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.tipped = False

    def rect(self):
        return (self.x, self.y, self.w, self.h)

    def cx(self):
        return self.x + 1.5

    def cy(self):
        return self.y + 1.0


class Critter(Body):
    kind = "critter"
    speed = (0.5, 0.25)
    flee_speed = (0.9, 0.45)

    def __init__(self, x, y):
        super().__init__(x, y)
        self.state = "enter"          # enter, go, work, leave, flee, popped
        self.facing = 1
        self.want = None              # "flower", "treat" or "can"
        self.bed = None
        self.slot = None
        self.item = None
        self.can = None
        self.target = None            # (x, y) the critter is heading for
        self.work_t = 0
        self.stun_t = 0
        self.hop_t = 0
        self.jx = 0
        self.jy = 0
        self.carrying = None          # "flower" or "treat"
        self.flower_color = None
        self.hits = 0
        self.eaten = 0
        self.anim = 0
        self.trail = []               # gopher dirt: [x, y, life]
        self.think_t = 0

    def underground(self):
        return False

    def scareable(self):
        return self.state not in ("flee", "popped") and not self.underground()


class Squirrel(Critter):
    kind = "squirrel"
    w = 3
    h = 1
    speed = SQUIRREL_SPEED
    flee_speed = SQUIRREL_FLEE


class Gopher(Critter):
    kind = "gopher"
    w = 3
    h = 1
    speed = GOPHER_SPEED
    flee_speed = GOPHER_FLEE

    def underground(self):
        return self.state in ("enter", "go", "leave", "flee")

    def head(self):
        return int(self.cx()), int(self.y)


class Raccoon(Critter):
    kind = "raccoon"
    w = 6
    h = 2
    speed = RACCOON_SPEED
    flee_speed = RACCOON_FLEE
    needed = RACCOON_BARKS


class Item(Body):
    """A treat or a dropped flower lying on (or flying toward) the lawn."""

    def __init__(self, kind, x, y, life, color=None):
        super().__init__(x, y)
        self.kind = kind
        self.life = life
        self.color = color
        self.w = 3 if kind == "treat" else 1
        self.h = 1
        self.air = 0
        self.air_total = 1
        self.x0 = self.x
        self.y0 = self.y

    def toss(self, x0, y0, ticks):
        self.x0, self.y0 = float(x0), float(y0)
        self.air = self.air_total = ticks

    def landed(self):
        return self.air <= 0

    def draw_pos(self):
        if self.air <= 0:
            return int(self.x), int(self.y)
        t = 1.0 - self.air / float(self.air_total)
        x = self.x0 + (self.x - self.x0) * t
        y = self.y0 + (self.y - self.y0) * t - 5.0 * math.sin(math.pi * t)
        return int(round(x)), int(round(y))


class Bark:
    def __init__(self, cx, cy):
        self.cx = cx
        self.cy = cy
        self.t = 0


class Particle:
    def __init__(self, x, y, vx, vy, life, ch, color):
        self.x = float(x)
        self.y = float(y)
        self.vx = vx
        self.vy = vy
        self.life = life
        self.ch = ch
        self.color = color


class FloatText:
    def __init__(self, x, y, text, color, life=28):
        self.x = float(x)
        self.y = float(y)
        self.text = text
        self.color = color
        self.life = life
        self.max_life = life
