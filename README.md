# onehand.py
This Python program runs a simulation of repeated games of One-Hand Solitaire, calculating statistics and optionally writing the game records to a MySQL/MariaDB database for additional analysis.

## Background
Growing up, I played a game of solitaire that I always knew as One-Hand Solitaire. The rules were simple, and the game could be played in the hand without needing to lay cards out on a flat surface. The problem was that the game was incredibly hard to win.

I started wondering what the actual win probability was, and I had just been doing some experiments with PyDealer, a playing card simulator for Python. I decided to write a small program to simulate the games and track the statistics. I wanted to know if there was a pattern to the wins and losses and ways to predict early in a game whether there was a good change of winning. Spoiler alert...there isn't.

As I came to the conclusion that the odds of winning were lower than I expected, I started wondering how the rules might be adjusted to make the odds a little better. You can see the rules of the game below, but, in essence two random cards with matching suits are good but two matching ranks (values) are better. I decided to write what I call a "Reverse Two-Hand Solitaire" simulator to see how the odds were changed if suit matches, which are obviously more likely, were better than rank matches. As expected, it did and now is the way that I teach the game to others. It is still a game of chance, and still entertaining, but now I don't have to play hundreds of hands before I might see a win.

The project here is the culmination of both of the programs I wrote. I decided to try and optimize the code by combining the two simulations into a single program, with a built-in database function so that I could database all of the games and do analysis on them.

At this point, I have played over 3,000,000 games of each. If you actually have interest in the historical data, I would be happy to share the database tables.

## One-Hand Solitaire Rules
*These are the rules for the "normal" way of playing. For Reverse One-Hand Solitaire, just flip how many cards you remove for a suit and value match*

Taking a standard, shuffled 52-card deck of playing cards (without Jokers), hold the deck face down in your hand. Draw from the back of the deck four cards and place them on top fanned out so that the suit and number can be seen.

If the first and fourth card are the same suit, discard the two middle cards, placing them on your lap if seated or in a pocket or elsewhere if standing. If there are previously drawn cards in your hand, rearrange the hand so that four cards are visible. If there are not enough cards to do this, draw from the back so that four cards are visible.

If the first and fourth card are the same number (or face card) discard all four cards. Again, if there are previously drawn cards in your hand, rearrange the hand so that four cards are visible. If there are not enough cards to do this, draw from the back so that four cards are visible.

Repeat the above process of discarding until the first and fourth card are neither the same suit nor number, upon which you draw one card from the back of the deck and place it after the fourth card, rearranging the drawn cards so that only four are visible.

Continue in this fashion until the end of the deck is reached. If all cards are discarded, you win the game.

## Usage
*Using the --debug option results in a lot of output: every draw, the complete hand, and every match*

```
usage: onehand.py [-h] [-n GAMES] [-c CONFIG] [--normal] [--reverse] [--nodb]
                  [--debug]

optional arguments:
  -h, --help            show this help message and exit
  -n GAMES, --games GAMES
                        Number of games to play
  -c CONFIG, --config CONFIG
                        Location of config file to use
  --normal              Play games using the normal rules
  --reverse             Play games using the reverse rules
  --nodb                Do not write games to the database
  --debug               Print debug info to the screen
```
