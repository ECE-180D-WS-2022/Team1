import pokemon as pk
import moves as mv
import numpy as np
import sys

full_movelist = mv.import_moves()
full_pokemonlist = pk.import_pokemon(full_movelist)

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
