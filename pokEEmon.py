#!/usr/bin/python

import paho.mqtt.client as mqtt
import argparse
import os
import csv
import pandas as pd
import tkinter as tk
from functools import partial

################################# SETUP ########################################################################
##### Command line interface to pass in name #####
parser = argparse.ArgumentParser(
    description="Start the game by typing ./pokEEmon.py <username>"
)

parser.add_argument("username", type=str, help="your in-game username")
args = parser.parse_args()
print("Welcome " + args.username)

class Game:
    def __init__(self, username):
        self.username = username
        self.window = None
        self.home_frame = None
        self.request_frame = None
        self.client = None

    def connect_mqtt(self):
        print("Connecting to MQTT")
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect_mqtt
        self.client.connect("test.mosquitto.org")
        self.client.on_message = self.rcv_request_mqtt
        self.client.subscribe("ece180d/pokEEmon/" + self.username + "/request", qos=1)
        print("Subscribed to " + "ece180d/pokEEmon/" + self.username + "/request")
        self.client.loop_start()

    def on_connect_mqtt(self, client, userdata, flags, rc):
        print("Connection returned result: " + str(rc))

    def rcv_request_mqtt(self, client, userdata, message):
        print(message.payload)

    def home_screen(self, prev_frame = None):
        print("Home screen")
        if prev_frame:
            prev_frame.pack_forget()
            
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

    def request_screen(self):
        print("Request screen")
        self.home_frame.pack_forget()
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


    def train_screen(self):
        pass

    def make_request(self, entry):
        opp_username = entry.get().strip()
        if opp_username:
            print("Requesting game with: " +  opp_username)
        else:
            print("Invalid username: " +  opp_username)
        
    
    def start_game(self):
        print("Starting game")
        self.window.mainloop()

    def exit_game(self):
        print("Exiting game")
        self.window.destroy()
        
        
        

game = Game(args.username)
game.connect_mqtt()
game.home_screen()
game.start_game()
