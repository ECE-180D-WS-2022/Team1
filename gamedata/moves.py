import sys
import time
import pokepy

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
        moveName = data[6*i]
        moveType = data[(6*i) + 1]
        movePower = int(data[(6*i) + 2])
        movePP = int(data[(6*i) + 3])
        moveAcc = float(data[(6*i) + 4])
        moveDesc = data[(6*i) + 5]
        object = move(moveName, moveType, movePower, movePP, moveAcc, moveDesc)
        movelist.append(object)

    return movelist

class move:
    def __init__(self, name, type, power, pp, accuracy, description):
        self.name = name
        self.type = type
        self.power = power
        self.pp = pp
        self.acc = accuracy
        self.desc = description

    def print_move(self):
        print(self.name)
        print("Move Type: ", self.type)
        print("Move Power: ", self.power)
        print("Move PP: ", self.pp)
        print("Move Accuracy", self.acc)
        print(self.desc)
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
