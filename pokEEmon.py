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
        print("Received request message")
        msg = message.payload
        print(msg)

        msg = str(msg.decode()).split(",")
        print(msg)
        
        if msg and msg[0] == "request":
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
            self.client.unsubscribe("ece180d/pokEEmon/" + self.username + "/cancel")
            print("Unsubscribed from " + "ece180d/pokEEmon/" + self.username + "/cancel")
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
                self.client.unsubscribe("ece180d/pokEEmon/" + self.username + "/response")
                #TODO next step
                self.home_screen(self.response_frame)
            else:
                print("Battle declined by: " + msg[1])
                self.client.unsubscribe("ece180d/pokEEmon/" + self.username + "/response")
                self.request_screen(self.response_frame)
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

        self.client.unsubscribe("ece180d/pokEEmon/" + self.username + "/request")
        self.client.on_message = self.rcv_cancel_mqtt
        self.client.subscribe("ece180d/pokEEmon/" + self.username + "/cancel")
        print("Unsubscribed from " + "ece180d/pokEEmon/" + self.username + "/request")
        print("Subscribed to " + "ece180d/pokEEmon/" + self.username + "/cancel")

        
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
                                                                            
        self.client.unsubscribe("ece180d/pokEEmon/" + self.username + "/request")
        self.client.unsubscribe("ece180d/pokEEmon/" + self.username + "/response")
        print("Unsubscribed from " + "ece180d/pokEEmon/" + self.username + "/request")
        print("Unsubscribed from " + "ece180d/pokEEmon/" + self.username + "/response")

        
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
        self.client.subscribe("ece180d/pokEEmon/" + self.username + "/response")
        print("Subscribed to " + "ece180d/pokEEmon/" + self.username + "/response")
        
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
        if opp_username and opp_username != self.username:
            self.request_num = random.randint(0,10000)
            request_msg = "request," + self.username + ",{}".format(self.request_num)
            print("Requesting game with: " +  opp_username + " request number {}".format(self.request_num))
            self.client.publish("ece180d/pokEEmon/" + opp_username + "/request", request_msg)
            self.response_screen(opp_username)
        else:
            print("Invalid username: " +  opp_username)

    def cancel_request(self, opp_username):
        cancel_msg = "cancel," + self.username + ",{}".format(self.request_num)
        print("Cancel request for: " +  opp_username + " request number {}".format(self.request_num))
        self.client.publish("ece180d/pokEEmon/" + opp_username + "/cancel", cancel_msg)
        self.request_screen(self.response_frame)
            
    def accept_request(self, opp_username):
        print("Accepted game with: " + opp_username)
        response_msg = "response," + self.username + ",{},accept".format(self.request_num)
        self.client.publish("ece180d/pokEEmon/" + opp_username + "/response", response_msg)
        #TODO add next step
        self.client.unsubscribe("ece180d/pokEEmon/" + self.username + "/cancel")
        print("Unsubscribed from " + "ece180d/pokEEmon/" + self.username + "/cancel")
        self.home_screen(self.receive_frame)

    def decline_request(self, opp_username):
        print("Declined game with: " + opp_username)
        response_msg = "response," + self.username + ",{},decline".format(self.request_num)
        self.client.publish("ece180d/pokEEmon/" + opp_username + "/response", response_msg)
        print("Unsubscribed from " + "ece180d/pokEEmon/" + self.username + "/cancel")
        self.client.unsubscribe("ece180d/pokEEmon/" + self.username + "/cancel")
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
