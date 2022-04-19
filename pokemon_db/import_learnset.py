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
df = pd.read_csv('learnset.csv')
#first filter out all gen except for "20"
#also filter out non-learned moves
for index in range(0, df.shape[0]):
    if (df.at[index, "version_group_id"] != 20):
        df.drop(index, axis = 0, inplace = True)
    #if (df.at[index, "pokemon_move_method_id"] != 1):
        #df.drop(index, axis = 0, inplace = True)

#reset indices w/ new csv
df.to_csv( "../pokemon_db/truncated_learnset.csv", index = False, quoting=csv.QUOTE_NONNUMERIC)
