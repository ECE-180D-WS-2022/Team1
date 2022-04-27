import numpy as np
import sys
import time
import random
import os
import copy
import csv
import pandas as pd

def import_learnset():
    df = pd.read_csv('data/final_learnset.csv')
    #array = [pokemon: 898][level: 0->100]

    #NOTE: POKEMON IDS ARE NOT ZERO INDEXED, BUT ARRAY IS ZERO-INDEXED
    #DO NOT FORGET TO -1 TO POKEMON ID TO AVOID OUT OF BOUNDS OR MISLABELING



    #define the learnset array
    array = [[0 for x in range(101)] for y in range(898)]
    #print(df.iloc[3])
    #test = df.iloc[3]
    #print(test.iloc[2])
    #learnset[700][100] = 0
    for x in range(14371):
        poo = 0
        #iloc format: [id, move_id, level]
        data = df.iloc[x]
        array[data.iloc[0] - 1][data.iloc[2]] = data.iloc[1]

    #find list of moves to omit
    #remove status moves and moves w/ fancy damage calculations
    omit = []
    moves = pd.read_csv('data/moves.csv')
    for x in range(826):
        data = moves.iloc[x]
        if (data.iloc[3] == "" or data.iloc[6] == 1):
            omit.append(data.iloc[0])

    #remove them moves
    for row in range(898):
        for col in range(101):
            if (array[row][col] in omit):
                array[row][col] = 0

    return array

def initialize_start_moves():
    return

def main():
    print("test")
    learnset = import_learnset()
    print("haxorus #612") #actually beartic #614
    print(learnset[613])
    print("alakazam #65") #actually machop #67
    print(learnset[66])
    print("timburr #532") #actually conkeldurr #534
    print(learnset[533])
    print("ID #1?")
    print(learnset[0])

if __name__ == "__main__":
    main()
