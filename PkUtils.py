import pandas as pd
import random
import numpy as np
import random

def import_learnset():
    print("importing learnset")
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
    print("finished importing learnset")
    return array


def learn_moves(pk_df, lvl, learnset):

    ans = pk_df.copy()

    #find pokemon ID number
    dictionary = pd.read_csv("data/new_pokemon.csv", index_col = "name")
    pokemon_id = ans.loc["id"]

    #if level learnset is not empty
    if learnset[pokemon_id-1][lvl] :
        #find name of move to be learned
        moves = pd.read_csv("data/moves.csv")
        #print(ans)
        #print(pokemon_id)
        #print(learnset[pokemon_id - 1][lvl][0])
        move_ids = learnset[pokemon_id - 1][lvl]
        for move_id in move_ids:
            move_learned = moves.loc[move_id == moves["id"]]
            move_name = move_learned.at[move_id-1, "identifier"]
            #check if move already exists
            if (ans.loc["move1"] == move_name or ans.loc["move2"] == move_name or ans.loc["move3"] == move_name or ans.loc["move4"] == move_name):
                temp = 0
            #print(move_learned)
            #check if there are empty move slots
            elif pd.isnull(ans.loc["move2"]):
                ans.at["move2"] = move_name

            elif pd.isnull(ans.loc["move3"]):
                ans.at["move3"] = move_name

            elif pd.isnull(ans.loc["move4"]):
                ans.at["move4"] = move_name
            #if no empty move slots, just randomly replace one
            else:
                index = random.randrange(4) + 1
                moveIdentifier = "move" + str(index)
                ans.at[moveIdentifier] = move_learned.at[move_id-1, "identifier"]


    return ans

def level_up (pk_df, xp_amt, learnset):
    #1000 xp to level up
    current_xp =  pk_df["xp_accumulated"]
    current_xp += xp_amt
    ans = pk_df.copy()
    ans["xp_accumulated"] = current_xp

    if int(current_xp) // 1000 >= int(pk_df["level"]):
        # level up
        # get base stats
        basepk_df = pd.read_csv("data/new_pokemon_withMoves.csv")
        basepk_df = basepk_df.loc[basepk_df["name"] == pk_df["name"]]
        # use base stats to calculate new level
        lvl = int(current_xp) // 1000 + 1
        ans["level"] = lvl
        ans["hp"] = int(((((2*int(basepk_df["hp"])) + random.randrange(28,31) + 20.25) * lvl)/100) + lvl + 10)
        ans["attack"] = int(((((2*basepk_df["attack"]) + random.randrange(28,31) + 20.25) * lvl)/100) + 5)
        ans["defense"] = int(((((2*basepk_df["defense"]) + random.randrange(28,31) + 20.25) * lvl)/100) + 5)
        ans["special_attack"] = int(((((2*basepk_df["special_attack"]) + random.randrange(28,31) + 20.25) * lvl)/100) + 5)
        ans["special_defense"] = int(((((2*basepk_df["special_defense"]) + random.randrange(28,31) + 20.25) * lvl)/100) + 5)
        ans["speed"] = int(((((2*basepk_df["speed"]) + random.randrange(28,31) + 20.25) * lvl)/100) + 5)

        ans = learn_moves(ans, lvl, learnset)

    return ans

def bot_level_up (pk_df, xp_amt, learnset):
    #1000 xp to level up
    current_xp =  pk_df["xp_accumulated"]
    current_xp += xp_amt
    ans = pk_df.copy()
    ans["xp_accumulated"] = current_xp

    basepk_df = pd.read_csv("data/new_pokemon_withMoves.csv")
    basepk_df = basepk_df.loc[basepk_df["name"] == pk_df["name"]]

    lvl = int(current_xp) // 1000 + 1
    ans["level"] = lvl
    ans["hp"] = int(((((2*int(basepk_df["hp"])) + random.randrange(28,31) + 20.25) * lvl)/100) + lvl + 10)
    ans["attack"] = int(((((2*basepk_df["attack"]) + random.randrange(28,31) + 20.25) * lvl)/100) + 5)
    ans["defense"] = int(((((2*basepk_df["defense"]) + random.randrange(28,31) + 20.25) * lvl)/100) + 5)
    ans["special_attack"] = int(((((2*basepk_df["special_attack"]) + random.randrange(28,31) + 20.25) * lvl)/100) + 5)
    ans["special_defense"] = int(((((2*basepk_df["special_defense"]) + random.randrange(28,31) + 20.25) * lvl)/100) + 5)
    ans["speed"] = int(((((2*basepk_df["speed"]) + random.randrange(28,31) + 20.25) * lvl)/100) + 5)

    for i in (range(2, lvl)):
        ans = learn_moves(ans, i, learnset)

    return ans
