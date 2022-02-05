import sys

def import_moves():
    movelist = []

    #get all data from movelist file
    #f = open('movelist.txt','r')
    #data = f.readlines()
    #f.close()

    with open('movelist.txt') as f:
        data = f.read().splitlines()

    #append each move into full movelist with data
    for i in range(6):  #6 moves
        moveName = data[6*i]
        moveType = data[(6*i) + 1]
        movePower = data[(6*i) + 2]
        movePP = data[(6*i) + 3]
        moveAcc = data[(6*i) + 4]
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
