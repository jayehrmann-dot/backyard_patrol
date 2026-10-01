"""Curses renderer: HUD, the yard, sprites, bark rings and overlays."""
import curses
import math

from .constants import (
    VIEW_COLS, VIEW_ROWS, PLAY_TOP, MSG_TOP, PLAY_ROWS, FENCE_Y, LAWN_TOP, LAWN_BOT, HOUSE_Y,
    FENCE_L, FENCE_R, LAWN_LEFT, LAWN_RIGHT, BARK_MAX, BARK_RX, BARK_RY, BARK_RING_TICKS,
    PALETTE, FONT, DOG_R, DOG_L, DOG_LEGEND, SQUIRREL_R, SQUIRREL_L, GOPHER, MOUND, DIRT,
    RACCOON_R, RACCOON_L, RACCOON_LEGEND, TREAT, FLOWER, FLOWER_SHAKE, STEM, BARK_RING,
    TREE, DOGHOUSE, DOGHOUSE_LEGEND, CAN_UP, CAN_DOWN, MESS,
)
from .world import TREE_X, TREE_Y, DOGHOUSE_X, DOGHOUSE_Y, DOOR_X, DOOR_W, WINDOW_X, WINDOW_W

CONTROLS = [
    "ARROWS / WASD ...... run around the yard",
    "SPACE / F / B ...... BARK (uses one breath from the bark meter)",
    "P .................. pause          ? ...... this card",
    "Q or ESC ........... quit (asks first)",
    "",
    "Squirrels hop the fence, dig up a flower and run off with it.",
    "Gophers tunnel in (watch the moving mound) and eat flowers",
    "from below. Stand on the mound to dig them out, or bark when",
    "they surface. Raccoons come at night: they go for your treats",
    "and the trash cans first. One bark only makes them hiss. Bark",
    "twice, or run straight into them.",
    "",
    "Running into any intruder chases it off too, for bonus points.",
    "A scared squirrel drops what it is carrying: walk over a",
    "dropped flower to replant it.",
    "",
    "Your BARK meter is your breath. The owner tosses biscuits",
    "(o=o) out of the kitchen window: catch them to recharge.",
    "Beware: squirrels and raccoons like biscuits too.",
    "",
    "When every flower is gone, the game is over.",
]


class Renderer:
    def __init__(self, stdscr):
        self.scr = stdscr
        self.pairs = {}
        self.colors_ok = curses.has_colors()
        if self.colors_ok:
            curses.start_color()
            try:
                curses.use_default_colors()
            except curses.error:
                pass
        self.many = self.colors_ok and curses.COLORS >= 256
        self.max_pairs = curses.COLOR_PAIRS if self.colors_ok else 0
        self.oy = self.ox = 0

    # ------------------------------------------------------------ colours
    def cidx(self, name):
        full, basic = PALETTE[name]
        return full if self.many else basic

    def attr(self, fg, bg, bold=False):
        if not self.colors_ok:
            return curses.A_BOLD if bold else 0
        key = (self.cidx(fg), self.cidx(bg))
        if key not in self.pairs:
            n = len(self.pairs) + 1
            if n >= self.max_pairs:
                return 0
            try:
                curses.init_pair(n, key[0], key[1])
            except curses.error:
                return 0
            self.pairs[key] = n
        a = curses.color_pair(self.pairs[key])
        return a | curses.A_BOLD if bold else a

    def put(self, y, x, s, attr=0):
        try:
            self.scr.addstr(y, x, s, attr)
        except curses.error:
            pass

    def fill(self, y0, x0, rows, cols, attr):
        for y in range(y0, y0 + rows):
            self.put(y, x0, " " * cols, attr)

    def center(self, y, text, attr=0):
        self.put(y, self.ox + (VIEW_COLS - len(text)) // 2, text, attr)

    def big(self, y, x, text, attr):
        for i, ch in enumerate(text.upper()):
            glyph = FONT.get(ch, FONT[" "])
            for r, row in enumerate(glyph):
                for c, px in enumerate(row):
                    if px == "█":
                        self.put(y + r, x + i * 4 + c, "█", attr)

    def big_center(self, y, text, attr):
        w = len(text) * 4 - 1
        self.big(y, self.ox + (VIEW_COLS - w) // 2, text, attr)

    # ------------------------------------------------------------ yard helpers
    def lawn_bg(self, g):
        return "lawn_n" if g.night else "lawn"

    def cell(self, g, x, y, ch, fg, bold=False, bg=None, clip=True):
        """Draw one cell at play-area coordinates (x, y)."""
        x, y = int(x), int(y)
        if clip and not (LAWN_LEFT <= x <= LAWN_RIGHT and LAWN_TOP <= y <= LAWN_BOT):
            return
        if not (0 <= x < VIEW_COLS and 0 <= y < PLAY_ROWS):
            return
        self.put(self.oy + PLAY_TOP + y, self.ox + x, ch, self.attr(fg, bg or self.lawn_bg(g), bold))

    def blit(self, g, x, y, rows, fg, legend=None, bold=False, bg=None, clip=True):
        x, y = int(x), int(y)
        for r, row in enumerate(rows):
            for c, ch in enumerate(row):
                if ch == " ":
                    continue
                f = fg
                if legend and ch in legend:
                    ch, f = legend[ch]
                self.cell(g, x + c, y + r, ch, f, bold, bg, clip)

    def text(self, g, x, y, s, fg, bold=True):
        for i, ch in enumerate(s):
            self.cell(g, x + i, y, ch, fg, bold)

    # ------------------------------------------------------------ frame
    def draw(self, g):
        self.scr.erase()
        rows, cols = self.scr.getmaxyx()
        if rows < VIEW_ROWS or cols < VIEW_COLS:
            self.put(0, 0, "Backyard Patrol needs a terminal of at least %dx%d (you have %dx%d)."
                     % (VIEW_COLS, VIEW_ROWS, cols, rows))
            self.put(1, 0, "Enlarge the window.")
            self.scr.refresh()
            return
        self.oy = (rows - VIEW_ROWS) // 2
        self.ox = (cols - VIEW_COLS) // 2
        if g.mode == "title" or (g.mode == "help" and g.prev_mode == "title"):
            self.draw_title(g)
        else:
            self.draw_hud(g)
            self.draw_yard(g)
            self.draw_messages(g)
        if g.mode == "help":
            self.draw_help()
        elif g.mode == "pause":
            self.overlay(["PAUSED", "", "P to resume   Q to quit   ? for help"])
        elif g.mode == "quit":
            self.overlay(["GO INSIDE?", "", "Y to quit, any other key to keep patrolling"])
        elif g.mode == "gameover":
            self.draw_gameover(g)
        if g.banner_t > 0 and g.mode in ("play", "clear") and g.banner:
            self.draw_banner(g)
        self.scr.refresh()

    # ------------------------------------------------------------ HUD
    def draw_hud(self, g):
        y = self.oy
        self.fill(y, self.ox, 1, VIEW_COLS, self.attr("hud", "hud_bg"))
        self.put(y, self.ox + 1, "SCORE", self.attr("hud_dim", "hud_bg"))
        self.put(y, self.ox + 7, "%06d" % g.score, self.attr("hud", "hud_bg", True))
        self.put(y, self.ox + 15, "HI", self.attr("hud_dim", "hud_bg"))
        self.put(y, self.ox + 18, "%06d" % max(g.high, g.score), self.attr("hud_gold", "hud_bg"))
        label = "NIGHT" if g.night else "DAY"
        self.put(y, self.ox + 26, label, self.attr("hud_dim", "hud_bg"))
        self.put(y, self.ox + 27 + len(label), "%02d" % g.day, self.attr("hud", "hud_bg", True))
        self.put(y, self.ox + 36, "BARK", self.attr("hud_dim", "hud_bg"))
        meter = "▮" * g.dog.bark + "▯" * (BARK_MAX - g.dog.bark)
        mcol = "hud_red" if g.dog.bark <= 1 else ("hud_gold" if g.dog.bark <= 3 else "hud_green")
        self.put(y, self.ox + 41, meter, self.attr(mcol, "hud_bg", True))
        n = g.flowers_left()
        self.put(y, self.ox + 49, "FLOWERS", self.attr("hud_dim", "hud_bg"))
        self.put(y, self.ox + 57, "%2d" % n, self.attr("hud_red" if n <= 3 else "hud", "hud_bg", True))
        self.put(y, self.ox + 60, FLOWER, self.attr("flower0", "hud_bg", True))

    # ------------------------------------------------------------ the yard
    def draw_yard(self, g):
        top = self.oy + PLAY_TOP
        night = g.night
        lawn = self.lawn_bg(g)
        tuft = "lawn_n2" if night else "lawn2"
        fence_fg = "fence_n" if night else "fence"
        fence_bg = "fence_nbg" if night else "fence_bg"
        wall_fg = "wall_n" if night else "wall"
        wall_bg = "wall_nbg" if night else "wall_bg"
        # lawn
        for r in range(LAWN_TOP, LAWN_BOT + 1):
            self.put(top + r, self.ox, " " * VIEW_COLS, self.attr(lawn, lawn))
        for x, y, ch in g.world.tufts:
            self.cell(g, x, y, ch, tuft)
        # back fence and side fences
        fence_row = "".join("█" if i % 4 == 0 else "▀" for i in range(VIEW_COLS))
        self.put(top + FENCE_Y, self.ox, fence_row, self.attr(fence_fg, fence_bg))
        for r in range(LAWN_TOP, LAWN_BOT + 1):
            self.put(top + r, self.ox + FENCE_L, "▌", self.attr(fence_fg, lawn))
            self.put(top + r, self.ox + FENCE_R, "▐", self.attr(fence_fg, lawn))
        # the house wall, back door and kitchen window
        self.put(top + HOUSE_Y, self.ox, "█" * VIEW_COLS, self.attr(wall_fg, wall_bg))
        self.put(top + HOUSE_Y, self.ox + DOOR_X, "▐" + "█" * (DOOR_W - 2) + "▌", self.attr("door", wall_bg))
        win = "▐" + ("▒" if (g.tick // 20) % 7 else "░") * (WINDOW_W - 2) + "▌"
        self.put(top + HOUSE_Y, self.ox + WINDOW_X, win, self.attr("window_n" if night else "window", wall_bg, True))
        # tree, doghouse, trash cans, mess
        leaf = "leaf_n" if night else "leaf"
        legend = {"▐": ("▐", "trunk"), "▌": ("▌", "trunk")}
        self.blit(g, TREE_X, TREE_Y, TREE, leaf, legend=legend, bold=not night)
        self.blit(g, DOGHOUSE_X, DOGHOUSE_Y, DOGHOUSE, "house_dark", legend=DOGHOUSE_LEGEND, bold=True)
        self.cell(g, DOGHOUSE_X + 3, DOGHOUSE_Y + 2, "▌", "house_dark", True)
        for k in g.world.cans:
            if k.tipped:
                self.blit(g, k.x, k.y, CAN_DOWN, "can_dark", bold=True)
            else:
                self.blit(g, k.x, k.y, CAN_UP, "can", legend={"▒": ("▒", "can_dark")}, bold=True)
        for i, (mx, my) in enumerate(g.mess):
            self.cell(g, mx, my, MESS[i % len(MESS)], "mess")
        # flowerbeds
        soil = "soil_n" if night else "soil"
        for b in g.world.beds:
            self.text(g, b.x, b.y + 1, "▓" * b.w, soil, False)
            for i, present in enumerate(b.slots):
                x = b.slot_x(i)
                if not present:
                    self.cell(g, x, b.y, STEM, "stem")
                elif b.shake[i] > 0:
                    self.cell(g, x, b.y, FLOWER_SHAKE[(g.tick // 2) % 2], b.color, True)
                else:
                    self.cell(g, x, b.y, FLOWER, b.color, True)
        # gopher tunnels and mounds
        for c in g.critters:
            if c.kind != "gopher":
                continue
            for tx, ty, life in c.trail:
                self.cell(g, tx, ty, DIRT[0 if life > 60 else 1 if life > 30 else 2], "dirt")
            if c.underground():
                hx, hy = c.head()
                self.cell(g, hx, hy, MOUND, "mound", True)
                if c.state == "go" and (g.tick // 4) % 2:
                    self.cell(g, hx, hy, "▲", "gopher2", True)
        # treats and dropped flowers
        for it in g.items:
            x, y = it.draw_pos()
            if it.kind == "treat":
                blink = it.life < 90 and (g.tick // 4) % 2 == 0 and it.landed()
                if not blink:
                    self.text(g, x, y, TREAT, "treat")
            else:
                self.cell(g, x, y, FLOWER, it.color or "flower0", True)
        # intruders
        for c in g.critters:
            self.draw_critter(g, c)
        # the dog and its bark
        self.draw_dog(g)
        for b in g.barks:
            self.draw_bark(g, b)
        # particles and floating text
        for p in g.particles:
            self.cell(g, p.x, p.y, p.ch, p.color, True)
        for t in g.texts:
            if (t.max_life - t.life) < 4 or t.life > 8 or (g.tick // 2) % 2:
                self.text(g, t.x, t.y, t.text, t.color)

    def draw_critter(self, g, c):
        if c.kind == "squirrel":
            frames = SQUIRREL_R if c.facing > 0 else SQUIRREL_L
            frame = frames[(c.anim // 3) % 2] if c.state in ("go", "leave", "flee") else frames[0]
            fg = "squirrel2" if c.state == "flee" and (g.tick // 2) % 2 else "squirrel"
            self.blit(g, c.x, c.y, frame, fg, bold=True)
            if c.carrying == "flower":
                self.cell(g, c.x + (2 if c.facing > 0 else 0), c.y - 1, FLOWER, c.flower_color or "flower0", True)
            elif c.carrying == "treat":
                self.cell(g, c.x + (2 if c.facing > 0 else 0), c.y - 1, "o", "treat", True)
        elif c.kind == "gopher":
            if c.underground():
                return
            fg = "gopher2" if c.state == "popped" and (g.tick // 2) % 2 else "gopher"
            self.blit(g, c.x, c.y, GOPHER, fg, bold=True)
            if c.state == "work":
                self.cell(g, c.x + 1, c.y, "▀" if (g.tick // 4) % 2 else "▄", "gopher2", True)
            if c.state == "popped":
                self.cell(g, c.x + 1, c.y - 1, "?", "hud", True)
        else:
            frames = RACCOON_R if c.facing > 0 else RACCOON_L
            frame = frames[(c.anim // 4) % 2] if c.state in ("go", "leave", "flee") else frames[0]
            fg = "raccoon"
            if c.stun_t > 0 and (g.tick // 2) % 2:
                fg = "eyes"
            self.blit(g, c.x, c.y, frame, fg, legend=RACCOON_LEGEND, bold=True)

    def draw_dog(self, g):
        d = g.dog
        frames = DOG_R if d.facing > 0 else DOG_L
        frame = frames[(d.anim // 3) % 2] if d.moving() else frames[2]
        self.blit(g, d.x, d.y, frame, "dog", legend=DOG_LEGEND, bold=True)
        if d.woof_t > 0:
            wx = d.x + d.w if d.facing > 0 else d.x - len(d.woof)
            wx = max(LAWN_LEFT, min(wx, LAWN_RIGHT - len(d.woof) + 1))
            wy = d.y - 1 if d.y > LAWN_TOP else d.y + d.h
            self.text(g, wx, wy, d.woof, "woof")

    def draw_bark(self, g, b):
        t = b.t / float(BARK_RING_TICKS)
        rx, ry = BARK_RX * t, BARK_RY * t
        fg = "bark" if b.t < 4 else "bark2"
        ch = BARK_RING[min(2, b.t // 3)]
        n = 28
        for i in range(n):
            a = i * math.tau / n
            x = b.cx + math.cos(a) * rx
            y = b.cy + math.sin(a) * ry
            self.cell(g, int(round(x)), int(round(y)), ch, fg, True)

    # ------------------------------------------------------------ messages
    def draw_messages(self, g):
        y = self.oy + MSG_TOP
        self.fill(y, self.ox, 2, VIEW_COLS, self.attr("hud", "hud_bg"))
        if g.messages:
            text, kind = g.messages[-1]
            self.put(y, self.ox + 1, text[:VIEW_COLS - 2], self.attr(kind, "hud_bg", kind != "msg"))
        left = g.intruders_left()
        self.put(y + 1, self.ox + 1, "INTRUDERS LEFT", self.attr("hud_dim", "hud_bg"))
        self.put(y + 1, self.ox + 16, "%2d" % left, self.attr("hud", "hud_bg", True))
        self.put(y + 1, self.ox + 21, "CHASED OFF", self.attr("hud_dim", "hud_bg"))
        self.put(y + 1, self.ox + 32, "%3d" % g.chased, self.attr("hud_green", "hud_bg", True))
        self.put(y + 1, self.ox + 38, "FLOWERS LOST", self.attr("hud_dim", "hud_bg"))
        self.put(y + 1, self.ox + 51, "%2d" % (12 - g.flowers_left()), self.attr("hud_red", "hud_bg", True))
        if g.dog.bark <= 1 and (g.tick // 8) % 2:
            self.put(y + 1, self.ox + 55, "TREATS!", self.attr("treat", "hud_bg", True))

    # ------------------------------------------------------------ overlays
    def draw_banner(self, g):
        y = self.oy + PLAY_TOP + 5
        text = g.banner
        w = len(text) * 4 + 3
        x = self.ox + (VIEW_COLS - w) // 2
        self.fill(y - 1, x, 7, w, self.attr("panel_fg", "panel"))
        fg = "title3" if "DONE" in text else ("title2" if g.night else "title")
        self.big(y, x + 2, text, self.attr(fg, "panel", True))
        if g.night and "DONE" not in text:
            self.center(y + 6, "NIGHT FALLS. SOMETHING IS RUSTLING BY THE FENCE.", self.attr("hud", "panel", True))

    def overlay(self, lines):
        w = max(len(l) for l in lines) + 6
        h = len(lines) + 2
        y = self.oy + PLAY_TOP + (PLAY_ROWS - h) // 2
        x = self.ox + (VIEW_COLS - w) // 2
        self.fill(y, x, h, w, self.attr("panel_fg", "panel"))
        for i, l in enumerate(lines):
            self.put(y + 1 + i, x + (w - len(l)) // 2, l, self.attr("title" if i == 0 else "panel_fg", "panel", i == 0))

    def draw_help(self):
        self.fill(self.oy, self.ox, VIEW_ROWS, VIEW_COLS, self.attr("panel_fg", "panel"))
        self.center(self.oy, "BACKYARD PATROL: HOW TO BE A GOOD DOG", self.attr("title", "panel", True))
        for i, line in enumerate(CONTROLS):
            self.put(self.oy + 2 + i, self.ox + 2, line, self.attr("panel_fg", "panel"))
        self.center(self.oy + VIEW_ROWS - 1, "any key to return", self.attr("hud_dim", "panel"))

    def draw_gameover(self, g):
        y = self.oy + PLAY_TOP + 3
        self.fill(y - 1, self.ox + 1, 13, VIEW_COLS - 2, self.attr("panel_fg", "panel"))
        self.big_center(y, "GAME OVER", self.attr("hud_red", "panel", True))
        self.center(y + 6, g.banner, self.attr("title", "panel", True))
        self.center(y + 7, "FINAL SCORE %06d     DAYS %d     CHASED OFF %d" % (g.score, g.day, g.chased),
                    self.attr("hud", "panel", True))
        if g.score >= g.high and g.score > 0:
            self.center(y + 8, "NEW HIGH SCORE", self.attr("title3", "panel", True))
        else:
            self.center(y + 8, "HIGH SCORE %06d" % g.high, self.attr("hud_gold", "panel"))
        self.center(y + 9, "Owner: ...you're still a good dog, Biscuit.", self.attr("hud_dim", "panel"))
        self.center(y + 11, "N  new game        Q  quit", self.attr("hud_dim", "panel"))

    def draw_title(self, g):
        # evening sky over a strip of lawn
        self.fill(self.oy, self.ox, 18, VIEW_COLS, self.attr("sky_star", "sky"))
        for i in range(30):
            sx = (i * 37 + 11) % VIEW_COLS
            sy = (i * 13 + 3) % 16
            ch = "·" if (i + g.title_t // 10) % 3 else "+"
            self.put(self.oy + sy, self.ox + sx, ch, self.attr("sky_star", "sky"))
        t = g.title_t
        self.big_center(self.oy + 1, "BACKYARD", self.attr("title", "sky", True))
        self.big_center(self.oy + 7, "PATROL", self.attr("title2", "sky", True))
        self.center(self.oy + 13, "SQUIRRELS. GOPHERS. ONE SNEAKY RACCOON.", self.attr("hud", "sky"))
        self.center(self.oy + 14, "YOU ARE THE DOG. THE FLOWERS ARE COUNTING ON YOU.", self.attr("hud_dim", "sky"))
        # a fence and a strip of lawn with a chase on it
        fence_row = "".join("█" if i % 4 == 0 else "▀" for i in range(VIEW_COLS))
        self.put(self.oy + 17, self.ox, fence_row, self.attr("fence", "fence_bg"))
        for r in range(18, 24):
            self.put(self.oy + r, self.ox, " " * VIEW_COLS, self.attr("lawn", "lawn"))
        for x, y, ch in g.world.tufts:
            if y % 3 == 0:
                self.put(self.oy + 18 + (y % 4), self.ox + x, ch, self.attr("lawn2", "lawn"))
        cx = (t * 2 // 3) % (VIEW_COLS + 30) - 15
        sq = SQUIRREL_R[(t // 3) % 2][0]
        for c, ch in enumerate(sq):
            if 0 <= cx + 10 + c < VIEW_COLS:
                self.put(self.oy + 19, self.ox + cx + 10 + c, ch, self.attr("squirrel", "lawn", True))
        if 0 <= cx + 12 < VIEW_COLS:
            self.put(self.oy + 18, self.ox + cx + 12, FLOWER, self.attr("flower0", "lawn", True))
        frame = DOG_R[(t // 3) % 2]
        for r, row in enumerate(frame):
            for c, ch in enumerate(row):
                if ch == " " or not (0 <= cx + c < VIEW_COLS):
                    continue
                fg = "dog"
                if ch in DOG_LEGEND:
                    ch, fg = DOG_LEGEND[ch]
                self.put(self.oy + 18 + r, self.ox + cx + c, ch, self.attr(fg, "lawn", True))
        if (t // 6) % 3 == 0 and 0 <= cx + 6 < VIEW_COLS - 5:
            self.put(self.oy + 17, self.ox + cx + 6, "WOOF!", self.attr("woof", "fence_bg", True))
        self.center(self.oy + 21, "HIGH SCORE %06d" % g.high, self.attr("hud_gold", "lawn", True))
        prompt = "N  START PATROL       ?  HOW TO PLAY       Q  QUIT"
        self.center(self.oy + 22, prompt, self.attr("panel" if (t // 15) % 2 else "hud", "lawn", True))
