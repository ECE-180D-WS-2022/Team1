#!/usr/bin/python

import Game as gm
import argparse


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Start the game by typing ./pokEEmon.py <username> <id>"
    )

    parser.add_argument("username", type=str, help="your in-game username")
    parser.add_argument("id", type=str, help="your pi id")
    args = parser.parse_args()
    print("Welcome " + args.username)

    game = gm.Game(args.username, args.id)
    game.connect_mqtt()
    game.home_screen()
    game.start_game()
