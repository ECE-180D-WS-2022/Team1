import sys
import time
import random
#import pokepy

def import_moves(num_moves):
    movelist = []

    #get all data from movelist file
    #f = open('movelist.txt','r')
    #data = f.readlines()
    #f.close()

    with open('movelist.txt') as f:
        data = f.read().splitlines()

    #append each move into full movelist with data
    for i in range(num_moves):
        moveName = data[7*i]
        moveType = data[(7*i) + 1]
        movePower = int(data[(7*i) + 2])
        movePP = int(data[(7*i) + 3])
        moveAcc = float(data[(7*i) + 4])
        moveDesc = data[(7*i) + 5]
        special = (data[(7*i) + 6] == "special")
        object = move(moveName, moveType, movePower, movePP, moveAcc, moveDesc, special)
        movelist.append(object)

    return movelist

class move:
    def __init__(self, name, type, power, pp, accuracy, description, isSpecial):
        self.name = name
        self.type = type
        self.power = power
        self.pp = pp
        self.acc = accuracy
        self.desc = description
        self.special = isSpecial

    def print_move(self):
        print(self.name)
        print("Move Type: ", self.type)
        if(self.special):
            print("Special Attack")
        else:
            print("Physical Attack")
        print(self.desc)
        print("Move Power: ", self.power)
        print("Move PP: ", self.pp)
        print("Move Accuracy: ", self.acc)
        return

    def find_effectiveness(self, pkmnType):
        #0 - 17 types
        #normal, fire, water, electric, grass, ice, fighting, poison, ground
        #flying, psychic, bug, rock, ghost, dragon, dark, steel, fairy
        #row = attack type, col = receiving type
        effectiveness_array = [[1,   1,   1,   1,   1,   1,   1,   1,   1,   1,   1,   1,   0.5, 0,   1,   1,   0.5, 1],
                               [1,   0.5, 0.5, 1,   2,   2,   1,   1,   1,   1,   1,   2,   0.5, 1,   0.5, 1,   2,   1],
                               [1,   2,   0.5, 1,   0.5, 1,   1,   1,   2,   1,   1,   1,   2,   1,   0.5, 1,   1,   1],
                               [1,   1,   2,   0.5, 0.5, 1,   1,   1,   0,   2,   1,   1,   1,   1,   0.5, 1,   1,   1],
                               [1,   0.5, 2,   1,   0.5, 1,   1,   0.5, 2,   0.5, 1,   0.5, 2,   1,   0.5, 1,   0.5, 1],
                               [1,   0.5, 0.5, 1,   2,   0.5, 1,   1,   2,   2,   1,   1,   1,   1,   2,   1,   0.5, 1],
                               [2,   1,   1,   1,   1,   2,   1,   0.5, 1,   0.5, 0.5, 0.5, 2,   0,   1,   2,   2,   0.5],
                               [1,   1,   1,   1,   2,   1,   1,   0.5, 0.5, 1,   1,   1,   0.5, 0.5, 1,   1,   0,   2],
                               [1,   2,   1,   2,   0.5, 1,   1,   2,   1,   0,   1,   0.5, 2,   1,   1,   1,   2,   1],
                               [1,   1,   1,   0.5, 2,   1,   2,   1,   1,   1,   1,   2,   0.5, 1,   1,   1,   0.5, 1],
                               [1,   1,   1,   1,   1,   1,   2,   2,   1,   1,   0.5, 1,   1,   1,   1,   0,   0.5, 1],
                               [1,   0.5, 1,   1,   2,   1,   0.5, 0.5, 1,   0.5, 2,   1,   1,   0.5, 1,   2,   0.5, 0.5],
                               [1,   2,   1,   1,   1,   2,   0.5, 1,   0.5, 2,   1,   2,   1,   1,   1,   1,   0.5, 1],
                               [0,   1,   1,   1,   1,   1,   1,   1,   1,   1,   2,   1,   1,   2,   1,   0.5, 1,   1],
                               [1,   1,   1,   1,   1,   1,   1,   1,   1,   1,   1,   1,   1,   1,   2,   1,   0.5, 0],
                               [1,   1,   1,   1,   1,   1,   0.5, 1,   1,   1,   2,   1,   1,   2,   1,   0.5, 1,   0.5],
                               [1,   0.5, 0.5, 0.5, 1,   2,   1,   1,   1,   1,   1,   1,   2,   1,   1,   1,   0.5, 2],
                               [1,   0.5, 1,   1,   1,   1,   2,   0.5, 1,   1,   1,   1,   1,   1,   2,   2,   0.5, 1], ]
        typeList = ["Normal", "Fire", "Water", "Electric", "Grass", "Ice", "Fighting", "Poison", "Ground", "Flying", "Psychic", "Bug", "Rock", "Ghost", "Dragon", "Dark", "Steel", "Fairy",]

        attackType = typeList.index(self.type)
        pkmnType_index = typeList.index(pkmnType)

        multiplier = effectiveness_array[attackType][pkmnType_index]
        return multiplier

    def calculate_damage(self, playerPkmn, targetPkmn):
        '''
        playerPkmn: pokemon object using move
        targetPkmn: pokemon object of move target

        returns: final damage

        '''
        random_mult = random.randrange(85,100) * 0.01       #random multiplier from 0.85 to 1
        damage = 0
        stab = 1
        multiplier = self.find_effectiveness(targetPkmn.type)
        if (playerPkmn.type == self.type): #implement same type attack bonus
            stab = 1.5

        #special attack calc
        if (self.special):
            damage = ((((((2*playerPkmn.lvl)/5)+2)*self.power*(playerPkmn.spatk/targetPkmn.spdef))/50)+2)*stab*multiplier*random_mult
        #physical attack calc
        else:
            damage = ((((((2*playerPkmn.lvl)/5)+2)*self.power*(playerPkmn.atk/targetPkmn.defense))/50)+2)*stab*multiplier*random_mult
        return damage
