"""Constants, tuning, palette, sprites, block font and owner chatter for Backyard Patrol."""

FPS = 30
TICK = 1.0 / FPS

# ---------------------------------------------------------------- screen layout
VIEW_COLS = 64
HUD_ROWS = 1
PLAY_ROWS = 21                                   # fence row, 19 lawn rows, house row
MSG_ROWS = 2
VIEW_ROWS = HUD_ROWS + PLAY_ROWS + MSG_ROWS      # 24 terminal rows
PLAY_TOP = HUD_ROWS                              # first play row (1)
MSG_TOP = PLAY_TOP + PLAY_ROWS                   # first message row (22)

# ---------------------------------------------------------------- the yard
# Play-area coordinates: row 0 is the back fence, row 20 is the house wall,
# column 0 and column 63 are the side fences.
FENCE_Y = 0
LAWN_TOP = 1
LAWN_BOT = 19
HOUSE_Y = 20
FENCE_L = 0
FENCE_R = 63
LAWN_LEFT = 1
LAWN_RIGHT = 62

# ---------------------------------------------------------------- the dog
DOG_VX = 0.80             # cells per tick
DOG_VY = 0.40
MOVE_HOLD = 3             # ticks one key event keeps the dog running (key repeat tops it up)
BARK_MAX = 6
BARK_START = 4
BARK_RX = 13.0            # the bark reaches this far sideways...
BARK_RY = 6.0             # ...and this far up and down (cells are twice as tall as wide)
BARK_COOLDOWN = 8
BARK_RING_TICKS = 8
BARK_REGEN = 25 * FPS     # slow passive recharge; treats are the real refill
TREAT_BARK = 2            # bark units per treat
TREAT_EVERY = (9 * FPS, 14 * FPS)
TREAT_HUNGRY_EVERY = (5 * FPS, 8 * FPS)   # the owner notices when you are out of breath
TREAT_AIR = 28            # ticks a tossed treat is in the air
TREAT_LIFE = 12 * FPS     # how long a treat lies on the lawn
FLOWER_LIFE = 15 * FPS    # how long a dropped flower lasts before it wilts

# ---------------------------------------------------------------- critters
SQUIRREL_SPEED = (0.55, 0.28)
SQUIRREL_FLEE = (0.95, 0.48)
SQUIRREL_DIG = 105
GOPHER_SPEED = (0.20, 0.10)
GOPHER_FLEE = (0.55, 0.28)
GOPHER_EAT = 150
RACCOON_SPEED = (0.30, 0.15)
RACCOON_FLEE = (0.50, 0.25)
RACCOON_DIG = 130
RACCOON_RAID = 150
FULL_BELLY = 2            # gophers and raccoons wander off after eating this many flowers
RACCOON_BARKS = 2         # barks it takes to send a raccoon packing (a tackle always works)
RACCOON_STUN = 25
POP_STUN = 20             # a dug-out gopher sits dazed this long before fleeing

BANNER_TICKS = 75

SCORE = {
    "squirrel": 100, "gopher": 150, "raccoon": 400, "pop": 150,
    "tackle_bonus": 50, "treat": 50, "flower_back": 75, "mess": -250,
}

# ---------------------------------------------------------------- palette
# name -> (256-colour index, basic 8-colour index)
# basic: 0 black 1 red 2 green 3 yellow 4 blue 5 magenta 6 cyan 7 white
PALETTE = {
    "lawn":       (34, 2),
    "lawn2":      (40, 2),
    "lawn_n":     (22, 2),
    "lawn_n2":    (28, 2),
    "fence":      (137, 3),
    "fence_bg":   (94, 3),
    "fence_n":    (95, 3),
    "fence_nbg":  (58, 3),
    "wall":       (250, 7),
    "wall_bg":    (240, 0),
    "wall_n":     (245, 7),
    "wall_nbg":   (236, 0),
    "door":       (94, 3),
    "window":     (226, 3),
    "window_n":   (220, 3),

    "soil":       (94, 3),
    "soil_n":     (58, 3),
    "stem":       (28, 2),
    "flower0":    (205, 5),
    "flower1":    (226, 3),
    "flower2":    (203, 1),
    "flower3":    (177, 5),

    "dog":        (215, 3),
    "dog_dark":   (130, 1),
    "collar":     (196, 1),

    "squirrel":   (137, 1),
    "squirrel2":  (180, 3),
    "gopher":     (94, 3),
    "gopher2":    (137, 3),
    "mound":      (130, 3),
    "dirt":       (95, 3),
    "raccoon":    (250, 7),
    "mask":       (236, 0),
    "eyes":       (231, 7),

    "treat":      (222, 3),
    "treat2":     (180, 3),
    "bark":       (231, 7),
    "bark2":      (226, 3),
    "woof":       (231, 7),
    "heart":      (205, 5),
    "dust":       (187, 7),

    "leaf":       (28, 2),
    "leaf2":      (34, 2),
    "leaf_n":     (22, 2),
    "trunk":      (94, 3),
    "house_red":  (160, 1),
    "house_dark": (52, 1),
    "can":        (250, 7),
    "can_dark":   (245, 7),
    "mess":       (137, 3),

    "hud_bg":     (16, 0),
    "hud":        (231, 7),
    "hud_dim":    (245, 7),
    "hud_gold":   (220, 3),
    "hud_red":    (196, 1),
    "hud_green":  (120, 2),
    "msg":        (159, 6),
    "msg_alert":  (203, 1),
    "msg_good":   (120, 2),
    "panel":      (16, 0),
    "panel_fg":   (231, 7),
    "title":      (220, 3),
    "title2":     (215, 3),
    "title3":     (120, 2),
    "sky":        (17, 4),
    "sky_star":   (250, 7),
}

# ---------------------------------------------------------------- sprites
MIRROR = {
    "▟": "▙", "▙": "▟", "▜": "▛", "▛": "▜", "▶": "◀", "◀": "▶",
    "▘": "▝", "▝": "▘", "▗": "▖", "▖": "▗", "▐": "▌", "▌": "▐",
    "▚": "▞", "▞": "▚", "◢": "◣", "◣": "◢", "◥": "◤", "◤": "◥",
    "(": ")", ")": "(", "<": ">", ">": "<", "/": "\\", "\\": "/",
}


def mirror(rows):
    return tuple("".join(MIRROR.get(ch, ch) for ch in reversed(row)) for row in rows)


# The dog, facing right. Two running frames and a standing frame.
# 'c' is the collar cell, drawn in red.
DOG_R = (
    ("▗▄▄c▟▙", " ▌▌ ▐▌"),
    ("▗▄▄c▟▙", " ▐▐ ▌▐"),
    ("▗▄▄c▟▙", " ▌▌ ▌▐"),
)
DOG_L = tuple(mirror(f) for f in DOG_R)
DOG_LEGEND = {"c": ("▄", "collar")}

# Squirrel facing right: tail up at the back, little head in front.
SQUIRREL_R = (("▞█▘",), ("▚█▘",))
SQUIRREL_L = tuple(mirror(f) for f in SQUIRREL_R)

GOPHER = ("▟▀▙",)            # surfaced gopher
MOUND = "▲"
DIRT = ("∴", "∵", "·")

# Raccoon facing right. 'm' cells are the mask, 'e' the eyes.
RACCOON_R = (
    ("▗▄▄▄▟▙", "▝memem▘"),
    ("▗▄▄▄▟▙", "▝memem▝"),
)
RACCOON_L = tuple(mirror(f) for f in RACCOON_R)
RACCOON_LEGEND = {"m": ("▓", "mask"), "e": ("•", "eyes")}

TREAT = "o=o"
FLOWER = "✿"
FLOWER_SHAKE = ("✿", "✾")
STEM = "."
HEART = "♥"
BARK_RING = ("∘", "∘", "·")
WOOF = ("WOOF!", "WOOF!", "ARF!", "WOOF!")

TREE = (
    "  ▄███████▄  ",
    "▟███████████▙",
    " ▀█████████▀ ",
    "     ▐▌      ",
    "     ▐▌      ",
)
DOGHOUSE = (
    " ▄▄▄▄ ",
    "▐████▌",
    "▐█▐▌█▌",
)
DOGHOUSE_LEGEND = {"▐": ("▐", "house_red"), "▌": ("▌", "house_red"), "█": ("█", "house_red")}
CAN_UP = ("▗▄▖", "▐▒▌")
CAN_DOWN = ("   ", "▄▀▙")
MESS = ("∴", "∵", "·", "'")

# ---------------------------------------------------------------- 3x5 block font
FONT = {
    "A": (" █ ", "█ █", "███", "█ █", "█ █"),
    "B": ("██ ", "█ █", "██ ", "█ █", "██ "),
    "C": (" ██", "█  ", "█  ", "█  ", " ██"),
    "D": ("██ ", "█ █", "█ █", "█ █", "██ "),
    "E": ("███", "█  ", "██ ", "█  ", "███"),
    "F": ("███", "█  ", "██ ", "█  ", "█  "),
    "G": (" ██", "█  ", "█ █", "█ █", " ██"),
    "H": ("█ █", "█ █", "███", "█ █", "█ █"),
    "I": ("███", " █ ", " █ ", " █ ", "███"),
    "J": ("  █", "  █", "  █", "█ █", " █ "),
    "K": ("█ █", "█ █", "██ ", "█ █", "█ █"),
    "L": ("█  ", "█  ", "█  ", "█  ", "███"),
    "M": ("█ █", "███", "███", "█ █", "█ █"),
    "N": ("██ ", "█ █", "█ █", "█ █", "█ █"),
    "O": ("███", "█ █", "█ █", "█ █", "███"),
    "P": ("██ ", "█ █", "██ ", "█  ", "█  "),
    "Q": ("███", "█ █", "█ █", "███", "  █"),
    "R": ("██ ", "█ █", "██ ", "█ █", "█ █"),
    "S": (" ██", "█  ", " █ ", "  █", "██ "),
    "T": ("███", " █ ", " █ ", " █ ", " █ "),
    "U": ("█ █", "█ █", "█ █", "█ █", "███"),
    "V": ("█ █", "█ █", "█ █", "█ █", " █ "),
    "W": ("█ █", "█ █", "███", "███", "█ █"),
    "X": ("█ █", "█ █", " █ ", "█ █", "█ █"),
    "Y": ("█ █", "█ █", " █ ", " █ ", " █ "),
    "Z": ("███", "  █", " █ ", "█  ", "███"),
    "0": ("███", "█ █", "█ █", "█ █", "███"),
    "1": (" █ ", "██ ", " █ ", " █ ", "███"),
    "2": ("███", "  █", "███", "█  ", "███"),
    "3": ("███", "  █", "███", "  █", "███"),
    "4": ("█ █", "█ █", "███", "  █", "  █"),
    "5": ("███", "█  ", "███", "  █", "███"),
    "6": ("█  ", "█  ", "███", "█ █", "███"),
    "7": ("███", "  █", "  █", "  █", "  █"),
    "8": ("███", "█ █", "███", "█ █", "███"),
    "9": ("███", "█ █", "███", "  █", "███"),
    "!": (" █ ", " █ ", " █ ", "   ", " █ "),
    "-": ("   ", "   ", "███", "   ", "   "),
    " ": ("   ", "   ", "   ", "   ", "   "),
}

# ---------------------------------------------------------------- owner chatter
LINES_TREAT = [
    "Owner: Here, Biscuit! *tosses a biscuit out the window*",
    "Owner: Who's a good dog? Catch!",
    "Owner: Snack time, buddy! Heads up!",
    "Owner: Hey pup! Think fast!",
    "Owner: You've earned this one. Go get it!",
]
LINES_SQUIRREL = [
    "Owner: Get 'em, Biscuit! Squirrel!",
    "Owner: Good dog! That squirrel won't be back.",
    "Owner: Ha! Look at it run!",
    "Owner: That's the one that keeps raiding the feeder. Good boy.",
]
LINES_GOPHER = [
    "Owner: You got the gopher! Good boy!",
    "Owner: That gopher's been undermining my begonias for weeks.",
    "Owner: Back to Mr. Gopher's hole with him!",
]
LINES_RACCOON = [
    "Owner: Was that a RACCOON?! Good dog, Biscuit!",
    "Owner: Bold little bandit. Nice work, pup.",
    "Owner: That's the Hendersons' trash panda. Not tonight!",
]
LINES_LOST = [
    "Owner: My flowers! Biscuit, where were you?",
    "Owner: Another one gone... come on, buddy.",
    "Owner: Those were prize petunias!",
    "Owner: I just planted those!",
]
LINES_STOLEN = [
    "Owner: Hey! That biscuit was for the DOG!",
    "Owner: That squirrel just took your treat! Get it back!",
]
LINES_DAY = [
    "Owner: Another morning, another squirrel. Let's go, Biscuit.",
    "Owner: The garden's looking good. Keep it up, pup!",
    "Owner: Rise and shine. The yard won't guard itself.",
    "Owner: Mailman's been. Now it's just us and the squirrels.",
]
LINES_NIGHT = [
    "Owner: Getting dark. Keep your ears up tonight, Biscuit.",
    "Owner: I hear rustling by the fence... stay sharp, pup.",
    "Owner: Porch light's on. Something's been at the trash cans.",
]
LINES_IDLE = [
    "*sniff sniff*",
    "A bird lands on the fence. Not your problem.",
    "Owner: Who's a good boy? You are. Yes you are.",
    "The wind rustles the leaves. Was that something moving?",
    "*scratch scratch* Ahh. Right there.",
    "Owner: Biscuit, stop eating grass.",
    "A butterfly drifts across the yard. Tempting.",
    "Owner: You're such a good dog, Biscuit. The best dog.",
    "Down the street another dog barks. You consider replying.",
]
