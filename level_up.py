import numpy as np
import sys
import time
import random
import os
import copy
import csv
import pandas as pd
import string
def import_learnset():
    df = pd.read_csv('data/final_learnset.csv')
    #array = [pokemon: 898][level: 0->100]

    #NOTE: POKEMON IDS ARE NOT ZERO INDEXED, BUT ARRAY IS ZERO-INDEXED
    #DO NOT FORGET TO -1 TO POKEMON ID TO AVOID OUT OF BOUNDS OR MISLABELING

    #find list of moves to omit
    #remove status moves and moves w/ fancy damage calculations
    omit = []
    moves = pd.read_csv('data/moves.csv')
    for x in range(826):
        data = moves.iloc[x]
        if ((pd.isnull(data.iloc[3])) or data.iloc[6] == 1):
            omit.append(data.iloc[0])

    #define the learnset array
    array = [[[] for x in range(101)] for y in range(898)]
    #print(df.iloc[3])
    #test = df.iloc[3]
    #print(test.iloc[2])
    #learnset[700][100] = 0
    for x in range(14371):
        #poo = 0
        #iloc format: [id, move_id, level]
        data = df.iloc[x]
        #only add if move is not in the omit list
        if (not np.isin(data.iloc[1], omit) ):
            array[data.iloc[0] - 1][data.iloc[2]].append(data.iloc[1])

    return array

'''
    #remove them moves
    for row in range(898):
        for col in range(101):
            if (len(array[row][col]) > 0 and np.any( np.isin(array[row][col], omit) ) ):
                #array[row][col] = 0
                #poo = 0
'''

def initialize_start_moves():
    return

def main():
    print("test")
    learnset = import_learnset()
    print("haxorus #612")
    print(learnset[611])
    print("alakazam #65")
    print(learnset[64])
    print("timburr #532")
    print(learnset[531])
    print("ID #1?")
    print(learnset[0])

if __name__ == "__main__":
    main()
