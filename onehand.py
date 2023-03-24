#!/usr/bin/python3
# -*- coding: utf-8 -*-

from __future__ import division
from typing import Optional
import copy
import pydealer     # Used to magage the deck of cards so we don't have to write our own module
import uuid         # Used to generate a unique "run ID" to store in the database
import pymysql      # Only supporting MySQL/MariaDB right now, but should probably expand that
import argparse
import configparser

# Collect the arguments and set up some defaults
ap = argparse.ArgumentParser()

ap.add_argument("-n", "--games", required=False, help="Number of games to play", type=int)
ap.add_argument('-c', '--config', required=False, help='Location of config file to use')
ap.add_argument('--normal', required=False, help='Play games using the normal rules', action='store_true')
ap.add_argument('--reverse', required=False, help='Play games using the reverse rules', action='store_true')
ap.add_argument('--nodb', help='Do not write games to the database', required=False, action='store_true')
ap.add_argument('--debug', help='Print debug info to the screen', required=False, action='store_true')
ap.add_argument('--timing', help='Print program execution timing', required=False, action='store_true')
ap.add_argument('--samedeck', help='Play a single set of Normal/Reverse games, using the same deck for both.',
                required=False, action='store_true')

args = ap.parse_args()

use_db = False  # Assume we aren't writing to a DB unless we find out differently

if args.timing:
    import timing   # I used someone else's code for this module, but it seems to work well enough for my needs

# Get the config file
config = configparser.ConfigParser()
if args.config:
    config.read(args.config)
else:
    config.read('config')

if args.debug:  # Check for debug on the command line
    debug = True
else:
    if config['General'].getboolean('debug'):   # Check to see if debug is enabled in the config file
        debug = True
    else:
        debug = False

# Let's find out if we need to write to the DB or not
if not args.nodb:   # If the commandline option is set, don't bother setting up a DB
    if config['Database'].getboolean('database'):
        # Set up a DB connection
        db_conn = pymysql.connect(host=config['Database']['host'], user=config['Database']['user'],
                                  password=config['Database']['password'], database=config['Database']['databasename'])
        use_db = True


def print_deck(deck):
    print("Deck:")
    card: pydealer.Card
    for card in deck.cards:
        print(card.abbrev)


def print_hand(hand):
    print(f"Hand: ({len(hand)})")
    hand: pydealer.Stack
    print(hand)
    print("------------------------")


class Run:
    def __init__(self):
        self.count: int = 1
        self.game_type: str = 'both'
        self.same_deck: bool = False
        self.id: str = str(uuid.uuid4())
        self.games = []

    def _print_progress_bar(self, iteration, prefix: str = 'Playing'):
        total = len(self.games)
        prefix += ':'
        suffix = 'Complete'
        decimals = 1
        length = 50
        fill = '█'
        percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
        filled_length = int(length * iteration // total)
        bar = fill * filled_length + '-' * (length - filled_length)
        print(f'\r{prefix} |{bar}| {percent}% {suffix}', end='\r', flush=True)
        # Print a newline at the end
        if iteration == total:
            print()

    @property
    def stats(self):
        stats = {
            'run': {
                'rules': self.game_type.lower(),
                'games': len(self.games),
                'wins': 0,
                'losses': 0
            },
            'normal': {
                'games': 0,
                'wins': 0,
                'losses': 0,
                'win_pct': 0,
                'max_cards_left': 0,
                'min_cards_left': 0,
                'avg_cards_left': 0
            },
            'reverse': {
                'games': 0,
                'wins': 0,
                'losses': 0,
                'win_pct': 0,
                'max_cards_left': 0,
                'min_cards_left': 0,
                'avg_cards_left': 0
            }
        }

        # Set up a list of remaining cards to do some math later
        cards_left = {'normal': [], 'reverse': []}

        for game in self.games:
            if game.win is True:
                stats['run']['wins'] += 1
                stats[game.type]['wins'] += 1
            else:
                stats['run']['losses'] += 1
                stats[game.type]['losses'] += 1
            stats[game.type]['games'] += 1
            cards_left[game.type].append(game.cards_left)

        for game_type in ['normal', 'reverse']:
            stats[game_type]['max_cards_left'] = max(cards_left[game_type])
            stats[game_type]['min_cards_left'] = min(cards_left[game_type])
            if stats[game_type]['losses'] != 0:
                stats[game_type]['avg_cards_left'] = round(sum(cards_left[game_type]) / int(stats[game_type]['games']))
            stats[game_type]['win_pct'] = "{:.2%}".format(int(stats[game_type]['wins']) /
                                                          int(stats[game_type]['games']))

        return stats

    def print_stats(self):
        # Return the summary of games played
        stats = self.stats
        print("=== Run Summary ===")
        print(f"Run ID: {self.id}")
        print(f"Rules: {stats['run']['rules'].title()}")
        print(f"Games played: {stats['run']['games']}")
        print(f"Wins: {stats['run']['wins']}")
        print(f"Losses: {stats['run']['losses']}")

        for game_type in ['normal', 'reverse']:
            if game_type == stats['run']['rules'] or stats['run']['rules'] == 'both':
                print(f"-- {game_type.title()} Games ---")
                print(f"Games: {stats[game_type]['games']}")
                print(f"Wins: {stats[game_type]['wins']}")
                print(f"Losses: {stats[game_type]['losses']}")
                print(f"Win percentage: {stats[game_type]['win_pct']}")
                print(f"Max cards left: {stats[game_type]['max_cards_left']}")
                print(f"Min cards left: {stats[game_type]['min_cards_left']}")
                print(f"Average cards left: {stats[game_type]['avg_cards_left']}")

    def prepare(self):
        for x in range(self.count):
            prep_games = []

            if int(self.count) >= 20:
                self._print_progress_bar(x + 1, prefix="Preparing")

            if self.game_type.lower() == 'both' or self.game_type.lower() == 'normal':
                normal_game = Game(type='normal', run_id=self.id)
                prep_games.append(normal_game)
                self.games.append(normal_game)
            if self.game_type.lower() == 'both' or self.game_type.lower() == 'reverse':
                reverse_game = Game(type='reverse', run_id=self.id)
                prep_games.append(reverse_game)
                self.games.append(reverse_game)

            # If we are playing with the same deck for each game, build and shuffle a deck and associate it
            if self.same_deck is True and self.game_type.lower() == 'both':
                deck1 = pydealer.Deck()
                deck1.shuffle()
                deck2 = copy.deepcopy(deck1)
                prep_games[0].deck = deck1
                prep_games[1].deck = deck2

    def start(self):
        if len(self.games) == 0:
            self.prepare()

        for x, game in enumerate(self.games):
            if int(self.count) >= 20:
                self._print_progress_bar(x+1)
            game.play()

        if use_db is True:
            db_conn.commit()
            db_conn.close()

        return True


class Game:
    def __init__(self, type: str, run_id: str, deck: Optional[pydealer.Deck] = None):
        if deck is None:
            deck = pydealer.Deck()
            deck.shuffle()
        self.type: str = type.lower()
        self.run_id: str = run_id
        self.deck: pydealer.Deck = deck
        self.played: bool = False
        self.win: Optional[bool] = None
        self.cards_left: int = 52
        self.first_match_card: int = 0
        self.first_match_type: str = ''
        self.two_matches: int = 0
        self.four_matches: int = 0
        self.cards_discarded: int = 0
        self.fingerprint: str = ''

    def play(self):
        self.played = True
        # Set up a stack to deal into
        hand = pydealer.Stack()

        # Variable to tell us that it needs to draw a card
        # Needed because a suit match later doesn't need to draw a card before checking
        draw_needed = True

        while len(self.deck) > 0:
            if draw_needed:
                draw_card = self.deck.deal(1)
                hand.add(draw_card)
                self.fingerprint += '.'
                if debug: print("\tDraw - %s" % draw_card)
                if debug: print_hand(hand)
            else:
                draw_needed = True

            # Make sure we have at least 4 cards in the hand
            if len(hand) < 4:
                continue

            # Find the last card and the "check" card three down from it
            last_card = len(hand) - 1  # The index of the last card
            current_card = hand[last_card]  # The actual last card
            check_card = hand[last_card - 3]  # The "check" card

            if debug: print("\tChecking - %s against %s" % (current_card, check_card))

            # Check for a 4-card-draw match (rank in normal, suit in reverse
            if self.type.lower() == 'normal':
                if current_card.value == check_card.value:
                    match4 = True
                    match_type = 'R'
                else:
                    match4 = False
            if self.type.lower() == 'reverse':
                if current_card.suit == check_card.suit:
                    match4 = True
                    match_type = 'S'
                else:
                    match4 = False

            # See if the value matches and remove all four cards from the hand
            if match4:
                if debug: print("\tFour Card match - %s matches %s" % (current_card, check_card))
                if self.first_match_card == 0:
                    self.first_match_card = len(hand)
                    self.first_match_type = match_type
                self.four_matches += 1
                self.fingerprint += match_type
                if debug: print("\tDiscard - %s" % hand[last_card])
                del hand[last_card]
                if debug: print("\tDiscard - %s" % hand[last_card - 1])
                del hand[last_card - 1]
                if debug: print("\tDiscard - %s" % hand[last_card - 2])
                del hand[last_card - 2]
                if debug: print("\tDiscard - %s" % hand[last_card - 3])
                del hand[last_card - 3]
                self.cards_discarded += 4
                draw_needed = True
                match4 = False
                match_type = ''
                if debug: print_hand(hand)

            if self.type.lower() == 'normal':
                if current_card.suit == check_card.suit:
                    match2 = True
                    match_type = 'S'
                else:
                    match2 = False
            if self.type.lower() == 'reverse':
                if current_card.value == check_card.value:
                    match2 = True
                    match_type = 'R'
                else:
                    match2 = False

            # See if the suit matched and remove the two cards between the last card and the check card
            if match2:
                if debug: print("\tTwo Card match - %s matches %s" % (current_card, check_card))
                if self.first_match_card == 0:
                    self.first_match_card = len(hand)
                    self.first_match_type = match_type
                self.two_matches += 1
                self.fingerprint += match_type
                if debug: print("\tDiscard - %s" % hand[last_card - 1])
                del hand[last_card - 1]
                if debug: print("\tDiscard - %s" % hand[last_card - 2])
                del hand[last_card - 2]
                self.cards_discarded += 2
                draw_needed = False
                if debug: print_hand(hand)
        self.cards_left = len(hand)
        if len(hand) == 0:  # Winner winner
            self.win = True
        else:
            self.win = False

        if use_db is True:
            self._write_db()
        return True

    def _write_db(self):
        with db_conn.cursor() as cursor:
            sql = "INSERT INTO games (game_type, win, cards_left, four_matches, two_matches, first_match_type, " \
                  "first_match_card, fingerprint, run_id) "
            sql += "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
            cursor.execute(sql, (self.type.title(), int(self.win), self.cards_left, self.four_matches, self.two_matches,
                                 self.first_match_type, self.first_match_card, self.fingerprint, self.run_id))


if __name__ == '__main__':
    run = Run()

    if args.games:  # Check for number of games on the command line
        run_count = args.games
    else:
        if 'games' in config['General']:  # Check for number of games in config file
            run_count = config['General']['games']
        else:  # Prompt the user for the number of games
            run_count = input("How many games should I play?\n")
    run.count = int(run_count)

    if args.normal or (not args.normal and not args.reverse):
        normal_game = True
    if args.reverse or (not args.normal and not args.reverse):
        reverse_game = True

    if normal_game is True and reverse_game is True:
        run.game_type = 'Both'
    elif normal_game is True and reverse_game is False:
        run.game_type = 'Normal'
    elif normal_game is False and reverse_game is True:
        run.game_type = 'Reverse'

    if config['Game Rules'].getboolean('SameDeck') is True:
        run.same_deck = True

    run.prepare()
    run.start()
    run.print_stats()

