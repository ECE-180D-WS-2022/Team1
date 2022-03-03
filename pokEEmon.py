#!/usr/bin/python

import paho.mqtt.client as mqtt
import argparse
import os
import csv
import io
import time
import pandas as pd
import tkinter as tk
from functools import partial
import random
import copy
import shutil

################################# SETUP ########################################################################
##### Command line interface to pass in name #####
parser = argparse.ArgumentParser(
    description="Start the game by typing ./pokEEmon.py <username>"
)

movedict = {"Thunderbolt" : 5, "Tackle" : 10, "Ice" : 2, "Flamethrower" : 6}

parser.add_argument("username", type=str, help="your in-game username")
args = parser.parse_args()
print("Welcome " + args.username)

class Battle:
    def __init__(self, user, battle_id, opp_user, window, client):
        self.user = copy.deepcopy(user)
        self.battle_id = battle_id
        self.opp_user = copy.deepcopy(opp_user)
        self.window = window
        self.client = client
        self.curr_pokemon = 0
        self.opp_pokemon = 0
        self.wait_frame = None
        self.move_frame = None
        self.choose_frame = None
        
    def rcv_battle_mqtt(self, client, userdata, message):
        print("Received move message")
        msg = message.payload
        print(msg)

        msg = str(msg.decode()).split(",")
        print(msg)
        
        if msg and msg[0] == "move" and int(msg[2]) == self.battle_id:
            movename = msg[3]
            #TODO get damage
            damage = movedict[movename]
            hp = self.user.team_df.iloc[self.curr_pokemon, self.user.team_df.columns.get_loc("hp")]
            hp -= damage
            if hp < 0:
                hp = 0
            self.user.team_df.iloc[self.curr_pokemon, self.user.team_df.columns.get_loc("hp")] = hp
            self.move_screen(self.wait_frame)
        if msg and msg[0] == "change" and int(msg[2]) == self.battle_id:
            self.opp_pokemon = int(msg[3])
            self.wait_screen(self.wait_frame)
        else:
            print("Received unexpected message")
        
    def sel_pokemon(self, index):
        self.curr_pokemon = index
        choose_msg = "change,{},{},{}".format(self.user.username, self.battle_id, index)
        self.client.publish("ece180d/pokEEmon/" + self.opp_user.username + "/change", choose_msg)
        self.move_screen(self.choose_frame)

    def do_move(self, move):
        movename = self.user.team_df.iloc[self.curr_pokemon][move]
        #TODO get damage
        damage = movedict[movename]
        opp_hp = self.opp_user.team_df.iloc[self.opp_pokemon, self.opp_user.team_df.columns.get_loc("hp")]
        opp_hp -= damage
        if opp_hp < 0:
            opp_hp = 0
        self.opp_user.team_df.iloc[self.opp_pokemon, self.opp_user.team_df.columns.get_loc("hp")] = opp_hp
        move_msg = "move,{},{},{}".format(self.user.username, self.battle_id, movename)
        self.client.publish("ece180d/pokEEmon/" + self.opp_user.username + "/move", move_msg)
        self.wait_screen(self.move_frame)
        

    def wait_screen(self, prev_frame = None):
        print("Waiting for opponent move")
        if prev_frame:
            prev_frame.pack_forget()
        if self.wait_frame:
            self.wait_frame.destroy()

        self.client.on_message = self.rcv_battle_mqtt
        self.client.subscribe("ece180d/pokEEmon/" + self.user.username + "/move", qos=1)
        self.client.subscribe("ece180d/pokEEmon/" + self.user.username + "/change", qos=1)
        print("Subscribed to " + "ece180d/pokEEmon/" + self.user.username + "/move")
        print("Subscribed to " + "ece180d/pokEEmon/" + self.user.username + "/change")

        self.wait_frame = tk.Frame(self.window)
        wait_label = tk.Label(self.wait_frame, text="Waiting for {} to move".format(self.opp_user.username))
        user_pokemon_name = self.user.team_df.iloc[self.curr_pokemon, self.user.team_df.columns.get_loc("name")]
        userteam_string = self.user.team_df.loc[:, ["name", "hp"]].to_string(index=False)
        userteam_string = userteam_string.replace(user_pokemon_name, "**" + user_pokemon_name)
        userteam_label = tk.Label(self.wait_frame, text="\nYour team: \n{}\n".format(userteam_string))
        opp_pokemon_name = self.opp_user.team_df.iloc[self.opp_pokemon, self.opp_user.team_df.columns.get_loc("name")]
        oppteam_string = self.opp_user.team_df.loc[:, ["name", "hp"]].to_string(index=False)
        oppteam_string = oppteam_string.replace(opp_pokemon_name, "**" + opp_pokemon_name)
        oppteam_label = tk.Label(self.wait_frame, text="\nOpponent team: \n{}\n".format(oppteam_string))
        wait_label.pack()
        userteam_label.pack()
        oppteam_label.pack()
        self.wait_frame.pack()
        
    def move_screen(self, prev_frame = None):
        print("Choose your move")
        if prev_frame:
            prev_frame.pack_forget()
        if self.move_frame:
            self.move_frame.destroy()

        #TODO check for cancel
        self.client.unsubscribe("ece180d/pokEEmon/" + self.user.username + "/move")
        self.client.unsubscribe("ece180d/pokEEmon/" + self.user.username + "/change")
        print("Unsubscribed to " + "ece180d/pokEEmon/" + self.user.username + "/move")
        print("Unsubscribed to " + "ece180d/pokEEmon/" + self.user.username + "/change")         
        
        self.move_frame = tk.Frame(self.window)
        move_label = tk.Label(self.move_frame, text="Choose your move")
        move1_button = tk.Button(self.move_frame, text=self.user.team_df.iloc[self.curr_pokemon]["move1"], command = partial(self.do_move, "move1"))
        move2_button = tk.Button(self.move_frame, text=self.user.team_df.iloc[self.curr_pokemon]["move2"], command = partial(self.do_move, "move2"))
        move3_button = tk.Button(self.move_frame, text=self.user.team_df.iloc[self.curr_pokemon]["move3"], command = partial(self.do_move, "move3"))
        move4_button = tk.Button(self.move_frame, text=self.user.team_df.iloc[self.curr_pokemon]["move4"], command = partial(self.do_move, "move4"))
        user_pokemon_name = self.user.team_df.iloc[self.curr_pokemon, self.user.team_df.columns.get_loc("name")]
        userteam_string = self.user.team_df.loc[:, ["name", "hp"]].to_string(index=False)
        userteam_string = userteam_string.replace(user_pokemon_name, "**" + user_pokemon_name)
        userteam_label = tk.Label(self.move_frame, text="\nYour team: \n{}\n".format(userteam_string))
        opp_pokemon_name = self.opp_user.team_df.iloc[self.opp_pokemon, self.opp_user.team_df.columns.get_loc("name")]
        oppteam_string = self.opp_user.team_df.loc[:, ["name", "hp"]].to_string(index=False)
        oppteam_string = oppteam_string.replace(opp_pokemon_name, "**" + opp_pokemon_name)
        oppteam_label = tk.Label(self.move_frame, text="\nOpponent team: \n{}\n".format(oppteam_string))
        change_button = tk.Button(self.move_frame, text="Change pokEEmon", command = self.choose_screen)
        move_label.pack()
        move1_button.pack()
        move2_button.pack()
        move3_button.pack()
        move4_button.pack()
        userteam_label.pack()
        oppteam_label.pack()
        change_button.pack()

        self.move_frame.pack()

    def choose_screen(self, prev_frame = None):
        if self.move_frame:
            self.move_frame.pack_forget()
        if self.choose_frame:
            self.choose_frame.destroy()

        self.choose_frame = tk.Frame(self.window)
        choose_label = tk.Label(self.choose_frame, text="Choose your pokemon")
        choose_label.pack()
        user_pokemon = self.user.team_df.loc[:,["name","hp"]]
        for row in user_pokemon.itertuples():
            if row.hp > 0:
                pokemon_button = tk.Button(self.choose_frame, text=row.name, command = partial(self.sel_pokemon, row.Index))
                pokemon_button.pack()
        self.choose_frame.pack()

class User:    
    def __init__(self, username = None):
        if username is not None:
            self.username = username
            self.path = "data/users/" + self.username
            self.gamestats_df, self.team_df = self.get_user_files()
        else:
            self.username = None
            self.team_df = None
    
    def get_user_files(self):
        """
        get the appropiate gamestats and team files if it exists, else create the folder and copy in the default
        """
        if not os.path.isdir(self.path):
            os.mkdir(self.path, 0o777)
            shutil.copy2("data/users/default/gamestats.csv", self.path)
            shutil.copy2("data/users/default/team.csv", self.path)

        gamestats_df = pd.read_csv(self.path + "/gamestats.csv")
        team_df = pd.read_csv(self.path + "/team.csv")
        return gamestats_df, team_df

class Game:
    def __init__(self, username):
        self.user = User(username)
        self.opp_user = None
        self.window = None
        self.home_frame = None
        self.receive_frame = None
        self.request_frame = None
        self.response_frame = None
        self.client = None
        self.connected = False
        self.request_num = None
        

    def connect_mqtt(self):
        print("Connecting to MQTT")
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect_mqtt
        self.client.connect("test.mosquitto.org")
        self.client.loop_start()
        while not self.connected:
            time.sleep(0.1)            
       
    def on_connect_mqtt(self, client, userdata, flags, rc):
        print("Connection returned result: " + str(rc))
        if rc == 0:
            print("Connection success")
            self.connected = True
        else:
            print("Connection failed")

    def rcv_request_mqtt(self, client, userdata, message):
        print("Received request message")
        msg = message.payload
        print(msg)

        msg = str(msg.decode()).split(",")
        print(msg)
        
        if msg and msg[0] == "request":
            self.opp_user = User()
            self.opp_user.username = msg[1]
            self.opp_user.team_df = pd.read_csv(io.StringIO(msg[3]), sep='\s+')
            self.request_num = int(msg[2])
            self.receive_screen(msg[1])
        else:
            print("Received unexpected message")

    def rcv_cancel_mqtt(self, client, userdata, message):
        print("Received cancel message")
        msg = message.payload
        print(msg)

        msg = str(msg.decode()).split(",")
        if msg and msg[0] == "cancel" and int(msg[2]) == self.request_num:
            print("received cancel from: " + msg[1])
            self.client.unsubscribe("ece180d/pokEEmon/" + self.user.username + "/cancel")
            print("Unsubscribed from " + "ece180d/pokEEmon/" + self.user.username + "/cancel")
            self.home_screen(self.receive_frame)
        else:
            print("Received unexpected message")
            
    def rcv_response_mqtt(self, client, userdata, message):
        print("Received response message")
        msg = message.payload
        print(msg)
        
        msg = str(msg.decode()).split(",")
        if msg and msg[0] == "response" and int(msg[2]) == self.request_num:
            if msg[3] == "accept":
                print("Starting battle with: " + msg[1])
                self.client.unsubscribe("ece180d/pokEEmon/" + self.user.username + "/response")
                self.opp_user = User()
                self.opp_user.username = msg[1]
                self.opp_user.team_df = pd.read_csv(io.StringIO(msg[4]), sep='\s+')
                b = Battle(self.user, self.request_num, self.opp_user, self.window, self.client)
                b.wait_screen(self.response_frame)
            else:
                print("Battle declined by: " + msg[1])
                self.client.unsubscribe("ece180d/pokEEmon/" + self.user.username + "/response")
                self.request_screen(self.response_frame)
        else:
            print("Received unexpected message")


    def home_screen(self, prev_frame = None):
        print("Home screen")
        if prev_frame:
            prev_frame.pack_forget()
            
        self.client.on_message = self.rcv_request_mqtt
        self.client.subscribe("ece180d/pokEEmon/" + self.user.username + "/request", qos=1)
        print("Subscribed to " + "ece180d/pokEEmon/" + self.user.username + "/request")

        if not self.window:
            self.window = tk.Tk()
        if not self.home_frame:
            self.home_frame = tk.Frame(self.window)       
            battle_button = tk.Button(self.home_frame, text = "Battle", command = partial(self.request_screen, self.home_frame))
            train_button = tk.Button(self.home_frame, text = "Train", command = self.train_screen)
            exit_button = tk.Button(self.home_frame, text = "Exit", command = self.exit_game)
            battle_button.pack()
            train_button.pack()
            exit_button.pack()

        self.home_frame.pack()

    def receive_screen(self, opp_username):
        print("Receive screen")
        self.home_frame.pack_forget()
        if self.receive_frame:
            self.receive_frame.destroy()

        self.client.unsubscribe("ece180d/pokEEmon/" + self.user.username + "/request")
        self.client.on_message = self.rcv_cancel_mqtt
        self.client.subscribe("ece180d/pokEEmon/" + self.user.username + "/cancel")
        print("Unsubscribed from " + "ece180d/pokEEmon/" + self.user.username + "/request")
        print("Subscribed to " + "ece180d/pokEEmon/" + self.user.username + "/cancel")

        
        self.receive_frame = tk.Frame(self.window)
        receive_label = tk.Label(self.receive_frame, text="Battle request from " + opp_username)
        accept_button = tk.Button(self.receive_frame, text = "Accept", command = partial(self.accept_request, opp_username))
        decline_button = tk.Button(self.receive_frame, text = "Decline", command = partial(self.decline_request, opp_username))
        receive_label.pack()
        accept_button.pack()
        decline_button.pack()

        self.receive_frame.pack()
        
    def request_screen(self, prev_screen = None):
        print("Request screen")

        if prev_screen:
            prev_screen.pack_forget()            
        if self.request_frame:
            self.request_frame.destroy()
                                                                            
        self.client.unsubscribe("ece180d/pokEEmon/" + self.user.username + "/request")
        self.client.unsubscribe("ece180d/pokEEmon/" + self.user.username + "/response")
        print("Unsubscribed from " + "ece180d/pokEEmon/" + self.user.username + "/request")
        print("Unsubscribed from " + "ece180d/pokEEmon/" + self.user.username + "/response")

        
        self.request_frame = tk.Frame(self.window)
        request_label = tk.Label(self.request_frame, text="Opponent username")
        username_entry = tk.Entry(self.request_frame)
        submit_button = tk.Button(self.request_frame, text = "Submit", command = partial(self.make_request, username_entry))
        back_button = tk.Button(self.request_frame, text = "Back", command = partial(self.home_screen, self.request_frame))
        request_label.pack()
        username_entry.pack()
        submit_button.pack()
        back_button.pack()

        self.request_frame.pack()


    def response_screen(self, opp_username):
        print("Response screen")
        self.request_frame.pack_forget()
        if self.response_frame:
            self.response_frame.destroy()


        self.client.on_message = self.rcv_response_mqtt
        self.client.subscribe("ece180d/pokEEmon/" + self.user.username + "/response")
        print("Subscribed to " + "ece180d/pokEEmon/" + self.user.username + "/response")
        
        self.response_frame = tk.Frame(self.window)
        request_label = tk.Label(self.response_frame, text="Waiting for " + opp_username)
        cancel_button = tk.Button(self.response_frame, text = "Cancel", command = partial(self.cancel_request, opp_username))
        request_label.pack()
        cancel_button.pack()

        self.response_frame.pack()
        
    def train_screen(self):
        pass

    def make_request(self, entry):
        opp_username = entry.get().strip()
        if opp_username and opp_username != self.user.username:
            self.request_num = random.randint(0,10000)
            request_msg = "request," + self.user.username + ",{},{}".format(self.request_num, self.user.team_df.to_string())
            print("Requesting game with: " +  opp_username + " request number {}".format(self.request_num))
            self.client.publish("ece180d/pokEEmon/" + opp_username + "/request", request_msg)
            self.response_screen(opp_username)
        else:
            print("Invalid username: " +  opp_username)

    def cancel_request(self, opp_username):
        cancel_msg = "cancel," + self.user.username + ",{}".format(self.request_num)
        print("Cancel request for: " +  opp_username + " request number {}".format(self.request_num))
        self.client.publish("ece180d/pokEEmon/" + opp_username + "/cancel", cancel_msg)
        self.request_screen(self.response_frame)
            
    def accept_request(self, opp_username):
        print("Accepted game with: " + opp_username)
        response_msg = "response," + self.user.username + ",{},accept,{}".format(self.request_num, self.user.team_df.to_string())
        self.client.publish("ece180d/pokEEmon/" + opp_username + "/response", response_msg)
        self.client.unsubscribe("ece180d/pokEEmon/" + self.user.username + "/cancel")
        print("Unsubscribed from " + "ece180d/pokEEmon/" + self.user.username + "/cancel")
        b = Battle(self.user, self.request_num, self.opp_user, self.window, self.client)
        b.move_screen(self.receive_frame)

    def decline_request(self, opp_username):
        print("Declined game with: " + opp_username)
        response_msg = "response," + self.user.username + ",{},decline".format(self.request_num)
        self.client.publish("ece180d/pokEEmon/" + opp_username + "/response", response_msg)
        print("Unsubscribed from " + "ece180d/pokEEmon/" + self.user.username + "/cancel")
        self.client.unsubscribe("ece180d/pokEEmon/" + self.user.username + "/cancel")
        self.home_screen(self.receive_frame)
    
    def start_game(self):
        print("Starting game")
        self.window.mainloop()

    def exit_game(self):
        print("Exiting game")
        self.user.gamestats_df.to_csv(self.user.path + "/gamestats.csv", index = False, quoting=csv.QUOTE_NONNUMERIC)
        self.user.team_df.to_csv(self.user.path + "/team.csv", index=False, quoting=csv.QUOTE_NONNUMERIC)
        self.window.destroy()
                      

game = Game(args.username)
game.connect_mqtt()
game.home_screen()
game.start_game()