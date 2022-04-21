import numpy as np
import sys
import time
#import pokepy
import random
import os
import copy
import csv
import pandas as pd



df = pd.read_csv('moves.csv', index_col = 0)
del df["super_contest_effect_id"]
del df["contest_effect_id"]
del df["contest_type_id"]
del df["effect_chance"]
del df["effect_id"]
#del df["damage_class_id"]
del df["target_id"]
del df["priority"]
del df["generation_id"]

df.columns = df.columns.str.lower()

df.drop(range(10001, 10019), axis = 0, inplace = True)

for index in range(1, 827):

    if (df.at[index, "type_id"] == 1):
        df.at[index, "type_id"] = "normal"

    if (df.at[index, "type_id"] == 2):
        df.at[index, "type_id"] = "fighting"

    if (df.at[index, "type_id"] == 3):
        df.at[index, "type_id"] = "flying"

    if (df.at[index, "type_id"] == 4):
        df.at[index, "type_id"] = "poison"

    if (df.at[index, "type_id"] == 5):
        df.at[index, "type_id"] = "ground"

    if (df.at[index, "type_id"] == 6):
        df.at[index, "type_id"] = "rock"

    if (df.at[index, "type_id"] == 7):
        df.at[index, "type_id"] = "bug"

    if (df.at[index, "type_id"] == 8):
        df.at[index, "type_id"] = "ghost"

    if (df.at[index, "type_id"] == 9):
        df.at[index, "type_id"] = "steel"

    if (df.at[index, "type_id"] == 10):
        df.at[index, "type_id"] = "fire"

    if (df.at[index, "type_id"] == 11):
        df.at[index, "type_id"] = "water"

    if (df.at[index, "type_id"] == 12):
        df.at[index, "type_id"] = "grass"

    if (df.at[index, "type_id"] == 13):
        df.at[index, "type_id"] = "electric"

    if (df.at[index, "type_id"] == 14):
        df.at[index, "type_id"] = "psychic"

    if (df.at[index, "type_id"] == 15):
        df.at[index, "type_id"] = "ice"

    if (df.at[index, "type_id"] == 16):
        df.at[index, "type_id"] = "dragon"

    if (df.at[index, "type_id"] == 17):
        df.at[index, "type_id"] = "dark"

    if (df.at[index, "type_id"] == 18):
        df.at[index, "type_id"] = "fairy"


df.to_csv("../data/moves.csv", index = False, quoting=csv.QUOTE_NONNUMERIC)
