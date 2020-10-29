#!/usr/bin/python3
# -*- coding: utf-8 -*-

from __future__ import division
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


if args.games:  # Check for number of games on the command line
    run_count = args.games
else:
    if 'games' in config['General']:    # Check for number of games in config file
        run_count = config['General']['games']
    else:    # Prompt the user for the number of games
        run_count = input("How many games should I play?\n")

# Let's find out if we need to write to the DB or not
if not args.nodb:   # If the commandline option is set, don't bother setting up a DB
    if config['Database'].getboolean('database'):
        # Set up a DB connection
        db_conn = pymysql.connect(config['Database']['host'], config['Database']['user'], config['Database']['password'], config['Database']['databasename'])
        use_db = True


run_id = str(uuid.uuid4())

def play(game_type, run_count):
    # Set up the blank stats
    win_count = 0
    loss_count = 0
    loss_stats = []
    two_matches = 0
    four_matches = 0
    cards_discarded = 0
    first_match = 0
    first_match_type = ''

    if (int(run_count) >= 20): printProgressBar(0, int(run_count), prefix = 'Playing:', suffix = 'Complete', length = 50)

    for run_num in range(int(run_count)):
        game_fingerprint = ''
        first_match = 0
        first_match_type = ''
        gm_two_matches = 0
        gm_four_matches = 0

        # Fire up a new deck and shuffle
        deck = pydealer.Deck()
        deck.shuffle()

        # Set up a stack to deal into
        hand = pydealer.Stack()

        # Variable to tell us that it needs to draw a card
        # Needed because a suit match later doesn't need to draw a card before checking
        draw_needed = True

        while len(deck) > 0:
            if debug: print("Hand")
            if debug: print(hand)
            if debug: print("------------------------")
            if draw_needed:
                draw_card = deck.deal(1)
                hand.add(draw_card)
                game_fingerprint += '.'
                if debug: print("Draw - %s" % draw_card)
            else:
                draw_needed = True

            # Make sure we have at least 4 cards in the hand
            if len(hand) < 4:
                continue
            
            # Find the last card and the "check" card three down from it
            last_card = len(hand)-1         # The index of the last card
            current_card = hand[last_card]  # The actual last card
            check_card = hand[last_card-3]  # The "check" card

            if debug: print("Checking - %s against %s" % (current_card, check_card))

            # Check for a 4-card-draw match (rank in normal, suit in reverse
            if game_type.lower() == 'normal':
                if current_card.value == check_card.value:
                    match4 = True
                    match_type = 'R'
                else:
                    match4 = False
            if game_type.lower() == 'reverse':
                if current_card.suit == check_card.suit:
                    match4 = True
                    match_type = 'S'
                else:
                    match4 = False

            # See if the value matches and remove all four cards from the hand
            if match4:
                if debug: print("Four Card match - %s matches %s" % (current_card, check_card))
                if first_match == 0:
                    first_match = len(hand)
                    first_match_type = match_type
                four_matches += 1
                gm_four_matches += 1
                game_fingerprint += match_type
                if debug: print("Dicard - %s" % hand[last_card])
                del hand[last_card]
                if debug: print("Dicard - %s" % hand[last_card-1])
                del hand[last_card-1]
                if debug: print("Dicard - %s" % hand[last_card-2])
                del hand[last_card-2]
                if debug: print("Dicard - %s" % hand[last_card-3])
                del hand[last_card-3]
                cards_discarded += 4
                draw_needed = True
                match4 = False
                match_type = ''

            if game_type.lower()== 'normal':
                if current_card.suit == check_card.suit:
                    match2 = True
                    match_type = 'S'
                else:
                    match2 = False
            if game_type.lower()== 'reverse':
                if current_card.value == check_card.value:
                    match2 = True
                    match_type = 'R'
                else:
                    match2 = False

            # See if the suit matched and remove the two cards between the last card and the check card
            if match2:
                if debug: print("Two Card match - %s matches %s" % (current_card, check_card))
                if first_match == 0:
                    first_match = len(hand)
                    first_match_type = match_type
                two_matches += 1
                gm_two_matches += 1
                game_fingerprint += match_type
                if debug: print("Dicard - %s" % hand[last_card-1])
                del hand[last_card-1]
                if debug: print("Dicard - %s" % hand[last_card-2])
                del hand[last_card-2]
                cards_discarded += 2
                draw_needed = False
        if len(hand) == 0:      # Winner winner
            win = 1
            win_count+=1
        else:
            win = 0
            loss_count+=1   # Lost game, collect some stats
            loss_stats.append(len(hand))

        # Write the values to the DB if needed
        if use_db:
            with db_conn.cursor() as cursor:
                cards_left = len(hand)
                sql = "INSERT INTO games (game_type, win, cards_left, four_matches, two_matches, first_match_type, first_match_card, fingerprint, run_id) "
                sql += "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
                cursor.execute(sql, (game_type.title(), win, cards_left, gm_four_matches, gm_two_matches, first_match_type, first_match, game_fingerprint, run_id))

        # Update the progress bar if needed
        if (int(run_count) >= 20): printProgressBar(run_num + 1, int(run_count), prefix = game_type.title(), suffix = 'Complete', length = 50)


    # Return the summary of games played
    retstring = "\n=== %s Game Stats ===" % (game_type.title())
    retstring += "\nWins: %s" % win_count
    retstring += "\nLosses %s" % loss_count
    retstring += "\nWin Percentage: %s" % "{:.2%}".format(int(win_count)/int(run_count))
    retstring += "\nMin cards left: %s" % min(loss_stats)
    retstring += "\nMax cards left: %s" % max(loss_stats)
    retstring += "\nAvg cards left: %s" % round((sum(loss_stats)/len(loss_stats)))
    retstring += "\nTotal 4-card matches: %s" % four_matches
    retstring += "\nTotal 2-card matches: %s" % two_matches
    retstring += "\nTotal number of cards discarded %s" % cards_discarded
    if int(run_count) == 1:
        retstring += "\nGame Fingerprint:\n\t%s" % game_fingerprint

    return retstring


    
def printProgressBar (iteration, total, prefix = '', suffix = '', decimals = 1, length = 100, fill = '█'):
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print('\r%s |%s| %s%% %s' % (prefix, bar, percent, suffix), end='\r')

    # Print a newline on complete
    if iteration == total:
        print()

# Main play loop
results = "\nRun ID: %s" % run_id
if args.normal or (not args.normal and not args.reverse):
    results += play('Normal', run_count)
if args.reverse or (not args.normal and not args.reverse):
    results += play('Reverse', run_count)

print(results)

# Commit and close the DB connection
if use_db:
    db_conn.commit()
    db_conn.close()
