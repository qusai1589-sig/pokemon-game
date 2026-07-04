"""
MONSTER TAMER
A text-based creature-catching and battling game.

Catch wild creatures, build your team, heal up, and battle trainers
on your way to becoming the Champion.

Run with: python monster_tamer.py
"""

import random
import sys
import time


# ----------------------------- DATA ----------------------------- #

TYPE_CHART = {
    # attacker_type: {defender_type: multiplier}
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

    def __str__(self):
        return f"{self.name} ({self.type}, PWR {self.power}, PP {self.pp}/{self.max_pp})"


# A shared move pool, referenced by name when building species
MOVES = {
    "Ember":        Move("Ember", "Fire", 40, 100, 25),
    "Flame Burst":  Move("Flame Burst", "Fire", 70, 90, 10),
    "Water Jet":    Move("Water Jet", "Water", 40, 100, 25),
    "Aqua Blast":   Move("Aqua Blast", "Water", 70, 90, 10),
    "Vine Whip":    Move("Vine Whip", "Grass", 40, 100, 25),
    "Leaf Storm":   Move("Leaf Storm", "Grass", 70, 90, 10),
    "Spark":        Move("Spark", "Electric", 40, 100, 25),
    "Thunder Shock":Move("Thunder Shock", "Electric", 70, 90, 10),
    "Tackle":       Move("Tackle", "Normal", 35, 100, 30),
    "Quick Strike": Move("Quick Strike", "Normal", 25, 100, 30),
    "Body Slam":    Move("Body Slam", "Normal", 60, 90, 15),
    "Bite":         Move("Bite", "Normal", 45, 95, 20),
}


class Species:
    """Blueprint for a creature type."""
    def __init__(self, name, ctype, base_hp, base_atk, base_def, base_spd, move_names, catch_rate):
        self.name = name
        self.type = ctype
        self.base_hp = base_hp
        self.base_atk = base_atk
        self.base_def = base_def
        self.base_spd = base_spd
        self.move_names = move_names
        self.catch_rate = catch_rate  # 0-1, higher = easier to catch


SPECIES = {
    "Flambit":   Species("Flambit", "Fire", 38, 12, 8, 12, ["Ember", "Tackle", "Flame Burst", "Quick Strike"], 0.35),
    "Aquafin":   Species("Aquafin", "Water", 42, 10, 10, 9, ["Water Jet", "Tackle", "Aqua Blast", "Bite"], 0.35),
    "Leafkit":   Species("Leafkit", "Grass", 40, 11, 11, 8, ["Vine Whip", "Tackle", "Leaf Storm", "Quick Strike"], 0.35),
    "Sparklet":  Species("Sparklet", "Electric", 35, 13, 7, 15, ["Spark", "Quick Strike", "Thunder Shock", "Tackle"], 0.30),
    "Rockhide":  Species("Rockhide", "Normal", 45, 9, 14, 6, ["Tackle", "Body Slam", "Bite", "Quick Strike"], 0.45),
    "Puffowl":   Species("Puffowl", "Normal", 32, 10, 8, 16, ["Quick Strike", "Tackle", "Bite", "Body Slam"], 0.50),
    "Emberdrake":Species("Emberdrake", "Fire", 50, 15, 10, 10, ["Flame Burst", "Ember", "Body Slam", "Quick Strike"], 0.15),
    "Tidalor":   Species("Tidalor", "Water", 55, 14, 12, 8, ["Aqua Blast", "Water Jet", "Body Slam", "Bite"], 0.15),
    "Thornback": Species("Thornback", "Grass", 52, 13, 13, 7, ["Leaf Storm", "Vine Whip", "Body Slam", "Tackle"], 0.15),
    "Voltusk":   Species("Voltusk", "Electric", 44, 16, 9, 17, ["Thunder Shock", "Spark", "Bite", "Quick Strike"], 0.12),
}


class Creature:
    def __init__(self, species_name, level=5):
        sp = SPECIES[species_name]
        self.species_name = species_name
        self.type = sp.type
        self.level = level
        self.catch_rate = sp.catch_rate

        # simple stat scaling with level
        self.max_hp = sp.base_hp + level * 3
        self.hp = self.max_hp
        self.attack = sp.base_atk + level
        self.defense = sp.base_def + level
        self.speed = sp.base_spd + level

        self.exp = 0
        self.exp_to_next = level * 20

        self.moves = [MOVES[m] for m in sp.move_names]
        for m in self.moves:
            m.pp = m.max_pp  # fresh pp

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
        leveled_up = False
        while self.exp >= self.exp_to_next:
            self.exp -= self.exp_to_next
            self.level_up()
            leveled_up = True
        return leveled_up

    def level_up(self):
        self.level += 1
        hp_gain = 3 + random.randint(0, 2)
        self.max_hp += hp_gain
        self.hp += hp_gain
        self.attack += 1 + random.randint(0, 1)
        self.defense += 1 + random.randint(0, 1)
        self.speed += 1 + random.randint(0, 1)
        self.exp_to_next = self.level * 20

    def status_line(self):
        bar = hp_bar(self.hp, self.max_hp)
        return f"{self.species_name} Lv.{self.level}  {bar}  {self.hp}/{self.max_hp} HP"


def hp_bar(hp, max_hp, width=20):
    filled = int(width * hp / max_hp) if max_hp else 0
    filled = max(0, min(width, filled))
    return "[" + "#" * filled + "-" * (width - filled) + "]"


def type_multiplier(attacker_type, defender_type):
    return TYPE_CHART.get(attacker_type, {}).get(defender_type, 1.0)


def make_wild_creature(min_level, max_level, pool=None):
    pool = pool or list(SPECIES.keys())
    species_name = random.choice(pool)
    level = random.randint(min_level, max_level)
    return Creature(species_name, level)


# ----------------------------- PLAYER ----------------------------- #

class Player:
    def __init__(self, name, starter_name):
        self.name = name
        self.team = [Creature(starter_name, level=5)]
        self.pokeballs = 5
        self.potions = 3
        self.money = 50
        self.badges = 0

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


# ----------------------------- BATTLE ----------------------------- #

def choose_move(creature):
    print(f"\nWhat will {creature.species_name} do?")
    usable = [m for m in creature.moves if m.pp > 0]
    if not usable:
        print(f"{creature.species_name} has no PP left and must Struggle!")
        return Move("Struggle", "Normal", 20, 100, 1)
    for i, m in enumerate(creature.moves, 1):
        marker = "" if m.pp > 0 else "  (no PP)"
        print(f"  {i}. {m}{marker}")
    while True:
        choice = input("Choose a move number: ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(creature.moves):
            move = creature.moves[int(choice) - 1]
            if move.pp <= 0:
                print("No PP left for that move!")
                continue
            return move
        print("Invalid choice, try again.")


def perform_attack(attacker, move, defender):
    if move.pp > 0:
        move.pp -= 1
    if random.randint(1, 100) > move.accuracy:
        print(f"{attacker.species_name}'s {move.name} missed!")
        return

    mult = type_multiplier(move.type, defender.type)
    base = (2 * attacker.level / 5 + 2) * move.power * (attacker.attack / max(1, defender.defense)) / 50 + 2
    dmg = int(base * mult * random.uniform(0.85, 1.0))
    dmg = max(1, dmg)
    defender.take_damage(dmg)

    print(f"{attacker.species_name} used {move.name}!")
    if mult > 1:
        print("It's super effective!")
    elif mult < 1:
        print("It's not very effective...")
    print(f"{defender.species_name} took {dmg} damage. ({defender.hp}/{defender.max_hp} HP left)")


def switch_creature(player, exclude_fainted=True):
    print("\nYour team:")
    for i, c in enumerate(player.team, 1):
        tag = " (fainted)" if c.is_fainted else ""
        print(f"  {i}. {c.status_line()}{tag}")
    while True:
        choice = input("Switch to which creature? (number, or 'c' to cancel): ").strip().lower()
        if choice == "c":
            return None
        if choice.isdigit() and 1 <= int(choice) <= len(player.team):
            picked = player.team[int(choice) - 1]
            if exclude_fainted and picked.is_fainted:
                print(f"{picked.species_name} has fainted and can't battle!")
                continue
            return picked
        print("Invalid choice.")


def award_exp_and_levelup(creature, exp_amount):
    leveled = creature.gain_exp(exp_amount)
    print(f"{creature.species_name} gained {exp_amount} EXP!")
    if leveled:
        print(f"{creature.species_name} grew to level {creature.level}!")


def try_catch(player, wild):
    if player.pokeballs <= 0:
        print("You're out of monster balls!")
        return False
    player.pokeballs -= 1

    hp_factor = 1 - (wild.hp / wild.max_hp) * 0.65  # lower hp -> higher chance
    chance = min(0.95, wild.catch_rate + hp_factor)
    print(f"\nYou throw a monster ball at the wild {wild.species_name}...")
    time.sleep(0.4)
    if random.random() < chance:
        print(f"Gotcha! {wild.species_name} was caught!")
        if len(player.team) < 6:
            player.team.append(wild)
        else:
            print("Your team is full! It was sent to storage (not tracked in this demo).")
        return True
    else:
        print(f"Oh no! The {wild.species_name} broke free!")
        return False


def battle(player, wild=None, trainer=None):
    """
    Run a battle. Exactly one of wild/trainer should be provided.
    Returns True if the player wins/succeeds, False if they flee or lose.
    """
    is_trainer_battle = trainer is not None
    enemy_name = trainer["name"] if is_trainer_battle else "Wild"
    enemy_team = trainer["team"] if is_trainer_battle else [wild]
    enemy_idx = 0
    enemy = enemy_team[enemy_idx]

    print("\n" + "=" * 50)
    if is_trainer_battle:
        print(f"Trainer {enemy_name} wants to battle!")
    else:
        print(f"A wild {enemy.species_name} (Lv.{enemy.level}) appeared!")
    print("=" * 50)

    if not player.has_usable_creature():
        print("You have no creatures able to battle!")
        return False

    mine = player.active

    while True:
        if mine.is_fainted:
            new_mine = switch_creature(player)
            if new_mine is None:
                if not player.has_usable_creature():
                    print("All your creatures have fainted. You blacked out!")
                    return False
                continue
            mine = new_mine

        if enemy.is_fainted:
            enemy_idx += 1
            if enemy_idx >= len(enemy_team):
                break
            enemy = enemy_team[enemy_idx]
            print(f"\n{enemy_name} sends out {enemy.species_name} (Lv.{enemy.level})!")

        print(f"\n-- {mine.status_line()}")
        print(f"-- {enemy.species_name} Lv.{enemy.level}  {hp_bar(enemy.hp, enemy.max_hp)}  {enemy.hp}/{enemy.max_hp} HP")

        print("\n1. Fight  2. Switch  3. Item  " + ("" if is_trainer_battle else "4. Catch  ") + "5. Run")
        action = input("Choose an action: ").strip()

        if action == "1":
            move = choose_move(mine)
        elif action == "2":
            new_mine = switch_creature(player)
            if new_mine is not None and new_mine is not mine:
                mine = new_mine
                print(f"Go, {mine.species_name}!")
            continue
        elif action == "3":
            if player.potions > 0:
                player.potions -= 1
                heal = 20
                mine.hp = min(mine.max_hp, mine.hp + heal)
                print(f"You used a potion! {mine.species_name} recovered {heal} HP.")
            else:
                print("You have no potions left!")
            move = None
        elif action == "4" and not is_trainer_battle:
            caught = try_catch(player, enemy)
            if caught:
                return True
            move = None
        elif action == "5":
            if is_trainer_battle:
                print("You can't run from a trainer battle!")
                continue
            print("Got away safely!")
            return False
        else:
            print("Invalid action.")
            continue

        # enemy turn (simple AI: random move)
        enemy_move = random.choice([m for m in enemy.moves if m.pp > 0] or enemy.moves)

        # determine order by speed if player attacked
        if move is not None:
            if mine.speed >= enemy.speed:
                perform_attack(mine, move, enemy)
                if not enemy.is_fainted:
                    perform_attack(enemy, enemy_move, mine)
            else:
                perform_attack(enemy, enemy_move, mine)
                if not mine.is_fainted:
                    perform_attack(mine, move, enemy)
        else:
            # used item or failed catch: enemy still attacks
            perform_attack(enemy, enemy_move, mine)

        if mine.is_fainted:
            print(f"{mine.species_name} fainted!")
        if enemy.is_fainted:
            print(f"{enemy.species_name} fainted!")
            exp_gain = enemy.level * 8
            award_exp_and_levelup(mine, exp_gain)

    print(f"\nYou defeated {enemy_name}!" if is_trainer_battle else "\nThe wild creature was defeated!")
    if is_trainer_battle:
        reward = trainer.get("reward", 20)
        player.money += reward
        player.badges += 1 if trainer.get("gives_badge") else 0
        print(f"You received ${reward}.")
        if trainer.get("gives_badge"):
            print(f"You earned a badge! ({player.badges} total)")
    return True


# ----------------------------- TRAINERS ----------------------------- #

def build_trainers():
    return [
        {
            "name": "Youngster Alex",
            "team": [Creature("Puffowl", 6), Creature("Rockhide", 7)],
            "reward": 30,
            "gives_badge": False,
        },
        {
            "name": "Camper Riya",
            "team": [Creature("Leafkit", 9), Creature("Sparklet", 9)],
            "reward": 50,
            "gives_badge": False,
        },
        {
            "name": "Ace Trainer Dev",
            "team": [Creature("Emberdrake", 12), Creature("Tidalor", 12), Creature("Thornback", 12)],
            "reward": 100,
            "gives_badge": True,
        },
        {
            "name": "Champion Meera",
            "team": [
                Creature("Voltusk", 16),
                Creature("Emberdrake", 16),
                Creature("Tidalor", 16),
                Creature("Thornback", 16),
            ],
            "reward": 300,
            "gives_badge": True,
        },
    ]


# ----------------------------- GAME LOOP ----------------------------- #

def print_team(player):
    print("\nYour team:")
    for i, c in enumerate(player.team, 1):
        print(f"  {i}. {c.status_line()}  (Type: {c.type}, EXP: {c.exp}/{c.exp_to_next})")
    print(f"Monster Balls: {player.pokeballs}  Potions: {player.potions}  Money: ${player.money}  Badges: {player.badges}")


def visit_shop(player):
    print("\n--- Shop ---")
    print("1. Monster Ball - $10")
    print("2. Potion - $15")
    print("3. Leave")
    while True:
        choice = input("Buy what? ").strip()
        if choice == "1":
            if player.money >= 10:
                player.money -= 10
                player.pokeballs += 1
                print("Bought a Monster Ball!")
            else:
                print("Not enough money!")
        elif choice == "2":
            if player.money >= 15:
                player.money -= 15
                player.potions += 1
                print("Bought a Potion!")
            else:
                print("Not enough money!")
        elif choice == "3":
            break
        else:
            print("Invalid choice.")


def choose_starter():
    print("\nChoose your starter creature:")
    starters = ["Flambit", "Aquafin", "Leafkit", "Sparklet"]
    for i, s in enumerate(starters, 1):
        sp = SPECIES[s]
        print(f"  {i}. {s} ({sp.type})")
    while True:
        choice = input("Enter number: ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(starters):
            return starters[int(choice) - 1]
        print("Invalid choice.")


def main():
    print("=" * 50)
    print("        WELCOME TO MONSTER TAMER")
    print("=" * 50)
    name = input("What is your name, trainer? ").strip() or "Trainer"
    starter = choose_starter()
    player = Player(name, starter)
    trainers = build_trainers()
    trainer_idx = 0

    print(f"\nGood luck, {player.name}! Your journey begins with {player.team[0].species_name}.")

    while True:
        print("\n" + "-" * 50)
        print("What would you like to do?")
        print("1. Explore (find a wild creature)")
        print("2. Battle next trainer")
        print("3. View team")
        print("4. Heal at Pokecenter (free)")
        print("5. Visit shop")
        print("6. Quit")
        choice = input("> ").strip()

        if choice == "1":
            if not player.has_usable_creature():
                print("All your creatures have fainted! Heal up first.")
                continue
            level_range = (3 + player.badges * 2, 8 + player.badges * 3)
            wild = make_wild_creature(*level_range)
            battle(player, wild=wild)

        elif choice == "2":
            if trainer_idx >= len(trainers):
                print("You've defeated all available trainers! You are the champion!")
                print("Thanks for playing Monster Tamer!")
                sys.exit(0)
            if not player.has_usable_creature():
                print("All your creatures have fainted! Heal up first.")
                continue
            t = trainers[trainer_idx]
            won = battle(player, trainer=t)
            if won:
                trainer_idx += 1

        elif choice == "3":
            print_team(player)

        elif choice == "4":
            player.heal_team()
            print("Your team has been fully healed!")

        elif choice == "5":
            visit_shop(player)

        elif choice == "6":
            print("Thanks for playing! See you next time.")
            sys.exit(0)

        else:
            print("Invalid choice, try again.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nGame closed. See you next time!")