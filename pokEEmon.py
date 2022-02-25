#!/usr/bin/python3

import paho.mqtt.client as mqtt
import argparse
import os
import csv
import pandas as pd
import tkinter as tk

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

    def home_screen(self):
        pass

game = Game(args.username)
game.connect_mqtt()
game.home_screen()
print("Here")

#is there a better thing to do here besides just looping?
while 1:
    continue
