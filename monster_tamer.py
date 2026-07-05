"""
MONSTER TAMER - Graphical Edition (Pygame)
An original creature-catching / battling game with a walkable overworld,
tall-grass encounters, NPC trainers, a Pokecenter tile, a shop, and a
full battle screen with colored HP bars and drawn creature sprites.

Install pygame first:
    pip install pygame

Run:
    python monster_tamer_graphical.py

Controls (overworld):
    Arrow keys / WASD - move
    T                 - open/close team screen
    ESC               - quit

Controls (battle):
    1-4               - choose move / menu option
    F                 - open Fight menu
    B                 - use a potion (Bag)
    C                 - throw a monster ball (Catch, wild battles only)
    R                 - run (wild battles only)
    SPACE / ENTER     - advance messages
"""

import math
import random
import sys

import pygame

# ----------------------------- CONSTANTS ----------------------------- #

TILE = 48
COLS, ROWS = 16, 10
MAP_W, MAP_H = COLS * TILE, ROWS * TILE
UI_H = 200
SCREEN_W, SCREEN_H = MAP_W, MAP_H + UI_H
FPS = 30

# Colors
WHITE = (245, 245, 250)
BLACK = (20, 20, 25)
DARK = (35, 35, 45)
PANEL_BG = (30, 32, 45)
PANEL_BORDER = (90, 95, 130)
PATH_COLOR = (214, 194, 145)
GRASS_COLOR = (146, 200, 96)
TALLGRASS_COLOR = (86, 150, 66)
TREE_COLOR = (46, 92, 48)
CENTER_COLOR = (250, 235, 235)
CENTER_ROOF = (210, 70, 70)
SHOP_COLOR = (235, 225, 190)
SHOP_ROOF = (90, 110, 190)
PLAYER_COLOR = (60, 100, 210)
TEXT_COLOR = (235, 235, 245)
HP_GREEN = (80, 200, 100)
HP_YELLOW = (235, 200, 60)
HP_RED = (220, 70, 70)

TYPE_COLORS = {
    "Fire": (225, 95, 55),
    "Water": (60, 130, 225),
    "Grass": (70, 175, 90),
    "Electric": (240, 210, 50),
    "Normal": (185, 180, 165),
}

# Tile legend
# '#' tree/wall   '.' path   ',' tall grass   'C' pokecenter   'S' shop
MAP_LAYOUT = [
    "################",
    "#..,,,,,,,,,,,.#",
    "#..,,,,,,,,,,,.#",
    "#..,,,,,,,,,,,.#",
    "#..,,,,,,,,,,,.#",
    "#..,,,,,,,,,,,.#",
    "#..,,,,,,,,,,,.#",
    "#..............#",
    "#......C...S...#",
    "################",
]

FONT_NAME = None  # default pygame font


# ----------------------------- GAME DATA ----------------------------- #

TYPE_CHART = {
    "Fire":     {"Grass": 2.0, "Water": 0.5, "Fire": 0.5, "Electric": 1.0, "Normal": 1.0},
    "Water":    {"Fire": 2.0, "Grass": 0.5, "Water": 0.5, "Electric": 1.0, "Normal": 1.0},
    "Grass":    {"Water": 2.0, "Fire": 0.5, "Grass": 0.5, "Electric": 1.0, "Normal": 1.0},
    "Electric": {"Water": 2.0, "Grass": 0.5, "Electric": 0.5, "Fire": 1.0, "Normal": 1.0},
    "Normal":   {"Fire": 1.0, "Water": 1.0, "Grass": 1.0, "Electric": 1.0, "Normal": 1.0},
}


class Move:
    def __init__(self, name, move_type, power, accuracy, pp):
        self.name = name
        self.type = move_type
        self.power = power
        self.accuracy = accuracy
        self.max_pp = pp
        self.pp = pp


MOVES = {
    "Ember":         Move("Ember", "Fire", 40, 100, 25),
    "Flame Burst":   Move("Flame Burst", "Fire", 70, 90, 10),
    "Water Jet":     Move("Water Jet", "Water", 40, 100, 25),
    "Aqua Blast":    Move("Aqua Blast", "Water", 70, 90, 10),
    "Vine Whip":     Move("Vine Whip", "Grass", 40, 100, 25),
    "Leaf Storm":    Move("Leaf Storm", "Grass", 70, 90, 10),
    "Spark":         Move("Spark", "Electric", 40, 100, 25),
    "Thunder Shock": Move("Thunder Shock", "Electric", 70, 90, 10),
    "Tackle":        Move("Tackle", "Normal", 35, 100, 30),
    "Quick Strike":  Move("Quick Strike", "Normal", 25, 100, 30),
    "Body Slam":     Move("Body Slam", "Normal", 60, 90, 15),
    "Bite":          Move("Bite", "Normal", 45, 95, 20),
}


class Species:
    def __init__(self, name, ctype, base_hp, base_atk, base_def, base_spd, move_names, catch_rate):
        self.name = name
        self.type = ctype
        self.base_hp = base_hp
        self.base_atk = base_atk
        self.base_def = base_def
        self.base_spd = base_spd
        self.move_names = move_names
        self.catch_rate = catch_rate


SPECIES = {
    "Flambit":    Species("Flambit", "Fire", 38, 12, 8, 12, ["Ember", "Tackle", "Flame Burst", "Quick Strike"], 0.35),
    "Aquafin":    Species("Aquafin", "Water", 42, 10, 10, 9, ["Water Jet", "Tackle", "Aqua Blast", "Bite"], 0.35),
    "Leafkit":    Species("Leafkit", "Grass", 40, 11, 11, 8, ["Vine Whip", "Tackle", "Leaf Storm", "Quick Strike"], 0.35),
    "Sparklet":   Species("Sparklet", "Electric", 35, 13, 7, 15, ["Spark", "Quick Strike", "Thunder Shock", "Tackle"], 0.30),
    "Rockhide":   Species("Rockhide", "Normal", 45, 9, 14, 6, ["Tackle", "Body Slam", "Bite", "Quick Strike"], 0.45),
    "Puffowl":    Species("Puffowl", "Normal", 32, 10, 8, 16, ["Quick Strike", "Tackle", "Bite", "Body Slam"], 0.50),
    "Emberdrake": Species("Emberdrake", "Fire", 50, 15, 10, 10, ["Flame Burst", "Ember", "Body Slam", "Quick Strike"], 0.15),
    "Tidalor":    Species("Tidalor", "Water", 55, 14, 12, 8, ["Aqua Blast", "Water Jet", "Body Slam", "Bite"], 0.15),
    "Thornback":  Species("Thornback", "Grass", 52, 13, 13, 7, ["Leaf Storm", "Vine Whip", "Body Slam", "Tackle"], 0.15),
    "Voltusk":    Species("Voltusk", "Electric", 44, 16, 9, 17, ["Thunder Shock", "Spark", "Bite", "Quick Strike"], 0.12),
}

SPECIES["Titanflare"] = Species(
    "Titanflare", "Fire", 90, 20, 16, 14,
    ["Flame Burst", "Body Slam", "Bite", "Ember"], 0.05
)

WILD_POOL = ["Flambit", "Aquafin", "Leafkit", "Sparklet", "Rockhide", "Puffowl"]


class Creature:
    def __init__(self, species_name, level=5):
        sp = SPECIES[species_name]
        self.species_name = species_name
        self.type = sp.type
        self.level = level

        self.max_hp = sp.base_hp + level * 3
        self.hp = self.max_hp
        self.attack = sp.base_atk + level
        self.defense = sp.base_def + level
        self.speed = sp.base_spd + level
        self.catch_rate = sp.catch_rate

        self.exp = 0
        self.exp_to_next = level * 20

        self.moves = [MOVES[m] for m in sp.move_names]
        for m in self.moves:
            m.pp = m.max_pp

    @property
    def is_fainted(self):
        return self.hp <= 0

    def take_damage(self, dmg):
        self.hp = max(0, self.hp - dmg)

    def heal_full(self):
        self.hp = self.max_hp
        for m in self.moves:
            m.pp = m.max_pp

    def gain_exp(self, amount):
        self.exp += amount
        leveled = False
        while self.exp >= self.exp_to_next:
            self.exp -= self.exp_to_next
            self.level_up()
            leveled = True
        return leveled

    def level_up(self):
        self.level += 1
        hp_gain = 3 + random.randint(0, 2)
        self.max_hp += hp_gain
        self.hp += hp_gain
        self.attack += 1 + random.randint(0, 1)
        self.defense += 1 + random.randint(0, 1)
        self.speed += 1 + random.randint(0, 1)
        self.exp_to_next = self.level * 20


def type_multiplier(atk_type, def_type):
    return TYPE_CHART.get(atk_type, {}).get(def_type, 1.0)


def make_wild_creature(min_level, max_level):
    return Creature(random.choice(WILD_POOL), random.randint(min_level, max_level))


def perform_attack(attacker, move, defender, log):
    if move.pp > 0:
        move.pp -= 1
    if random.randint(1, 100) > move.accuracy:
        log.append(f"{attacker.species_name}'s {move.name} missed!")
        return
    mult = type_multiplier(move.type, defender.type)
    base = (2 * attacker.level / 5 + 2) * move.power * (attacker.attack / max(1, defender.defense)) / 50 + 2
    dmg = max(1, int(base * mult * random.uniform(0.85, 1.0)))
    defender.take_damage(dmg)
    log.append(f"{attacker.species_name} used {move.name}!")
    if mult > 1:
        log.append("It's super effective!")
    elif mult < 1:
        log.append("It's not very effective...")
    log.append(f"{defender.species_name} took {dmg} damage.")


# ----------------------------- PLAYER / TRAINERS ----------------------------- #

class Player:
    def __init__(self, name, starter_name):
        self.name = name
        self.team = [Creature(starter_name, level=5)]
        self.pokeballs = 5
        self.potions = 3
        self.money = 60
        self.badges = 0
        self.grid_x, self.grid_y = 2, 7
        self.facing = "down"

    @property
    def active(self):
        for c in self.team:
            if not c.is_fainted:
                return c
        return None

    def has_usable_creature(self):
        return any(not c.is_fainted for c in self.team)

    def heal_team(self):
        for c in self.team:
            c.heal_full()


def build_trainers():
    return [
        {"pos": (3, 7), "name": "Youngster Alex",
         "team": [Creature("Puffowl", 6), Creature("Rockhide", 7)],
         "reward": 30, "gives_badge": False, "defeated": False},
        {"pos": (6, 7), "name": "Camper Riya",
         "team": [Creature("Leafkit", 9), Creature("Sparklet", 9)],
         "reward": 50, "gives_badge": False, "defeated": False},
        {"pos": (9, 7), "name": "Ace Trainer Dev",
         "team": [Creature("Emberdrake", 12), Creature("Tidalor", 12), Creature("Thornback", 12)],
         "reward": 100, "gives_badge": True, "defeated": False},
        {"pos": (12, 7), "name": "Champion Meera",
         "team": [Creature("Voltusk", 16), Creature("Emberdrake", 16),
                  Creature("Tidalor", 16), Creature("Thornback", 16)],
         "reward": 300, "gives_badge": True, "defeated": False, "champion": True},
        {"pos": (7, 1), "name": "Titanflare (Boss)",
         "team": [Creature("Titanflare", 22)],
         "reward": 500, "gives_badge": False, "defeated": False, "is_boss": True},
    ]


SHOPKEEPER_POS = (11, 8)


# ----------------------------- DRAW HELPERS ----------------------------- #

def draw_text(surface, text, pos, font, color=TEXT_COLOR):
    surface.blit(font.render(text, True, color), pos)


def draw_hp_bar(surface, x, y, w, h, hp, max_hp):
    pct = max(0, hp / max_hp) if max_hp else 0
    color = HP_GREEN if pct > 0.5 else (HP_YELLOW if pct > 0.2 else HP_RED)
    pygame.draw.rect(surface, (50, 50, 60), (x, y, w, h), border_radius=4)
    pygame.draw.rect(surface, color, (x, y, int(w * pct), h), border_radius=4)
    pygame.draw.rect(surface, (15, 15, 20), (x, y, w, h), width=2, border_radius=4)


def _shade(color, amount):
    return tuple(max(0, min(255, c + amount)) for c in color)


def draw_creature_sprite(surface, cx, cy, radius, ctype, facing_left=False, scale=1.0):
    radius = int(radius * scale)
    color = TYPE_COLORS.get(ctype, (180, 180, 180))
    dark = _shade(color, -55)
    light = _shade(color, 45)

    # ground shadow
    pygame.draw.ellipse(surface, (25, 25, 30), (cx - radius, cy + radius - 6, radius * 2, 14))

    # feet
    foot_w, foot_h = radius // 2, radius // 4
    pygame.draw.ellipse(surface, dark, (cx - radius // 2 - foot_w // 2, cy + radius - 6, foot_w, foot_h))
    pygame.draw.ellipse(surface, dark, (cx + radius // 2 - foot_w // 2, cy + radius - 6, foot_w, foot_h))

    # ears (species-flavored by type)
    if ctype == "Fire":
        pygame.draw.polygon(surface, dark, [(cx - radius + 4, cy - radius + 10),
                                             (cx - radius - 6, cy - radius - 14),
                                             (cx - radius + 16, cy - radius + 2)])
        pygame.draw.polygon(surface, dark, [(cx + radius - 4, cy - radius + 10),
                                             (cx + radius + 6, cy - radius - 14),
                                             (cx + radius - 16, cy - radius + 2)])
    elif ctype == "Electric":
        pygame.draw.polygon(surface, dark, [(cx - radius + 6, cy - radius + 6),
                                             (cx - radius - 10, cy - radius - 6),
                                             (cx - radius + 4, cy - radius - 10),
                                             (cx - radius + 18, cy - radius + 4)])
        pygame.draw.polygon(surface, dark, [(cx + radius - 6, cy - radius + 6),
                                             (cx + radius + 10, cy - radius - 6),
                                             (cx + radius - 4, cy - radius - 10),
                                             (cx + radius - 18, cy - radius + 4)])
    else:
        pygame.draw.circle(surface, dark, (cx - radius + 6, cy - radius + 10), radius // 4)
        pygame.draw.circle(surface, dark, (cx + radius - 6, cy - radius + 10), radius // 4)

    # main body with a lighter belly patch for depth
    pygame.draw.circle(surface, color, (cx, cy), radius)
    pygame.draw.ellipse(surface, light, (cx - radius // 2, cy - 2, radius, radius // 1.4))
    pygame.draw.circle(surface, dark, (cx, cy), radius, width=4)

    # cheeks / blush
    blush_col = _shade(color, 60)
    pygame.draw.circle(surface, blush_col, (cx - radius + radius // 3, cy + radius // 6), max(3, radius // 7))
    pygame.draw.circle(surface, blush_col, (cx + radius - radius // 3, cy + radius // 6), max(3, radius // 7))

    # eyes
    eye_offset = radius // 3
    eye_y = cy - radius // 6
    er = max(4, radius // 6)
    for sign in (-1, 1):
        ex = cx + sign * eye_offset
        pygame.draw.circle(surface, WHITE, (ex, eye_y), er)
        pupil_shift = -2 if facing_left else 2
        pygame.draw.circle(surface, BLACK, (ex + pupil_shift, eye_y), max(2, er // 2))

    # simple mouth
    pygame.draw.arc(surface, dark, (cx - radius // 3, cy + radius // 6, radius * 2 // 3, radius // 3),
                     3.5, 6.0, 2)

    # type-flavored head accent
    if ctype == "Fire":
        pts = [(cx, cy - radius - 10), (cx - 7, cy - radius + 6), (cx + 7, cy - radius + 6)]
        pygame.draw.polygon(surface, (255, 175, 70), pts)
    elif ctype == "Water":
        pygame.draw.polygon(surface, (150, 210, 255),
                             [(cx - 6, cy - radius + 2), (cx + 6, cy - radius + 2), (cx, cy - radius - 12)])
    elif ctype == "Grass":
        pygame.draw.polygon(surface, (120, 220, 130),
                             [(cx - 7, cy - radius), (cx + 7, cy - radius), (cx, cy - radius - 16)])
        pygame.draw.polygon(surface, (100, 200, 110),
                             [(cx - 14, cy - radius + 6), (cx - 2, cy - radius + 2), (cx - 6, cy - radius + 14)])
    elif ctype == "Electric":
        pygame.draw.polygon(surface, (255, 240, 120),
                             [(cx - 4, cy - radius - 14), (cx + 7, cy - radius), (cx - 1, cy - radius),
                              (cx + 5, cy - radius + 12)])


SKIN_COLOR = (235, 190, 150)
HAIR_COLOR = (60, 40, 30)
SHIRT_COLOR = (60, 110, 200)
PANTS_COLOR = (50, 55, 70)
CAP_COLOR = (200, 60, 60)


def draw_player_sprite(surface, x, y, facing):
    cx, cy = x + TILE // 2, y + TILE // 2

    # shadow
    pygame.draw.ellipse(surface, (25, 25, 30), (cx - 14, y + TILE - 10, 28, 8))

    # legs
    leg_off = 4 if facing in ("left", "right") else 6
    pygame.draw.rect(surface, PANTS_COLOR, (cx - leg_off - 3, cy + 6, 6, 12), border_radius=2)
    pygame.draw.rect(surface, PANTS_COLOR, (cx + leg_off - 3, cy + 6, 6, 12), border_radius=2)

    # arms
    arm_dx = 12 if facing in ("left", "right") else 10
    pygame.draw.circle(surface, SKIN_COLOR, (cx - arm_dx, cy + 2), 4)
    pygame.draw.circle(surface, SKIN_COLOR, (cx + arm_dx, cy + 2), 4)

    # torso (shirt)
    torso = pygame.Rect(cx - 11, cy - 8, 22, 20)
    pygame.draw.rect(surface, SHIRT_COLOR, torso, border_radius=7)
    pygame.draw.rect(surface, _shade(SHIRT_COLOR, -40), torso, width=2, border_radius=7)

    # head (skin)
    head_r = 11
    head_cy = cy - 16
    pygame.draw.circle(surface, SKIN_COLOR, (cx, head_cy), head_r)

    # hair peeking out from under the cap
    pygame.draw.rect(surface, HAIR_COLOR, (cx - head_r, head_cy, head_r * 2, 6))

    # face direction: eyes shift, and cap brim points the way you're facing
    if facing == "down":
        eye_dx, brim = 4, (cx - 6, head_cy + 2, 12, 5)
    elif facing == "up":
        eye_dx, brim = None, (cx - 6, head_cy - 12, 12, 5)
    elif facing == "left":
        eye_dx, brim = -3, (cx - 14, head_cy - 2, 8, 5)
    else:
        eye_dx, brim = 3, (cx + 6, head_cy - 2, 8, 5)

    if eye_dx is not None:
        pygame.draw.circle(surface, BLACK, (cx - 4, head_cy + 1), 1)
        pygame.draw.circle(surface, BLACK, (cx + 4, head_cy + 1), 1)

    # cap
    pygame.draw.circle(surface, CAP_COLOR, (cx, head_cy - 4), head_r - 1)
    pygame.draw.ellipse(surface, CAP_COLOR, brim)
    pygame.draw.circle(surface, _shade(CAP_COLOR, 60), (cx, head_cy - 10), 3)


# ----------------------------- MAIN GAME CLASS ----------------------------- #

class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Monster Tamer")
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(FONT_NAME, 20)
        self.font_small = pygame.font.Font(FONT_NAME, 16)
        self.font_big = pygame.font.Font(FONT_NAME, 28)

        self.state = "NAME_ENTRY"
        self.name_input = ""
        self.starter_choice = 0
        self.starters = ["Flambit", "Aquafin", "Leafkit", "Sparklet"]

        self.player = None
        self.trainers = build_trainers()

        self.messages = []
        self.msg_index = 0
        self.after_messages = None

        self.battle = None  # dict holding battle context
        self.team_cursor = 0
        self.shop_cursor = 0
        self.anim = None  # active animation (e.g. catch throw/shake)

    # ---------------- setup ---------------- #

    def start_game(self, name, starter):
        self.player = Player(name or "Trainer", starter)
        self.state = "MAP"
        self.push_message(f"Welcome, {self.player.name}! Explore, catch creatures, and beat every trainer.")

    def push_message(self, *lines, after=None):
        self.messages = list(lines)
        self.msg_index = 0
        self.after_messages = after
        self.state = "MESSAGE"

    def advance_message(self):
        self.msg_index += 1
        if self.msg_index >= len(self.messages):
            after = self.after_messages
            self.after_messages = None
            if after == "return_map":
                self.state = "MAP"
            elif after == "return_battle":
                self.state = "BATTLE"
                self.battle["menu"] = "MAIN"
            elif after == "battle_check":
                self.resolve_battle_state()
            elif after == "start_battle":
                self.state = "BATTLE"
            elif callable(after):
                after()
            else:
                self.state = "MAP"

    # ---------------- map logic ---------------- #

    def tile_at(self, gx, gy):
        if 0 <= gy < len(MAP_LAYOUT) and 0 <= gx < len(MAP_LAYOUT[0]):
            return MAP_LAYOUT[gy][gx]
        return "#"

    def trainer_at(self, gx, gy):
        for t in self.trainers:
            if t["pos"] == (gx, gy):
                return t
        return None

    def try_move(self, dx, dy):
        p = self.player
        if dx == -1:
            p.facing = "left"
        elif dx == 1:
            p.facing = "right"
        elif dy == -1:
            p.facing = "up"
        elif dy == 1:
            p.facing = "down"

        nx, ny = p.grid_x + dx, p.grid_y + dy
        tile = self.tile_at(nx, ny)

        trainer = self.trainer_at(nx, ny)
        if trainer is not None:
            gated = trainer.get("champion") or trainer.get("is_boss")
            if gated and not all(t["defeated"] for t in self.trainers if t is not trainer):
                who = trainer["name"]
                self.push_message(f"{who}: \"Beat every other trainer here first!\"", after="return_map")
                return
            if not trainer["defeated"]:
                self.start_trainer_battle(trainer)
            return

        if self.shopkeeper_at(nx, ny):
            self.open_shop()
            return

        if tile == "#":
            return  # blocked

        p.grid_x, p.grid_y = nx, ny

        if tile == "C":
            self.player.heal_team()
            self.push_message("Your team was fully healed. Good luck out there!", after="return_map")
        elif tile == ",":
            if random.random() < 0.14:
                level_range = (3 + p.badges * 2, 8 + p.badges * 3)
                wild = make_wild_creature(*level_range)
                self.start_wild_battle(wild)

    def shopkeeper_at(self, gx, gy):
        return (gx, gy) == SHOPKEEPER_POS

    def open_shop(self):
        self.shop_cursor = 0
        self.state = "SHOP"

    # ---------------- battle setup ---------------- #

    def start_wild_battle(self, wild):
        if not self.player.has_usable_creature():
            self.push_message("All your creatures have fainted! Heal up at the Pokecenter.", after="return_map")
            return
        self.battle = {
            "is_trainer": False,
            "trainer": None,
            "enemy_team": [wild],
            "enemy_idx": 0,
            "enemy": wild,
            "menu": "MAIN",
        }
        self.push_message(f"A wild {wild.species_name} (Lv.{wild.level}) appeared!", after="start_battle")

    def start_trainer_battle(self, trainer):
        if not self.player.has_usable_creature():
            self.push_message("All your creatures have fainted! Heal up at the Pokecenter.", after="return_map")
            return
        for c in trainer["team"]:
            c.heal_full()
        self.battle = {
            "is_trainer": True,
            "trainer": trainer,
            "enemy_team": trainer["team"],
            "enemy_idx": 0,
            "enemy": trainer["team"][0],
            "menu": "MAIN",
        }
        if trainer.get("is_boss"):
            self.push_message(
                "The ground shakes...",
                f"{trainer['name']} emerges, towering and furious!",
                "This is going to be a tough fight!",
                after="start_battle",
            )
        else:
            self.push_message(f"Trainer {trainer['name']} wants to battle!", after="start_battle")

    def current_enemy(self):
        return self.battle["enemy"]

    # ---------------- battle actions ---------------- #

    def do_move(self, move_index):
        mine = self.player.active
        if mine is None:
            return
        usable = [m for m in mine.moves if m.pp > 0]
        if not usable:
            move = Move("Struggle", "Normal", 20, 100, 1)
        else:
            if move_index >= len(mine.moves):
                return
            move = mine.moves[move_index]
            if move.pp <= 0:
                return

        enemy = self.current_enemy()
        log = []
        if mine.speed >= enemy.speed:
            perform_attack(mine, move, enemy, log)
            if not enemy.is_fainted:
                enemy_move = random.choice([m for m in enemy.moves if m.pp > 0] or enemy.moves)
                perform_attack(enemy, enemy_move, mine, log)
        else:
            enemy_move = random.choice([m for m in enemy.moves if m.pp > 0] or enemy.moves)
            perform_attack(enemy, enemy_move, mine, log)
            if not mine.is_fainted:
                perform_attack(mine, move, enemy, log)

        if enemy.is_fainted:
            log.append(f"{enemy.species_name} fainted!")
            exp_gain = enemy.level * 8
            leveled = mine.gain_exp(exp_gain)
            log.append(f"{mine.species_name} gained {exp_gain} EXP!")
            if leveled:
                log.append(f"{mine.species_name} grew to level {mine.level}!")
        if mine.is_fainted:
            log.append(f"{mine.species_name} fainted!")

        self.push_message(*log, after="battle_check")

    def use_potion(self):
        p = self.player
        mine = p.active
        if mine is None:
            return
        if p.potions <= 0:
            self.push_message("You have no potions left!", after="return_battle")
            return
        p.potions -= 1
        heal = 20
        mine.hp = min(mine.max_hp, mine.hp + heal)
        log = [f"You used a potion! {mine.species_name} recovered {heal} HP."]
        enemy = self.current_enemy()
        enemy_move = random.choice([m for m in enemy.moves if m.pp > 0] or enemy.moves)
        perform_attack(enemy, enemy_move, mine, log)
        if mine.is_fainted:
            log.append(f"{mine.species_name} fainted!")
        self.push_message(*log, after="battle_check")

    def try_catch(self):
        p = self.player
        wild = self.current_enemy()
        if p.pokeballs <= 0:
            self.push_message("You're out of monster balls!", after="return_battle")
            return
        p.pokeballs -= 1
        hp_factor = 1 - (wild.hp / wild.max_hp) * 0.65
        chance = min(0.95, wild.catch_rate + hp_factor)
        success = random.random() < chance
        # more shakes for a closer call, always at least 1
        shakes = 3 if success else random.randint(1, 2)

        self.anim = {
            "type": "catch",
            "start": pygame.time.get_ticks(),
            "success": success,
            "wild": wild,
            "shakes": shakes,
        }
        self.state = "CATCH_ANIM"

    def finish_catch_animation(self):
        p = self.player
        wild = self.anim["wild"]
        success = self.anim["success"]
        self.anim = None

        if success:
            if len(p.team) < 6:
                p.team.append(wild)
                msg = f"Gotcha! {wild.species_name} was caught and added to your team!"
            else:
                msg = f"Gotcha! {wild.species_name} was caught, but your team is full (it wasn't kept)."
            self.push_message(msg, after="battle_end_win")
        else:
            log = [f"Oh no! The {wild.species_name} broke free!"]
            enemy_move = random.choice([m for m in wild.moves if m.pp > 0] or wild.moves)
            mine = p.active
            perform_attack(wild, enemy_move, mine, log)
            if mine.is_fainted:
                log.append(f"{mine.species_name} fainted!")
            self.push_message(*log, after="battle_check")

    def run_away(self):
        if self.battle["is_trainer"]:
            self.push_message("You can't run from a trainer battle!", after="return_battle")
            return
        self.push_message("Got away safely!", after="battle_end_flee")

    def switch_to(self, index):
        p = self.player
        if index >= len(p.team):
            return
        picked = p.team[index]
        if picked.is_fainted:
            self.push_message(f"{picked.species_name} has fainted and can't battle!", after="return_battle")
            return
        p.team.remove(picked)
        p.team.insert(0, picked)
        self.push_message(f"Go, {picked.species_name}!", after="return_battle")
        self.battle["menu"] = "MAIN"

    def resolve_battle_state(self):
        p = self.player
        b = self.battle
        enemy = b["enemy"]

        if enemy.is_fainted:
            b["enemy_idx"] += 1
            if b["enemy_idx"] >= len(b["enemy_team"]):
                self.finish_battle(win=True)
                return
            b["enemy"] = b["enemy_team"][b["enemy_idx"]]
            name = b["trainer"]["name"] if b["is_trainer"] else "The wild creature"
            self.push_message(f"{name} sent out {b['enemy'].species_name} (Lv.{b['enemy'].level})!",
                               after="return_battle")
            return

        mine = p.active
        if mine is None or mine.is_fainted:
            if not p.has_usable_creature():
                self.finish_battle(win=False)
                return
            self.state = "BATTLE"
            self.battle["menu"] = "FORCE_SWITCH"
            return

        self.state = "BATTLE"
        self.battle["menu"] = "MAIN"

    def finish_battle(self, win):
        p = self.player
        b = self.battle
        if win:
            if b["is_trainer"]:
                reward = b["trainer"].get("reward", 20)
                p.money += reward
                b["trainer"]["defeated"] = True
                lines = [f"You defeated {b['trainer']['name']}!", f"You received ${reward}."]
                if b["trainer"].get("gives_badge"):
                    p.badges += 1
                    lines.append(f"You earned a badge! ({p.badges} total)")
                if b["trainer"].get("champion"):
                    lines.append("You are the new Champion! Thanks for playing Monster Tamer!")
            else:
                lines = ["The wild creature was defeated!"]
        else:
            lines = ["All your creatures have fainted. You blacked out!", "Better luck next time — heal up and try again."]
            for c in p.team:
                c.heal_full()
            p.grid_x, p.grid_y = 2, 7

        self.battle = None
        self.push_message(*lines, after="return_map")

    # ---------------- input handling ---------------- #

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return

        if self.state == "NAME_ENTRY":
            self.handle_name_entry(event)
        elif self.state == "STARTER_SELECT":
            self.handle_starter_select(event)
        elif self.state == "MAP":
            self.handle_map_input(event)
        elif self.state == "MESSAGE":
            if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                self.advance_message()
        elif self.state == "BATTLE":
            self.handle_battle_input(event)
        elif self.state == "TEAM":
            if event.key in (pygame.K_t, pygame.K_ESCAPE):
                self.state = "MAP"
        elif self.state == "SHOP":
            self.handle_shop_input(event)

    def handle_name_entry(self, event):
        if event.key == pygame.K_RETURN:
            self.state = "STARTER_SELECT"
        elif event.key == pygame.K_BACKSPACE:
            self.name_input = self.name_input[:-1]
        elif event.unicode.isprintable() and len(self.name_input) < 12:
            self.name_input += event.unicode

    def handle_starter_select(self, event):
        if event.key in (pygame.K_LEFT, pygame.K_a):
            self.starter_choice = (self.starter_choice - 1) % len(self.starters)
        elif event.key in (pygame.K_RIGHT, pygame.K_d):
            self.starter_choice = (self.starter_choice + 1) % len(self.starters)
        elif event.key == pygame.K_RETURN:
            self.start_game(self.name_input, self.starters[self.starter_choice])

    def handle_map_input(self, event):
        if event.key in (pygame.K_UP, pygame.K_w):
            self.try_move(0, -1)
        elif event.key in (pygame.K_DOWN, pygame.K_s):
            self.try_move(0, 1)
        elif event.key in (pygame.K_LEFT, pygame.K_a):
            self.try_move(-1, 0)
        elif event.key in (pygame.K_RIGHT, pygame.K_d):
            self.try_move(1, 0)
        elif event.key == pygame.K_t:
            self.team_cursor = 0
            self.state = "TEAM"
        elif event.key == pygame.K_ESCAPE:
            pygame.quit()
            sys.exit(0)

    def handle_battle_input(self, event):
        menu = self.battle["menu"]
        if menu == "MAIN":
            if event.key == pygame.K_f or event.key == pygame.K_1:
                self.battle["menu"] = "MOVES"
            elif event.key == pygame.K_2:
                self.battle["menu"] = "SWITCH"
            elif event.key == pygame.K_b or event.key == pygame.K_3:
                self.use_potion()
            elif event.key == pygame.K_c or event.key == pygame.K_4:
                if not self.battle["is_trainer"]:
                    self.try_catch()
            elif event.key == pygame.K_r or event.key == pygame.K_5:
                self.run_away()
        elif menu == "MOVES":
            if event.key == pygame.K_ESCAPE:
                self.battle["menu"] = "MAIN"
            elif pygame.K_1 <= event.key <= pygame.K_4:
                self.do_move(event.key - pygame.K_1)
        elif menu in ("SWITCH", "FORCE_SWITCH"):
            if event.key == pygame.K_ESCAPE and menu == "SWITCH":
                self.battle["menu"] = "MAIN"
            elif pygame.K_1 <= event.key <= pygame.K_6:
                self.switch_to(event.key - pygame.K_1)

    def handle_shop_input(self, event):
        p = self.player
        if event.key == pygame.K_1:
            if p.money >= 10:
                p.money -= 10
                p.pokeballs += 1
        elif event.key == pygame.K_2:
            if p.money >= 15:
                p.money -= 15
                p.potions += 1
        elif event.key in (pygame.K_ESCAPE, pygame.K_3):
            self.state = "MAP"

    # ---------------- drawing ---------------- #

    def draw(self):
        screen = self.screen
        screen.fill(DARK)

        if self.state == "NAME_ENTRY":
            self.draw_name_entry()
        elif self.state == "STARTER_SELECT":
            self.draw_starter_select()
        else:
            self.draw_map()
            if self.state in ("BATTLE", "CATCH_ANIM"):
                self.draw_battle()
            elif self.state == "TEAM":
                self.draw_team()
            elif self.state == "SHOP":
                self.draw_shop()
            self.draw_bottom_panel()

        pygame.display.flip()

    def draw_name_entry(self):
        draw_text(self.screen, "MONSTER TAMER", (SCREEN_W // 2 - 140, 120), self.font_big)
        draw_text(self.screen, "What is your name, trainer?", (SCREEN_W // 2 - 160, 220), self.font)
        pygame.draw.rect(self.screen, PANEL_BG, (SCREEN_W // 2 - 150, 260, 300, 40), border_radius=6)
        pygame.draw.rect(self.screen, PANEL_BORDER, (SCREEN_W // 2 - 150, 260, 300, 40), width=2, border_radius=6)
        draw_text(self.screen, self.name_input + "|", (SCREEN_W // 2 - 140, 270), self.font)
        draw_text(self.screen, "Press ENTER to continue", (SCREEN_W // 2 - 140, 320), self.font_small)

    def draw_starter_select(self):
        draw_text(self.screen, "Choose your starter", (SCREEN_W // 2 - 130, 60), self.font_big)
        spacing = 160
        start_x = SCREEN_W // 2 - (len(self.starters) * spacing) // 2 + spacing // 2
        for i, s in enumerate(self.starters):
            sp = SPECIES[s]
            x = start_x + i * spacing
            y = 220
            selected = (i == self.starter_choice)
            if selected:
                pygame.draw.rect(self.screen, PANEL_BORDER, (x - 55, y - 55, 110, 150), border_radius=10)
            draw_creature_sprite(self.screen, x, y, 40, sp.type)
            draw_text(self.screen, s, (x - self.font.size(s)[0] // 2, y + 55), self.font_small)
            draw_text(self.screen, sp.type, (x - self.font.size(sp.type)[0] // 2, y + 75), self.font_small,
                      TYPE_COLORS[sp.type])
        draw_text(self.screen, "<- / -> to choose, ENTER to confirm", (SCREEN_W // 2 - 170, 400), self.font_small)

    def draw_map(self):
        for gy, row in enumerate(MAP_LAYOUT):
            for gx, ch in enumerate(row):
                x, y = gx * TILE, gy * TILE
                if ch == "#":
                    color = TREE_COLOR
                elif ch == ",":
                    color = TALLGRASS_COLOR
                elif ch == "C":
                    color = CENTER_COLOR
                elif ch == "S":
                    color = SHOP_COLOR
                else:
                    color = PATH_COLOR if ch == "." else GRASS_COLOR
                pygame.draw.rect(self.screen, color, (x, y, TILE, TILE))
                if ch == "#":
                    pygame.draw.circle(self.screen, (30, 70, 32), (x + TILE // 2, y + TILE // 2), TILE // 2 - 4)
                if ch == "C":
                    pygame.draw.rect(self.screen, CENTER_ROOF, (x, y, TILE, 12))
                if ch == "S":
                    pygame.draw.rect(self.screen, SHOP_ROOF, (x, y, TILE, 12))

        for t in self.trainers:
            gx, gy = t["pos"]
            x, y = gx * TILE, gy * TILE
            color = (140, 140, 150) if t["defeated"] else (210, 70, 70)
            pygame.draw.rect(self.screen, color, (x + 6, y + 6, TILE - 12, TILE - 12), border_radius=6)
            mark = "x" if t["defeated"] else "!"
            draw_text(self.screen, mark, (x + TILE // 2 - 4, y + 10), self.font_small, WHITE)

        sx, sy = SHOPKEEPER_POS
        pygame.draw.rect(self.screen, (100, 180, 210),
                          (sx * TILE + 6, sy * TILE + 6, TILE - 12, TILE - 12), border_radius=6)
        draw_text(self.screen, "$", (sx * TILE + TILE // 2 - 4, sy * TILE + 10), self.font_small, WHITE)

        p = self.player
        draw_player_sprite(self.screen, p.grid_x * TILE, p.grid_y * TILE, p.facing)

    def draw_bottom_panel(self):
        panel_rect = (0, MAP_H, SCREEN_W, UI_H)
        pygame.draw.rect(self.screen, PANEL_BG, panel_rect)
        pygame.draw.rect(self.screen, PANEL_BORDER, panel_rect, width=3)

        if self.state == "MESSAGE":
            text = self.messages[self.msg_index]
            draw_text(self.screen, text, (20, MAP_H + 20), self.font)
            draw_text(self.screen, f"({self.msg_index + 1}/{len(self.messages)})  SPACE to continue",
                      (20, MAP_H + 60), self.font_small)
        elif self.state == "MAP":
            p = self.player
            draw_text(self.screen, f"{p.name}   Money: ${p.money}   Badges: {p.badges}", (20, MAP_H + 15), self.font)
            draw_text(self.screen, f"Balls: {p.pokeballs}   Potions: {p.potions}", (20, MAP_H + 45), self.font_small)
            draw_text(self.screen,
                      "Arrows/WASD move  |  T: team  |  ESC: quit  |  Walk into shopkeeper ($) or trainers (!)",
                      (20, MAP_H + 80), self.font_small)
            if p.active:
                draw_text(self.screen, f"Lead: {p.active.species_name} Lv.{p.active.level}", (20, MAP_H + 110),
                          self.font_small)
                draw_hp_bar(self.screen, 20, MAP_H + 135, 200, 14, p.active.hp, p.active.max_hp)
                draw_text(self.screen, f"{p.active.hp}/{p.active.max_hp} HP", (230, MAP_H + 133), self.font_small)
        elif self.state == "BATTLE":
            self.draw_battle_menu()
        elif self.state == "CATCH_ANIM":
            draw_text(self.screen, "Throwing Monster Ball...", (20, MAP_H + 20), self.font)

    def draw_battle(self):
        b = self.battle
        p = self.player
        mine = p.active
        enemy = b["enemy"]
        is_boss = bool(b.get("trainer") and b["trainer"].get("is_boss"))

        if is_boss:
            tint = pygame.Surface((MAP_W, MAP_H), pygame.SRCALPHA)
            tint.fill((90, 60, 10, 60))
            self.screen.blit(tint, (0, 0))

        # enemy side (top of map area)
        enemy_scale = 1.5 if is_boss else 1.0
        draw_creature_sprite(self.screen, MAP_W - 150, 120, 50, enemy.type, facing_left=True, scale=enemy_scale)
        pygame.draw.rect(self.screen, PANEL_BG, (20, 20, 240, 70), border_radius=8)
        pygame.draw.rect(self.screen, PANEL_BORDER, (20, 20, 240, 70), width=2, border_radius=8)
        draw_text(self.screen, f"{enemy.species_name} Lv.{enemy.level}", (32, 28), self.font_small)
        draw_hp_bar(self.screen, 32, 55, 200, 14, enemy.hp, enemy.max_hp)

        # player side (bottom of map area)
        if mine:
            draw_creature_sprite(self.screen, 140, MAP_H - 130, 50, mine.type)
            pygame.draw.rect(self.screen, PANEL_BG, (SCREEN_W - 260, MAP_H - 100, 240, 80), border_radius=8)
            pygame.draw.rect(self.screen, PANEL_BORDER, (SCREEN_W - 260, MAP_H - 100, 240, 80), width=2,
                              border_radius=8)
            draw_text(self.screen, f"{mine.species_name} Lv.{mine.level}", (SCREEN_W - 248, MAP_H - 92),
                      self.font_small)
            draw_hp_bar(self.screen, SCREEN_W - 248, MAP_H - 65, 200, 14, mine.hp, mine.max_hp)
            draw_text(self.screen, f"{mine.hp}/{mine.max_hp} HP", (SCREEN_W - 248, MAP_H - 40), self.font_small)
            draw_text(self.screen, f"EXP {mine.exp}/{mine.exp_to_next}", (SCREEN_W - 248, MAP_H - 20),
                      self.font_small)

        if self.state == "CATCH_ANIM":
            self.draw_catch_anim()
        # NOTE: battle menu is drawn by draw_bottom_panel(), AFTER the panel
        # background is painted, so it doesn't get erased.

    def draw_catch_anim(self):
        if not self.anim:
            return
        elapsed = pygame.time.get_ticks() - self.anim["start"]
        start_pos = (140, MAP_H - 130)
        end_pos = (MAP_W - 150, 120)

        ball_r = 12
        if elapsed < self.THROW_MS:
            t = elapsed / self.THROW_MS
            # simple arc: linear interpolation plus a vertical hump
            bx = start_pos[0] + (end_pos[0] - start_pos[0]) * t
            by = start_pos[1] + (end_pos[1] - start_pos[1]) * t - 60 * (1 - (2 * t - 1) ** 2)
            self._draw_ball(bx, by, spin=elapsed)
        elif elapsed < self.THROW_MS + self.SHAKE_MS:
            shake_elapsed = elapsed - self.THROW_MS
            shakes = self.anim["shakes"]
            shake_window = self.SHAKE_MS / max(1, shakes)
            phase = shake_elapsed % shake_window
            wobble = 8 * (1 if int(shake_elapsed / (shake_window / 2)) % 2 == 0 else -1) * (
                1 - phase / shake_window)
            self._draw_ball(end_pos[0] + wobble, end_pos[1] + 30, spin=0)
        else:
            if self.anim["success"]:
                self._draw_sparkle(end_pos[0], end_pos[1])
            else:
                draw_creature_sprite(self.screen, end_pos[0], end_pos[1], 50, self.anim["wild"].type,
                                      facing_left=True)
                self._draw_ball(end_pos[0], end_pos[1] + 40, spin=0)

    def _draw_ball(self, x, y, spin=0):
        x, y = int(x), int(y)
        pygame.draw.circle(self.screen, (220, 60, 60), (x, y), 12)
        pygame.draw.rect(self.screen, WHITE, (x - 12, y, 24, 12))
        pygame.draw.circle(self.screen, (30, 30, 30), (x, y), 12, width=2)
        pygame.draw.line(self.screen, (30, 30, 30), (x - 12, y), (x + 12, y), 2)
        pygame.draw.circle(self.screen, WHITE, (x, y), 4)
        pygame.draw.circle(self.screen, (30, 30, 30), (x, y), 4, width=1)

    def _draw_sparkle(self, x, y):
        for i in range(8):
            ang = i * (3.14159 * 2 / 8)
            r1, r2 = 20, 45
            x1, y1 = x + r1 * math.cos(ang), y + r1 * math.sin(ang)
            x2, y2 = x + r2 * math.cos(ang), y + r2 * math.sin(ang)
            pygame.draw.line(self.screen, (255, 225, 100), (x1, y1), (x2, y2), 3)
        draw_text(self.screen, "Caught!", (x - 30, y - 70), self.font)

    def draw_button(self, x, y, w, h, number, label, color=(55, 60, 85)):
        border = PANEL_BORDER
        pygame.draw.rect(self.screen, color, (x, y, w, h), border_radius=8)
        pygame.draw.rect(self.screen, border, (x, y, w, h), width=2, border_radius=8)
        badge_r = 12
        pygame.draw.circle(self.screen, (240, 200, 60), (x + 20, y + h // 2), badge_r)
        num_surf = self.font_small.render(str(number), True, BLACK)
        self.screen.blit(num_surf, (x + 20 - num_surf.get_width() // 2, y + h // 2 - num_surf.get_height() // 2))
        draw_text(self.screen, label, (x + 40, y + h // 2 - 10), self.font_small)

    def draw_battle_menu(self):
        menu = self.battle["menu"]
        p = self.player
        mine = p.active
        y0 = MAP_H

        if menu == "MAIN":
            options = [("Fight", (90, 60, 55)), ("Switch", (55, 75, 90)), ("Bag", (60, 85, 65))]
            if not self.battle["is_trainer"]:
                options.append(("Catch", (85, 70, 40)))
                options.append(("Run", (75, 55, 85)))
            btn_w, btn_h = 220, 42
            for i, (label, color) in enumerate(options):
                col = i % 3
                row = i // 3
                x = 20 + col * (btn_w + 12)
                y = y0 + 15 + row * (btn_h + 10)
                self.draw_button(x, y, btn_w, btn_h, i + 1, label, color)
        elif menu == "MOVES" and mine:
            btn_w, btn_h = 350, 40
            for i, m in enumerate(mine.moves):
                col = i % 2
                row = i // 2
                x = 20 + col * (btn_w + 12)
                y = y0 + 12 + row * (btn_h + 8)
                label = f"{m.name}  PWR {m.power}  PP {m.pp}/{m.max_pp}"
                color = tuple(max(0, c // 3) for c in TYPE_COLORS.get(m.type, (150, 150, 150)))
                self.draw_button(x, y, btn_w, btn_h, i + 1, label, color)
            draw_text(self.screen, "ESC: back to menu", (20, y0 + 12 + 2 * (btn_h + 8) + 4), self.font_small)
        elif menu in ("SWITCH", "FORCE_SWITCH"):
            if menu == "FORCE_SWITCH":
                draw_text(self.screen, f"{mine.species_name if mine else 'Your creature'} fainted! Choose next:",
                          (20, y0 + 6), self.font_small, HP_RED)
                start_y = y0 + 30
            else:
                start_y = y0 + 10
            btn_w, btn_h = 350, 34
            for i, c in enumerate(p.team):
                col = i % 2
                row = i // 2
                x = 20 + col * (btn_w + 12)
                y = start_y + row * (btn_h + 6)
                tag = " (fainted)" if c.is_fainted else ""
                color = (50, 50, 55) if c.is_fainted else tuple(max(0, ch // 3) for ch in TYPE_COLORS.get(c.type, (150, 150, 150)))
                self.draw_button(x, y, btn_w, btn_h, i + 1, f"{c.species_name} Lv.{c.level}{tag}", color)

    def draw_team(self):
        pygame.draw.rect(self.screen, (0, 0, 0, 160), (0, 0, MAP_W, MAP_H))
        overlay = pygame.Surface((MAP_W, MAP_H), pygame.SRCALPHA)
        overlay.fill((10, 10, 20, 200))
        self.screen.blit(overlay, (0, 0))
        draw_text(self.screen, "Your Team", (30, 20), self.font_big)
        for i, c in enumerate(self.player.team):
            y = 70 + i * 60
            draw_creature_sprite(self.screen, 60, y + 15, 25, c.type)
            draw_text(self.screen, f"{c.species_name}  Lv.{c.level}  ({c.type})", (110, y), self.font_small)
            draw_hp_bar(self.screen, 110, y + 22, 200, 12, c.hp, c.max_hp)
            draw_text(self.screen, f"{c.hp}/{c.max_hp}", (320, y + 20), self.font_small)
        draw_text(self.screen, "Press T or ESC to close", (30, MAP_H - 30), self.font_small)

    def draw_shop(self):
        overlay = pygame.Surface((MAP_W, MAP_H), pygame.SRCALPHA)
        overlay.fill((10, 10, 20, 200))
        self.screen.blit(overlay, (0, 0))
        draw_text(self.screen, "Shop", (30, 20), self.font_big)
        draw_text(self.screen, f"Your money: ${self.player.money}", (30, 60), self.font_small)
        draw_text(self.screen, "1. Monster Ball - $10", (30, 110), self.font_small)
        draw_text(self.screen, "2. Potion - $15", (30, 140), self.font_small)
        draw_text(self.screen, "3 / ESC. Leave", (30, 170), self.font_small)

    # ---------------- main loop ---------------- #

    # Animation timing (ms)
    THROW_MS = 500
    SHAKE_MS = 900
    PAUSE_MS = 400

    def update(self):
        if self.state == "CATCH_ANIM" and self.anim:
            elapsed = pygame.time.get_ticks() - self.anim["start"]
            total = self.THROW_MS + self.SHAKE_MS + self.PAUSE_MS
            if elapsed >= total:
                self.finish_catch_animation()

    def run(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit(0)
                self.handle_event(event)
            self.update()
            self.draw()
            self.clock.tick(FPS)


if __name__ == "__main__":
    Game().run()
