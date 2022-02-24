# This will represent a client in the game
# right now we will be using hardcoded string of Justin, but will be passed in from

import paho.mqtt.client as mqtt
import numpy as np
import argparse
import os
import csv
import pandas as pd
import numpy as np

################################# SETUP ########################################################################
##### Command line interface to pass in name #####
parser = argparse.ArgumentParser(
    description="Start the game by passing in python3 client.py username"
)
parser.add_argument("username", type=str, help="username used in game")
args = parser.parse_args()

##### Write a new folder for username #####
path = "data/users/" + args.username
if not os.path.isdir(path):
    os.mkdir(path, 0o777)

    ##### write into the folder gamestats.csv and wins.csv ######
    ## gamestats.csv ##
    fieldnames = ["games_played", "wins"]
    starting_entries = [0, 0]
    game_stats_df = pd.DataFrame(columns=fieldnames)
    game_stats_df = game_stats_df.append(
        {"games_played": 0, "wins": 0}, ignore_index=True
    )
    game_stats_df.to_csv(
        path + "/gamestats.csv", index=False, quoting=csv.QUOTE_NONNUMERIC
    )

    ## teams.csv ##
    fieldnames = [
        "name",
        "type",
        "hp",
        "attack",
        "defense",
        "special attack",
        "special defense",
        "speed",
        "xp reward",
        "move1",
        "move2",
        "move3",
        "move4",
        "xp_accumulated",
        "level",
    ]
    df = pd.read_csv("../data/pokemon.csv")
    team_df = pd.DataFrame(columns=fieldnames)
    team_df = team_df.append(df.loc[df["name"] == "Pikachu"], ignore_index=True)
    team_df.to_csv(path + "/team.csv", index=False, quoting=csv.QUOTE_NONNUMERIC)
else:
    game_stats_df = pd.read_csv(path + "/gamestats.csv")
    team_df = pd.read_csv(path + "/team.csv")
#################################################################################################################

################################# MQTT SETUP ###################################################################
"""
  Notes:
    Handling how to deal with someone sending a game request in the middle of training or some shit
"""
in_game = 0
opponent = ""


def on_connect(client, userdata, flags, rc):
    print("Connection returned result: " + str(rc))
    client.subscribe("ece180d/" + args.username, qos=1)


# The callback of the client when it disconnects.
def on_disconnect(client, userdata, rc):
    if rc != 0:
        print("Unexpected Disconnect")
    else:
        print("Expected Disconnect")


# The default message callback.
"""
Request game: "0,username"
Respond request: "1,[0 - deny/1 - accept]"
Send team: "2,[json]"
Send move: "3,pokemon,movename,stat,amount"
Game over?: "4,winner"
"""


def on_message(client, userdata, message):
    message.payload.split(" ")
    damage_done = int(message.payload)
    print('Damage done is:"' + str(message.payload))


# 1. create a client instance.
client = mqtt.Client()
# add additional client options (security, certifications, etc.)
# many default options should be good to start off.
# add callbacks to client.
client.on_connect = on_connect
client.on_disconnect = on_disconnect
client.on_message = on_message
# 2. connect to a broker using one of the connect*() functions.
client.connect_async("test.mosquitto.org")
# 3. call one of the loop*() functions to maintain network traffic flow with the broker.
client.loop_start()
# 4. use subscribe() to subscribe to a topic and receive messages.
# 5. use publish() to publish messages to the broker.
# payload must be a string, bytearray, int, float or None.
################################################################################################################


###### GAME LOGIC SPLIT #########################################################################################
"""
  Notes:
    Have to be able to loop back onto this
    Also have to be able to handle the case of someone sending a battle request(maybe can have both be requesting for battle)
"""
end_flag = 0
while True:
    decision = input("Enter (1) for Training (2) for Battling:\n")
    #### Training Path ####
    if decision == "1":
        print("Available Pokemons are:")
        print(team_df["name"].tolist())
        working_pokemon = ""
        while working_pokemon not in team_df["name"].tolist():
            working_pokemon = input("Please type Pokemon name you want to train\n")
        curr_accumulated_xp = 0

        ## Pose Recognition to train ##
        while True:
            # TO DO: Incorporate Pose Recognition Here #
            curr_accumulated_xp = 20
            break
        team_df.loc[
            team_df.name == working_pokemon, "xp_accumulated"
        ] += curr_accumulated_xp

        # TO DO: Leveling up system logic here #

    #### Battling Path ####
    if decision == "2":
        pass
    end_flag = input("Press (1) to continue to top of screen or (2) to exit:\n")
    if end_flag == "2":
        print("goodbye!")
        break


################################################################################################################


###### END ######################################################################################################
"""
At the end write persistently to all the files that were changed
"""
game_stats_df.to_csv(path + "/gamestats.csv", index=False, quoting=csv.QUOTE_NONNUMERIC)
team_df.to_csv(path + "/team.csv", index=False, quoting=csv.QUOTE_NONNUMERIC)
#################################################################################################################

# # The callback for when the client receives a CONNACK response from the server.
# def on_connect(client, userdata, flags, rc):
#   print("Connection returned result: "+str(rc))
#   client.subscribe("ece180d/justin", qos=1)

# # The callback of the client when it disconnects.
# def on_disconnect(client, userdata, rc):
#     if rc != 0:
#         print('Unexpected Disconnect')
#     else:
#         print('Expected Disconnect')

# # The default message callback.
# def on_message(client, userdata, message):
#     message.payload.split(" ")
#     damage_done = int(message.payload)
#     print('Damage done is:"' + str(message.payload))

# # 1. create a client instance.
# client = mqtt.Client()
# # add additional client options (security, certifications, etc.)
# # many default options should be good to start off.
# # add callbacks to client.
# client.on_connect = on_connect
# client.on_disconnect = on_disconnect
# client.on_message = on_message
# # 2. connect to a broker using one of the connect*() functions.
# client.connect_async("test.mosquitto.org")
# # 3. call one of the loop*() functions to maintain network traffic flow with the broker.
# client.loop_start()
# # 4. use subscribe() to subscribe to a topic and receive messages.
# # 5. use publish() to publish messages to the broker.
# # payload must be a string, bytearray, int, float or None.
# print('Publishing...')
# for i in range(10):
#   client.publish('ece180d/test', f"ping: {i}", qos=1)
# while True:
#   pass
# # 6. use disconnect() to disconnect from the broker.
# client.loop_stop()
# client.disconnect()
