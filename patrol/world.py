"""The yard: flowerbeds, the tree, the doghouse, the trash cans and the house."""
import random

from .constants import LAWN_TOP, LAWN_BOT, LAWN_LEFT, LAWN_RIGHT, DOGHOUSE
from .entities import Bed, TrashCan, rects_overlap

# (x, y, colour) of each flowerbed's top-left corner
BEDS = [
    (6, 3, "flower0"),
    (34, 5, "flower1"),
    (12, 12, "flower2"),
    (40, 13, "flower3"),
]

TREE_X, TREE_Y = 49, 1
TRUNK_RECT = (TREE_X + 5, TREE_Y + 3, 2, 2)        # the only solid part of the tree
TREE_SPAWN = (TREE_X + 4, TREE_Y + 5)              # squirrels come down the trunk here

DOGHOUSE_X, DOGHOUSE_Y = 2, 16
DOGHOUSE_RECT = (DOGHOUSE_X, DOGHOUSE_Y, len(DOGHOUSE[0]), len(DOGHOUSE))

CANS = [(51, 17), (55, 17)]

DOOR_X, DOOR_W = 26, 4
WINDOW_X, WINDOW_W = 34, 6
TOSS_FROM = (WINDOW_X + 2, LAWN_BOT)               # treats fly out of the kitchen window

DOG_START = (10, 17)


class World:
    def __init__(self):
        self.beds = [Bed(x, y, c) for x, y, c in BEDS]
        self.cans = [TrashCan(x, y) for x, y in CANS]
        rng = random.Random(1985)
        self.tufts = []
        solid = self.solid_rects()
        while len(self.tufts) < 70:
            x = rng.randint(LAWN_LEFT + 1, LAWN_RIGHT - 1)
            y = rng.randint(LAWN_TOP + 1, LAWN_BOT - 1)
            if not any(rects_overlap((x, y, 1, 1), r) for r in solid):
                self.tufts.append((x, y, rng.choice("'',`")))

    def reset(self):
        for b in self.beds:
            b.slots = [True, True, True]
            b.shake = [0, 0, 0]
        for c in self.cans:
            c.tipped = False

    # ------------------------------------------------------------ geometry
    def solid_rects(self):
        rects = [b.rect() for b in self.beds]
        rects.append(TRUNK_RECT)
        rects.append(DOGHOUSE_RECT)
        rects.extend(c.rect() for c in self.cans)
        return rects

    def blocked(self, x, y, w, h):
        """True if a w x h footprint at (x, y) would stand on something solid."""
        r = (x, y, w, h)
        return any(rects_overlap(r, s) for s in self.solid_rects())

    def free(self, x, y, w, h, margin=1):
        """True if the footprint (plus a margin) is clear lawn."""
        if x < LAWN_LEFT or y < LAWN_TOP or x + w - 1 > LAWN_RIGHT or y + h - 1 > LAWN_BOT:
            return False
        r = (x - margin, y - margin, w + 2 * margin, h + 2 * margin)
        return not any(rects_overlap(r, s) for s in self.solid_rects())

    # ------------------------------------------------------------ flowers
    def flowers(self):
        return sum(b.count() for b in self.beds)

    def beds_with_flowers(self):
        return [b for b in self.beds if b.count() > 0]

    def beds_with_room(self):
        return [b for b in self.beds if b.count() < 3]
