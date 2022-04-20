import numpy as np
import sys
import time
#import pokepy
import random
import os
import copy
import csv
import pandas as pd

'''
pd.set_option('precision', 0)
df = pd.read_csv('learnset.csv', iterator = True, chunksize = 5000)
for chunk in df:
    for index in chunk:
        if (chunk.at[index, "version_group_id"] != 20):
            chunk.drop(index, axis = 0, inplace = True)
'''
'''
df = pd.read_csv('learnset.csv')
#first filter out all gen except for "18" (ultra sun/moon; last gen where pokemon
#can be transferred

for index in range(0, df.shape[0]):
    if (df.at[index, "version_group_id"] != 18):
        df.drop(index, axis = 0, inplace = True)

        #if (df.at[index, "pokemon_move_method_id"] != 1):
            #df.drop(index, axis = 0, inplace = True)

#reset indices w/ new csv
df.to_csv( "../data/truncated_learnset.csv", index = False, quoting=csv.QUOTE_NONNUMERIC)
'''

'''
df = pd.read_csv('truncated_learnset.csv')
#filter out  non-learned moves
for index in range(0, df.shape[0]):
    if (df.at[index, "pokemon_move_method_id"] != 1):
        df.drop(index, axis = 0, inplace = True)

df.to_csv( "../data/truncated_learnset_1.csv", index = False, quoting=csv.QUOTE_NONNUMERIC)
'''

'''
df = pd.read_csv('truncated_learnset_1.csv')
#delete unneeded columns
#del df["version_group_id"]
del df["order"]

#filter out  non-learned moves
for index in range(0, df.shape[0]):
    if (df.at[index, "pokemon_move_method_id"] != 1):
        df.drop(index, axis = 0, inplace = True)

df.to_csv( "../data/truncated_learnset_2.csv", index = False, quoting=csv.QUOTE_NONNUMERIC)
'''
df = pd.read_csv('truncated_learnset_2.csv')
#remove generation 19, and delete generation column and learn method column
for index in range(0, df.shape[0]):
    if (df.at[index, "version_group_id"] == 19):
        df.drop(index, axis = 0, inplace = True)

del df["version_group_id"]
del df["pokemon_move_method_id"]
#export
df.to_csv( "../data/final_learnset.csv", index = False, quoting=csv.QUOTE_NONNUMERIC)
#13-24, 46-49, 56-57, 69-71, 74-76, 84-89, 96-97, 100-101, 152-162, 165-168
#179-181, 187-193, 198, 200-201, 203-205, 207, 209-210, 216-219, 228-229,
#231-232, 234-235, 261-262, 265-269, 276-277, 283-289, 296-297, 299-301
#307-308, 311-314, 316-317, 322-323, 325-327, 331-332, 335-336, 351-354,
#357-358, 366-368, 370, 386-402, 408-414, 417-419, 424, 429-433, 441, 455-457
#469, 472, 476, 489-493, 495-505, 511-516, 522-523, 540-542, 580-581, 585-586
#594, 602-604, 648, 650-658, 664-673, 676, 720, 731-735, 739-741, 774-775, 779
