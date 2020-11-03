#!/usr/bin/python3
# -*- coding: utf-8 -*-

from __future__ import division
import pymysql      # Only supporting MySQL/MariaDB right now, but should probably expand that
#import argparse
import configparser
import matplotlib.pyplot as plt
import numpy as np

# Get the config file
config = configparser.ConfigParser()
config.read('config')

db_conn = pymysql.connect(config['Database']['host'], config['Database']['user'], config['Database']['password'], config['Database']['databasename'])

try:
    f = open("stats/stats.md", "w")
    f.write("| Game Type | Games Played | Wins | Win Percentage |\n")
    f.write("| --------- |:------------:|:----:|:--------------:|\n")
    with db_conn.cursor() as cur:
        cur.execute("SELECT win, count(win) FROM games WHERE game_type = 'Normal' GROUP BY win WITH ROLLUP")
        rows = cur.fetchall()

        wins = rows[1][1]
        games = rows[2][1]

        f.write(f"| Normal  | {games:,} | {wins:,} | %s |\n" % "{:.2%}".format(int(wins)/int(games)))

    with db_conn.cursor() as cur:
        cur.execute("SELECT win, count(win) FROM games WHERE game_type = 'Reverse' GROUP BY win WITH ROLLUP")
        rows = cur.fetchall()

        wins = rows[1][1]
        games = rows[2][1]

        f.write(f"| Reverse  | {games:,} | {wins:,} | %s |\n" % "{:.2%}".format(int(wins)/int(games)))
finally:
    f.close()

# Now let's make some graphs
try:
    with db_conn.cursor() as cur:
        cur.execute("SELECT first_match_card, count(win) FROM games WHERE win = 1 AND game_type = 'Normal' GROUP BY first_match_card")
        rows = cur.fetchall()

        # Hraph data
        objects = []
        values = []

        for row in rows:
            objects.append(row[0])
            values.append(row[1])

        y_pos = np.arange(len(objects))

        plt.bar(y_pos, values, align='center')
        plt.xticks(y_pos, objects)
        plt.ylabel('Games Won')
        plt.xlabel('First Match Card')
        plt.title('Wins by First Match Card - Normal')
        plt.savefig('stats/normal.png')
    
    with db_conn.cursor() as cur:
        cur.execute("SELECT first_match_card, count(win) FROM games WHERE win = 1 AND game_type = 'Reverse' GROUP BY first_match_card")
        rows = cur.fetchall()

        # Hraph data
        objects = []
        values = []

        for row in rows:
            objects.append(row[0])
            values.append(row[1])

        y_pos = np.arange(len(objects))

        plt.bar(y_pos, values, align='center')
        plt.xticks(y_pos, objects)
        plt.ylabel('Games Won')
        plt.xlabel('First Match Card')
        plt.title('Wins by First Match Card - Reverse')
        plt.savefig('stats/reverse.png')
finally:    
    db_conn.close()



