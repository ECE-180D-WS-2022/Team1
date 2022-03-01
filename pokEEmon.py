#!/usr/bin/python

import paho.mqtt.client as mqtt
import argparse
import os
import csv
import time
import pandas as pd
import tkinter as tk
from functools import partial
import random

################################# SETUP ########################################################################
##### Command line interface to pass in name #####
parser = argparse.ArgumentParser(
    description="Start the game by typing ./pokEEmon.py <username>"
)

parser.add_argument("username", type=str, help="your in-game username")
args = parser.parse_args()
print("Welcome " + args.username)
class User:
    def __init__(self, username):
        self.username = username
        self.path = "data/users/" + self.username
        self.gamestats_df, self.team_df = self.get_user_files()      
    
    def get_user_files(self):
        """
        get the appropiate gamestats and team files if it exists, else create the folder and copy in the default
        """
        if os.path.isdir(self.path):
            game_stats_df = pd.read_csv(self.path + "/gamestats.csv")
            team_df = pd.read_csv(self.path + "/team.csv")
        else:
            os.mkdir(self.path, 0o777)
            game_stats_df = pd.read_csv("data/users/default/gamestats.csv")
            team_df = pd.read_csv("data/users/default/team.csv")
        return game_stats_df, team_df

class Game:
    def __init__(self, username):
        self.username = username
        self.user = User(username)
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
        print(message.payload)

    def rcv_response_mqtt(self, client, userdata, message):
        msg = message.payload
        print(msg)
        
        msg = msg.split(",")
        if msg and msg[0] == "response" and int(msg[2]) == self.request_num:
            print(msg)
            print("Starting game with: " + msg[1])
        else:
            print("Received unexpected message")

    def home_screen(self, prev_frame = None):
        print("Home screen")
        if prev_frame:
            prev_frame.pack_forget()
            
        self.client.on_message = self.rcv_request_mqtt
        self.client.subscribe("ece180d/pokEEmon/" + self.username + "/request", qos=1)
        print("Subscribed to " + "ece180d/pokEEmon/" + self.username + "/request")

        if not self.window:
            self.window = tk.Tk()
        if not self.home_frame:
            self.home_frame = tk.Frame(self.window)       
            battle_button = tk.Button(self.home_frame, text = "Battle", command = self.request_screen)
            train_button = tk.Button(self.home_frame, text = "Train", command = self.train_screen)
            exit_button = tk.Button(self.home_frame, text = "Exit", command = self.exit_game)
            battle_button.pack()
            train_button.pack()
            exit_button.pack()

        self.home_frame.pack()

    def receive_screen(self, opp_username):
        print("Receive screen")
        self.home_screen.pack_forget()
        if self.receive_frame:
            self.receive_frame.destroy()

        self.client.unsubscribe("ece180d/pokEEmon/" + self.username + "/request")

        self.receive_frame = tk.Frame(self.window)
        receive_label = tk.Label(self.receive_frame, text="Battle request from " + opp_username)
        accept_button = tk.Button(self.receive_frame, text = "Accept", command = self.exit_game)
        decline_button = tk.Button(self.receive_frame, text = "Decline", command = partial(self.home_screen, self.receive_frame)
        

    def request_screen(self, prev_screen = None):
        print("Request screen")

        if prev_screen:
            prev_screen.pack_forget()

        self.client.unsubscribe("ece180d/pokEEmon/" + self.username + "/request")
        
        if not self.request_frame:
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


    def response_screen(self, username):
        print("Response screen")
        self.request_frame.pack_forget()
        if self.response_frame:
            self.response_frame.destroy()


        self.client.on_message = self.rcv_response_mqtt
        self.client.subscribe("ece180d/pokEEmon/" + self.username + "/response")

        
        self.response_frame = tk.Frame(self.window)
        request_label = tk.Label(self.request_frame, text="Waiting for " + username)
        cancel_button = tk.Button(self.request_frame, text = "Cancel", command = partial(self.home_screen, partial(self.request_screen, self.response_frame))
        request_label.pack()
        cancel_button.pack()

        self.response_frame.pack()
        
    def train_screen(self):
        pass

    def make_request(self, entry):
        opp_username = entry.get().strip()
        self.request_num = random.randint()
        request_msg = "request," + self.username + ",{}".replace(self.request_num)
        if opp_username:
            print("Requesting game with: " +  opp_username)
            self.client.publish("ece180d/pokEEmon/" + opp_username + "/request", request_msg)
        else:
            print("Invalid username: " +  opp_username)
        
    
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
