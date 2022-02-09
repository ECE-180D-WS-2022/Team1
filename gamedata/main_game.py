import pokemon as pk
import moves as mv
import numpy as np
import sys
import time
#import pokepy
#import json
import os
import random

full_movelist = mv.import_moves(6) #6 moves
full_pokemonlist = pk.import_pokemon(full_movelist, 3) #3 pkmn

def save_game(playerTeam):
    if os.path.exists("savefile.txt"):
        os.remove("savefile.txt")
        print("old savefile removed")
        f = open("savefile.txt", "w")
        for mon in playerTeam:
            f.write(mon.name)
            f.write("\n")
            f.write(mon.type)
            f.write("\n")
            f.write(str(mon.hp))
            f.write("\n")
            f.write(str(mon.atk))
            f.write("\n")
            f.write(str(mon.defense))
            f.write("\n")
            f.write(str(mon.spatk))
            f.write("\n")
            f.write(str(mon.spdef))
            f.write("\n")
            f.write(str(mon.speed))
            f.write("\n")
            f.write(str(mon.battleXP))
            f.write("\n")
            f.write(mon.moves[0].name)
            f.write("\n")
            f.write(mon.moves[1].name)
            f.write("\n")
            f.write(mon.moves[2].name)
            f.write("\n")
            f.write(mon.moves[3].name)
            f.write("\n")
            f.write(str(mon.xp))
            f.write("\n")
            f.write(str(mon.lvl))
            f.write("\n")

        print("new savefile created")

    else:
        print("savefile does not exist, creating one.")
        f = open("savefile.txt", "w")
        print("new savefile created")

    return

def load_game(move_list):
    loadTeam = []
    with open('savefile.txt') as f:
        data = f.read().splitlines()
    #use number of lines in savedata to determine team size
    #each saved pokemon uses 14 lines
    teamSize = int(len(data)/14)
    #print(teamSize)

    for i in range(teamSize):
        pName = data[15*i]
        pType = data[(15*i) + 1]
        pStats = []
        pMoveName = []
        pStats.append(int(data[(15*i) + 2])) #hp
        pStats.append(int(data[(15*i) + 3])) #atk
        pStats.append(int(data[(15*i) + 4])) #def
        pStats.append(int(data[(15*i) + 5])) #spatk
        pStats.append(int(data[(15*i) + 6])) #spdef
        pStats.append(int(data[(15*i) + 7])) #spdef
        pStats.append(int(data[(15*i) + 8])) #xpreward
        pMoveName.append(data[(15*i) + 9])   #move1
        pMoveName.append(data[(15*i) + 10])   #move2
        pMoveName.append(data[(15*i) + 11])  #move3
        pMoveName.append(data[(15*i) + 12])  #move4

        #import the move objects and associate them with pokemon
        pMoves = []
        for name in pMoveName:
            for move in move_list:
                if (name == move.name):
                    pMoves.append(move)

        object = pk.pokemon(pName, pType, pMoves, pStats)

        #assign total XP and level to object
        object.xp = int(data[(15*i) + 13])
        object.lvl = int(data[(15*i) + 14])

        #append the object to the loaded team
        loadTeam.append(object)

    return loadTeam

def test_loadgame():
    #print("test")

    #full_movelist[0].print_move()
    #full_movelist[1].print_move()
    #full_movelist[2].print_move()
    #full_movelist[3].print_move()
    #full_movelist[4].print_move()
    #full_movelist[5].print_move()

    #for i in full_pokemonlist:
    #    i.print_pokemon()
    #    print()

    #print(full_movelist[1].find_effectiveness("Fire"))

    playerTeam = []
    playerTeam.append(full_pokemonlist[0])
    playerTeam.append(full_pokemonlist[1])
    #playerTeam[0].lvl = 10
    save_game(playerTeam)

    playerTeam = load_game(full_movelist)
    for i in playerTeam:
        i.print_pokemon()
        print()
    return

def test_levelscaling():
    tempTeam = []
    tempTeam.append(full_pokemonlist[0])
    tempTeam.append(full_pokemonlist[1])
    tempTeam.append(full_pokemonlist[2])
    playerTeam[2].scale_stats(100)
    playerTeam[2].print_pokemon()

playerTeam = []
playerTeam.append(full_pokemonlist[0])
playerTeam.append(full_pokemonlist[1])
playerTeam.append(full_pokemonlist[2])
#test_levelscaling()
#test_loadgame()
pk.battle_random(playerTeam, full_pokemonlist, len(playerTeam), 3)
print("done")
