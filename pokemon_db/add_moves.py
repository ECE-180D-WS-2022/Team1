import numpy as np
import sys
import time
import random
import os
import copy
import csv
import pandas as pd
import string
import level_up as lv

df = pd.read_csv('../data/new_pokemon.csv')
movelist = pd.read_csv('moves.csv')
learnset = lv.import_learnset()

#NOTE: POKEMON ID = ARRAY+1 -> ie: #532 CORRESPONDS WITH LEARNSET[531]
#print(learnset[611][1]) #print haxorus starting moves
for pkmn in range(898):
    #retrieve starting moves list
    start_moves = learnset[pkmn][1]
    #default move if pokemon has no stock moves
    if len(start_moves) == 0:
        df.at[pkmn, 'move1'] = 'tackle'
    if len(start_moves) >= 4:
        randomMoves = random.sample(start_moves, 4)
        df.at[pkmn, 'move1'] = movelist.at[randomMoves[0]-1, 'identifier']
        df.at[pkmn, 'move2'] = movelist.at[randomMoves[1]-1, 'identifier']
        df.at[pkmn, 'move3'] = movelist.at[randomMoves[2]-1, 'identifier']
        df.at[pkmn, 'move4'] = movelist.at[randomMoves[3]-1, 'identifier']
    if len(start_moves) == 3:
        df.at[pkmn, 'move1'] = movelist.at[start_moves[0]-1, 'identifier']
        df.at[pkmn, 'move2'] = movelist.at[start_moves[1]-1, 'identifier']
        df.at[pkmn, 'move3'] = movelist.at[start_moves[2]-1, 'identifier']
    if len(start_moves) == 2:
        df.at[pkmn, 'move1'] = movelist.at[start_moves[0]-1, 'identifier']
        df.at[pkmn, 'move2'] = movelist.at[start_moves[1]-1, 'identifier']
    if len(start_moves) == 1:
        df.at[pkmn, 'move1'] = movelist.at[start_moves[0]-1, 'identifier']

df['xp_accumulated'] = 0
df['level'] = 0

df.to_csv("../data/new_pokemon_withMoves.csv", index = False, quoting = csv.QUOTE_NONNUMERIC)
