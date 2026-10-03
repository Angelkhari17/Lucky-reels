"""Slot Machine - a terminal casino game written in Python.

Features
    * Deposit money, choose 1-3 lines, and set a bet per line
    * Weighted symbols: rarer symbols pay more
    * Winnings are checked line by line
    * Stats (spins played, best balance) are saved between runs in a JSON file
"""

import json
import random
import time
from pathlib import Path

# ----------------------------- Game settings ----------------------------- #
MAX_LINES = 3
MAX_BET = 100
MIN_BET = 1

ROWS = 3
COLS = 3

# How many of each symbol exist on a reel. Fewer copies = rarer.
SYMBOL_COUNT = {"A": 2, "B": 4, "C": 6, "D": 8}

# Multiplier paid when a whole line is the same symbol (bet x multiplier).
SYMBOL_VALUE = {"A": 5, "B": 4, "C": 3, "D": 2}

SAVE_FILE = Path(__file__).with_name("slot_stats.json")


# ------------------------------ Input helpers ----------------------------- #
def get_int(prompt, minimum, maximum=None):
    """Keep asking until the user types a whole number in the allowed range."""
    while True:
        text = input(prompt).strip()
        if not text.isdigit():
            print("Please enter a number.")
            continue
        value = int(text)
        if value < minimum or (maximum is not None and value > maximum):
            if maximum is None:
                print(f"Amount must be at least ${minimum}.")
            else:
                print(f"Value must be between {minimum} and {maximum}.")
            continue
        return value


def deposit():
    """Ask how much money the player wants to start with."""
    return get_int("What would you like to deposit? $", 1)


def get_number_of_lines():
    """Ask how many lines (rows) to bet on."""
    return get_int(f"Enter the number of lines to bet on (1-{MAX_LINES}): ", 1, MAX_LINES)


def get_bet():
    """Ask how much to bet on each line."""
    return get_int(
        f"What would you like to bet on each line? (${MIN_BET}-${MAX_BET}): $",
        MIN_BET,
        MAX_BET,
    )


# ------------------------------- Game logic ------------------------------- #
def get_slot_machine_spin(rows, cols, symbols):
    """Return a list of columns; each column is a list of `rows` symbols."""
    all_symbols = []
    for symbol, count in symbols.items():
        all_symbols.extend([symbol] * count)

    columns = []
    for _ in range(cols):
        available = all_symbols[:]  # copy, so each column starts with a full pool
        column = []
        for _ in range(rows):
            value = random.choice(available)
            available.remove(value)  # a symbol can't repeat beyond its count
            column.append(value)
        columns.append(column)
    return columns


def print_slot_machine(columns, animate=True):
    """Print the reels as rows, e.g.  A | B | C"""
    if animate:
        for dots in ("Spinning.", "Spinning..", "Spinning..."):
            print(dots, end="\r")
            time.sleep(0.4)
        print(" " * 15, end="\r")

    print("-" * 11)
    for row in range(len(columns[0])):
        print(" | ".join(column[row] for column in columns))
    print("-" * 11)


def check_winnings(columns, lines, bet, values):
    """Return (total_winnings, list_of_winning_line_numbers).

    Line 1 is the top row, line 2 the middle row, line 3 the bottom row.
    A line wins when every column shows the same symbol on that row.
    """
    winnings = 0
    winning_lines = []
    for line in range(lines):
        symbol = columns[0][line]
        if all(column[line] == symbol for column in columns):
            winnings += values[symbol] * bet
            winning_lines.append(line + 1)
    return winnings, winning_lines


def play_round(balance):
    """Play one spin and return the net change in balance (can be negative)."""
    while True:
        lines = get_number_of_lines()
        bet = get_bet()
        total_bet = bet * lines
        if total_bet <= balance:
            break
        print(f"You do not have enough to bet that amount. Your balance is ${balance}.")

    print(f"You are betting ${bet} on {lines} line(s). Total bet: ${total_bet}")

    slots = get_slot_machine_spin(ROWS, COLS, SYMBOL_COUNT)
    print_slot_machine(slots)

    winnings, winning_lines = check_winnings(slots, lines, bet, SYMBOL_VALUE)
    if winning_lines:
        print(f"You won ${winnings}!")
        print("You won on line(s):", *winning_lines)
    else:
        print("No win this time.")
    return winnings - total_bet


# ---------------------------- Saving / loading ---------------------------- #
def load_stats():
    """Read saved stats; fall back to fresh stats if the file is missing/broken."""
    try:
        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {
            "spins": int(data.get("spins", 0)),
            "best_balance": int(data.get("best_balance", 0)),
        }
    except (FileNotFoundError, ValueError, json.JSONDecodeError):
        return {"spins": 0, "best_balance": 0}


def save_stats(stats):
    try:
        with open(SAVE_FILE, "w", encoding="utf-8") as f:
            json.dump(stats, f)
    except OSError:
        print("(Could not save stats.)")


# --------------------------------- Main ----------------------------------- #
def main():
    stats = load_stats()
    print("=== SLOT MACHINE ===")
    print(f"Lifetime spins: {stats['spins']} | Best balance: ${stats['best_balance']}")

    balance = deposit()
    starting_balance = balance

    while True:
        print(f"\nCurrent balance: ${balance}")
        choice = input("Press Enter to play (q to quit): ").strip().lower()
        if choice == "q":
            break

        balance += play_round(balance)
        stats["spins"] += 1
        stats["best_balance"] = max(stats["best_balance"], balance)

        if balance < MIN_BET:
            print("\nYou're out of money. Game over!")
            break

    net = balance - starting_balance
    result = "up" if net >= 0 else "down"
    print(f"\nYou left with ${balance} ({result} ${abs(net)}).")
    save_stats(stats)


if __name__ == "__main__":
    main()
