import pokemon as pk
import moves as mv
import numpy as np
import sys
import time
import pokepy

full_movelist = mv.import_moves(6) #6 moves
full_pokemonlist = pk.import_pokemon(full_movelist, 3) #3 pkmn

print("test")
#full_movelist[0].print_move()
#full_movelist[1].print_move()
#full_movelist[2].print_move()
#full_movelist[3].print_move()
#full_movelist[4].print_move()
#full_movelist[5].print_move()

for i in full_pokemonlist:
    i.print_pokemon()
    print()

print(full_movelist[1].find_effectiveness("Fire"))
