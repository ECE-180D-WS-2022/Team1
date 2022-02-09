import moves as mv
import numpy as np
import sys
import time
#import pokepy
import random

def import_pokemon(move_list, num_pkmn):
    pokemon_list = []

    #f = open('monsterlist.txt','r')
    #data = f.readlines()
    #f.close()

    with open('monsterlist.txt') as f:
        data = f.read().splitlines()

    #append pokemon list with full list of pokemon
    for i in range(num_pkmn):  #3 total pokemon
        #print(i)
        #start by pulling the data values

        pName = data[13*i]
        pType = data[(13*i) + 1]

        pStats = []
        pMoveName = []
        pStats.append(int(data[(13*i) + 2])) #hp
        pStats.append(int(data[(13*i) + 3])) #atk
        pStats.append(int(data[(13*i) + 4])) #def
        pStats.append(int(data[(13*i) + 5])) #spatk
        pStats.append(int(data[(13*i) + 6])) #spdef
        pStats.append(int(data[(13*i) + 7])) #speed
        pStats.append(int(data[(13*i) + 8])) #xpreward
        pMoveName.append(data[(13*i) + 9])   #move1
        pMoveName.append(data[(13*i) + 10])   #move2
        pMoveName.append(data[(13*i) + 11])  #move3
        pMoveName.append(data[(13*i) + 12])  #move4

        #create list of moves for the pokemon instead of 4 separate moves
        pMoves = []
        for name in pMoveName:
            for move in move_list:
                if (name == move.name):
                    pMoves.append(move)

        object = pokemon(pName, pType, pMoves, pStats)
        pokemon_list.append(object)

    return pokemon_list

class pokemon:
    def __init__(self, name, type, moves, stats):
        self.name = name
        self.type = type
        self.hp = stats[0]
        self.atk = stats[1]
        self.defense = stats[2]
        self.spatk = stats[3]
        self.spdef = stats[4]
        self.speed = stats[5]
        self.battleXP = stats[6]
        self.moves = moves
        self.xp = 0
        self.lvl = 1

    def print_pokemon(self):
        print(self.name)
        print("Type: ", self.type)
        print("HP: ", self.hp)
        print("ATK: ", self.atk)
        print("DEF: ", self.defense)
        print("SPATK: ", self.spatk)
        print("SPDEF: ", self.spdef)
        print("SPD: ", self.speed)
        print("EXP Reward: ", self.battleXP)
        print("Total XP: ", self.xp)
        print("Current Level: ", self.lvl)
        print()
        for i in self.moves:
            i.print_move()
            print()

    def update_level(self, gained_xp):
        #1000 xp to level up
        self.xp += gained_xp
        if (self.xp > (self.lvl * 1000)):
            print()
            #TODO: implement leveling
        return

    #function meant for scaling the HP stats
    def scale_hp(self, level):
        self.hp = (((((2*self.hp) + random.randrange(0,31) + 20.25) * level)/100) + level + 10)
        return
    #function meant for scaling all other stats
    def scale_others(self, level):
        self.atk = (((((2*self.hp) + random.randrange(0,31) + 20.25) * level)/100) + 5)
        self.defense = (((((2*self.hp) + random.randrange(0,31) + 20.25) * level)/100) + 5)
        self.spatk = (((((2*self.hp) + random.randrange(0,31) + 20.25) * level)/100) + 5)
        self.spdef = (((((2*self.hp) + random.randrange(0,31) + 20.25) * level)/100) + 5)
        self.speed = (((((2*self.hp) + random.randrange(0,31) + 20.25) * level)/100) + 5)
        return

    #function that takes in average level, and scales
    #pokemon to the approximate states of avg level
    def scale_stats(self, level):
        self.scale_hp(level)
        self.scale_others(level)
        return

def battle_random(playerTeam, pokemonList, playerTeamSize, numPokemon):
    #have player battle against a random CPU
    battle_participants = []    #track number of participants
    health = []                 #array that stores team health
    total_lvl = 0
    for mon in playerTeam:      #store pokemon health
        health.append(mon.hp)
        total_lvl += mon.lvl

    activePokemon = 0           #always start with first pokemon
    battle_participants.append(activePokemon)   #append to participants

    #function that checks if player still has pokemon
    #that are able to battle
    def health_check(health_arr):
        total = sum(health_arr[i] for i in range(len(health_arr)))
        #print(total)
        return (total > 0)

    #print(health_check(health))

    #generate a random opponent (use avg team level, rounded down)
    avg_lvl = int(total_lvl/len(playerTeam))
    #print(avg_lvl)


    #while player still has pokemon that can battle,
    #keep battling
    #while(health_check(health)):



    #return

def battle_opponent(playerTeam):
    #have player battle against another live player

    return
