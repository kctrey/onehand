#!/usr/bin/python3
# -*- coding: utf-8 -*-

from __future__ import division
import pydealer
import uuid
import pymysql
import argparse

# Collect the arguments and set up some defaults
ap = argparse.ArgumentParser()

ap.add_argument("-n", "--games", required=False, help="Number of games to play", type=int)
ap.add_argument('--nodb', help='Do not write games to the database', required=False, action='store_true')
ap.add_argument('--debug', help='Print debug info to the screen', required=False, action='store_true')

args = ap.parse_args()

if args.debug:
    debug = True
else:
    debug = False

if not args.games:
    run_count = input("How many games should I play?\n")
else:
    run_count = args.games

# Let's find out if we need to write to the DB or not
if not args.nodb:
    # Set up a DB connection
    db_host = 'localhost'
    db_user = 'trey'
    db_pass = 'hope96'
    db_database = 'SOLITAIRE'

    db_conn = pymysql.connect(db_host, db_user, db_pass, db_database)


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
        if not args.nodb:
            with db_conn.cursor() as cursor:
                cards_left = len(hand)
                sql = "INSERT INTO games (game_type, win, cards_left, four_matches, two_matches, first_match_type, first_match_card, fingerprint, run_id) "
                sql += "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
                cursor.execute(sql, (game_type.title(), win, cards_left, gm_four_matches, gm_two_matches, first_match_type, first_match, game_fingerprint, run_id))

        # Update the progress bar if needed
        if (int(run_count) >= 20): printProgressBar(run_num + 1, int(run_count), prefix = 'Playing:', suffix = 'Complete', length = 50)


    # Print the summary of games played
    print("\n=== %s Game Stats ===" % (game_type.title()))
    print("Run ID:", run_id)
    print("Wins:",win_count)
    print("Losses:",loss_count)
    print("Win Percentage: {:.2%}".format(int(win_count)/int(run_count)))
    print("Min cards left:",min(loss_stats))
    print("Max cards left:",max(loss_stats))
    print("Avg cards left:",sum(loss_stats)/len(loss_stats))
    print("Total 4-card matches:",four_matches)
    print("Total 2-card matches:",two_matches)
    print("Total number of cards discarded:",cards_discarded)

    if int(run_count) == 1:
        print("Game Fingerprint: ")
        print(game_fingerprint)


    
def printProgressBar (iteration, total, prefix = '', suffix = '', decimals = 1, length = 100, fill = '█'):
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print('\r%s |%s| %s%% %s' % (prefix, bar, percent, suffix), end='\r')

    # Print a newline on complete
    if iteration == total:
        print()

# Main play look
play('Normal', run_count)
play('Reverse', run_count)

# Commit and close the DB connection
if not args.nodb:
    db_conn.commit()
    db_conn.close()
