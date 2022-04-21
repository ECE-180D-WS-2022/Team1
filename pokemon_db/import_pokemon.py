import numpy as np
import sys
import time
#import pokepy
import random
import os
import copy
import csv
import pandas as pd

pd.set_option('precision', 0)
out = pd.read_csv('pokemon_names.csv', index_col = 0)
del out["species_id"]
del out["height"]
del out["weight"]
del out["order"]
del out["is_default"]
out.rename(columns={"identifier": "name", "base_experience": "xp_reward"}, inplace=True)

out.columns = out.columns.str.lower()

#truncate unused pokemon
out.drop(range(10001, 10229), axis = 0, inplace = True)

#PARSE IN POKEMON TYPES
types = pd.read_csv('pokemon_types.csv')
#truncate unused pokemon
types.drop(range(1340, 1728), axis = 0, inplace = True)
#using only primary types; drop rows containing 'secondary' types
for index in range(0, types.shape[0]):
    if (types.at[index, "slot"] == 2):
        types.drop(index, axis = 0, inplace = True)
del types["id_1"]
del types["slot"]
#output to reset dataframe indices
types.to_csv("../pokemon_db/types_test.csv", index = False, quoting = csv.QUOTE_NONNUMERIC)
types = pd.read_csv('types_test.csv')
#add types column to exported dictionary
for index in range(0, 898):
    if (types.at[index, "type_id"] == 1):
        out.at[index+1, "type"] = "normal"

    if (types.at[index, "type_id"] == 2):
        out.at[index+1, "type"] = "fighting"

    if (types.at[index, "type_id"] == 3):
        out.at[index+1, "type"] = "flying"

    if (types.at[index, "type_id"] == 4):
        out.at[index+1, "type"] = "poison"

    if (types.at[index, "type_id"] == 5):
        out.at[index+1, "type"] = "ground"

    if (types.at[index, "type_id"] == 6):
        out.at[index+1, "type"] = "rock"

    if (types.at[index, "type_id"] == 7):
        out.at[index+1, "type"] = "bug"

    if (types.at[index, "type_id"] == 8):
        out.at[index+1, "type"] = "ghost"

    if (types.at[index, "type_id"] == 9):
        out.at[index+1, "type"] = "steel"

    if (types.at[index, "type_id"] == 10):
        out.at[index+1, "type"] = "fire"

    if (types.at[index, "type_id"] == 11):
        out.at[index+1, "type"] = "water"

    if (types.at[index, "type_id"] == 12):
        out.at[index+1, "type"] = "grass"

    if (types.at[index, "type_id"] == 13):
        out.at[index+1, "type"] = "electric"

    if (types.at[index, "type_id"] == 14):
        out.at[index+1, "type"] = "psychic"

    if (types.at[index, "type_id"] == 15):
        out.at[index+1, "type"] = "ice"

    if (types.at[index, "type_id"] == 16):
        out.at[index+1, "type"] = "dragon"

    if (types.at[index, "type_id"] == 17):
        out.at[index+1, "type"] = "dark"

    if (types.at[index, "type_id"] == 18):
        out.at[index+1, "type"] = "fairy"

#PARSE IN POKEMON STATS
stats = pd.read_csv('pokemon_stats.csv')
#stat order: hp/atk/def/spatk/spdef/spd
for index in range(0, 5388):
    if (stats.at[index, "stat_id"] == 1):
        out.at[stats.at[index, "id"], "hp"] = int(stats.at[index, "base_stat"])
    if (stats.at[index, "stat_id"] == 2):
        out.at[stats.at[index, "id"], "atk"] = int(stats.at[index, "base_stat"])
    if (stats.at[index, "stat_id"] == 3):
        out.at[stats.at[index, "id"], "def"] = int(stats.at[index, "base_stat"])
    if (stats.at[index, "stat_id"] == 4):
        out.at[stats.at[index, "id"], "spatk"] = int(stats.at[index, "base_stat"])
    if (stats.at[index, "stat_id"] == 5):
        out.at[stats.at[index, "id"], "spdef"] = int(stats.at[index, "base_stat"])
    if (stats.at[index, "stat_id"] == 6):
        out.at[stats.at[index, "id"], "spd"] = int(stats.at[index, "base_stat"])

#PARSE IN INITIAL MOVES(?)

#ADD COLUMNS TO STORE LEVEL AND TOTAL XP

#remove decimals?
#out["id"].round()
#export
print(out)
out.to_csv("../data/new_pokemon.csv", index = False, quoting = csv.QUOTE_NONNUMERIC)

'''
out['xp_reward'] = 82
out["move1"] = "Thunderbolt"
out["move2"] = "Tackle"
out["move3"] = "Water Gun"
out["move4"] = "Flamethrower"
out["xp_accumulated"] = 0
out["level"] = 0

out.columns = out.columns.str.lower()


out.to_csv( "../pokemon_db/import_pokemon_filtered.csv", index = False, quoting=csv.QUOTE_NONNUMERIC)
#print(out)

with open('import_pokemon_filtered.csv', 'rt') as inp, open('import_pokemon_filtered_2.csv', 'wt') as out:
    writer = csv.writer(out)
    for row in csv.reader(inp):
        if row[3] != "0":
            writer.writerow(row)

out = pd.read_csv('import_pokemon_filtered_2.csv')
del out['is_default']

out.to_csv( "../pokemon_db/import_pokemon_filtered_3.csv", index = False, quoting=csv.QUOTE_NONNUMERIC)
'''
