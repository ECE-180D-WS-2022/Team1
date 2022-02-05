import moves as mv

def import_pokemon(move_list):
    pokemon_list = []

    #f = open('monsterlist.txt','r')
    #data = f.readlines()
    #f.close()

    with open('monsterlist.txt') as f:
        data = f.read().splitlines()

    #testing reading file values
    #print(data[0])
    #print(data[1])
    #print(data[2])
    #print(data[3])
    #print(data[4])
    #print(data[5])
    #print(data[6])
    #print(data[7])
    #print(data[8])
    #print(data[9])
    #print(data[10])
    #print(data[11])

    #append pokemon list with full list of pokemon
    for i in range(3):  #3 total pokemon
        print(i)
        #start by pulling the data values

        pName = data[12*i]
        pType = data[(12*i) + 1]

        pStats = []
        pMoveName = []
        pStats.append(int(data[(12*i) + 2]))
        pStats.append(int(data[(12*i) + 3]))
        pStats.append(int(data[(12*i) + 4]))
        pStats.append(int(data[(12*i) + 5]))
        pStats.append(int(data[(12*i) + 6]))
        pStats.append(int(data[(12*i) + 7]))
        pMoveName.append(data[(12*i) + 8])
        pMoveName.append(data[(12*i) + 9])
        pMoveName.append(data[(12*i) + 10])
        pMoveName.append(data[(12*i) + 11])

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
        self.xp = 0
        self.battleXP = stats[5]
        self.moves = moves

    def print_pokemon(self):
        print(self.name)
        print("Type: ", self.type)
        print("HP: ", self.hp)
        print("ATK: ", self.atk)
        print("DEF: ", self.defense)
        print("SPATK: ", self.spatk)
        print("SPDEF: ", self.spdef)
        print("EXP Gained: ", self.battleXP)
        print()
        for i in self.moves:
            i.print_move()
            print()
