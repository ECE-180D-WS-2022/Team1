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
import speech_recognition as sr
import cv2
from PIL import Image, ImageTk
import mediapipe as mp
import matplotlib.pyplot as plt
import pose as ps
import random
import winsound
import math
from level_up import import_learnset
import pronouncing
#import moves_new as mv

movegesture = {"Thunderbolt" : "slash", "Tackle" : "block", "Water-gun" : "whip", "Flamethrower" : "scratch"}
learnset = import_learnset()

def learn_moves(pk_df, lvl):

    ans = pk_df.copy()

    #if level learnset is not empty
    if not learnset[ans.loc["id"] - 1][lvl] :
        #find name of move to be learned
        move_learned = pd.read_csv("data/moves.csv")
        move_learned = move_learned.loc[learnset[ans.loc["id"] - 1][lvl][0] == moves["id"]]

        #check if there are empty move slots
        if pd.isnull(ans.loc["move2"]):
            ans.at["move2"] = move_learned.at["identifier"]
            return ans

        if pd.isnull(ans.loc["move3"]):
            ans.at["move3"] = move_learned.at["identifier"]
            return ans

        if pd.isnull(ans.loc["move4"]):
            ans.at["move4"] = move_learned.at["identifier"]
            return ans

        #if no empty move slots, just randomly replace one
        index = randrange(4) + 10
        ans.iat[index] = move_learned.at["identifier"]

    return ans

def level_up (pk_df, xp_amt):
    #1000 xp to level up
    current_xp =  pk_df["xp_accumulated"]
    current_xp += xp_amt
    ans = pk_df.copy()
    ans["xp_accumulated"] = current_xp

    if int(current_xp) // 1000 >= int(pk_df["level"]):
        # level up
        # get base stats
        basepk_df = pd.read_csv("data/pokemon.csv")
        basepk_df = basepk_df.loc[basepk_df["name"] == pk_df["name"]]
        # use base stats to calculate new level
        lvl = int(current_xp) // 1000 + 1
        ans["level"] = lvl
        ans["hp"] = int(((((2*int(basepk_df["hp"])) + random.randrange(28,31) + 20.25) * lvl)/100) + lvl + 10)
        ans["attack"] = int(((((2*basepk_df["attack"]) + random.randrange(28,31) + 20.25) * lvl)/100) + 5)
        ans["defense"] = int(((((2*basepk_df["defense"]) + random.randrange(28,31) + 20.25) * lvl)/100) + 5)
        ans["special_attack"] = int(((((2*basepk_df["special_attack"]) + random.randrange(28,31) + 20.25) * lvl)/100) + 5)
        ans["special_defense"] = int(((((2*basepk_df["special_defense"]) + random.randrange(28,31) + 20.25) * lvl)/100) + 5)
        ans["speed"] = int(((((2*basepk_df["speed"]) + random.randrange(28,31) + 20.25) * lvl)/100) + 5)

        #ans = learn_moves(ans, lvl)

    return ans

class Battle:
    def __init__(self, user, battle_id, opp_user, window, client, home, id, singleplayer = False):
        self.user = user
        self.user.team_df["curr_hp"] = self.user.team_df["hp"]
        self.battle_id = battle_id
        self.opp_user = opp_user
        self.opp_user.team_df["curr_hp"] = self.opp_user.team_df["hp"]
        self.window = window
        self.client = client
        self.home = home
        self.curr_pokemon = 0
        self.opp_pokemon = 0
        self.wait_frame = None
        self.move_frame = None
        self.gesture_frame = None
        self.choose_frame = None
        self.mic = None
        self.rec = None
        self.stop_listening = None
        self.id = id
        self.movename = None
        self.moves_df = pd.read_csv("data/moves.csv")
        self.singleplayer = singleplayer
        self.gameover = False

    def rcv_gesture_mqtt(self, client, userdata, message):
        print("Received move message")
        msg = message.payload
        print(msg)

        msg = str(msg.decode())

        if msg == movegesture[self.movename]:
            print("Got correct gesture")
            self.do_move()
        else:
            print("Incorrect gestures")

    def rcv_battle_mqtt(self, client, userdata, message):
        print("Received move or cancel message")
        msg = message.payload
        print(msg)

        msg = str(msg.decode()).split(",")
        print(msg)

        if msg and msg[0] == "move" and int(msg[2]) == self.battle_id:
            winsound.PlaySound('whoosh.wav', winsound.SND_FILENAME | winsound.SND_ASYNC)
            movename = msg[3]
            pokeemon_name = self.opp_user.team_df.iloc[self.opp_pokemon, self.opp_user.team_df.columns.get_loc("name")]
            damage = self.calc_damage(movename, int(msg[4]), self.opp_user.team_df.iloc[self.opp_pokemon], self.user.team_df.iloc[self.curr_pokemon])
            curr_hp = self.user.team_df.iloc[self.curr_pokemon, self.user.team_df.columns.get_loc("curr_hp")]
            curr_hp -= damage
            if curr_hp < 0:
                curr_hp = 0
            self.user.team_df.iloc[self.curr_pokemon, self.user.team_df.columns.get_loc("curr_hp")] = curr_hp
            if self.user.team_df[self.user.team_df["curr_hp"] > 0].empty:
                print("You lost")
                self.user.gamestats_df["games_played"] += 1
                self.user.gamestats_df.to_csv(self.user.path + "/gamestats.csv", index=False, quoting=csv.QUOTE_NONNUMERIC)
                self.gameover_screen(False, self.wait_frame)
            else:
                self.move_screen(self.wait_frame, "{}'s {} played {}".format(self.opp_user.username.capitalize(), pokeemon_name, movename))
        elif msg and msg[0] == "change" and int(msg[2]) == self.battle_id:
            self.opp_pokemon = int(msg[3])
            self.wait_screen(self.wait_frame, "{} changed their pokEEmon to {}".format(self.opp_user.username, self.opp_user.team_df.iloc[self.opp_pokemon, self.opp_user.team_df.columns.get_loc("name")]))
        elif msg and msg[0] == "quit" and int(msg[2]) == self.battle_id:
            print("You won")
            self.user.gamestats_df["games_played"] += 1
            self.user.gamestats_df["wins"] += 1
            self.user.gamestats_df.to_csv(self.user.path + "/gamestats.csv", index=False, quoting=csv.QUOTE_NONNUMERIC)
            self.gameover_screen(True, self.wait_frame)
        else:
            print("Received unexpected message")

    def edit_distance(self, list1, list2):
        len1 = len(list1)
        len2 = len(list2)

        DP = [[0 for i in range(len1 + 1)]
                 for j in range(2)];

        for i in range(0, len1 + 1):
            DP[0][i] = i

        for i in range(1, len2 + 1):
            for j in range(0, len1 + 1):
                if (j == 0):
                    DP[i % 2][j] = i
                elif(list1[j - 1] == list2[i-1]):
                    DP[i % 2][j] = DP[(i - 1) % 2][j - 1]
                else:
                    DP[i % 2][j] = (1 + min(DP[(i - 1) % 2][j],
                                        min(DP[i % 2][j - 1],
                                        DP[(i - 1) % 2][j - 1])))

        return DP[len2 % 2][len1]

    def voice_callback(self, recognizer, audio):
        try:
            words = recognizer.recognize_google(audio).lower()
            print("Heard: " + words)
            for move in ["move1", "move2", "move3", "move4"]:
                movename = self.user.team_df.iloc[self.curr_pokemon][move].lower()
                if movename.replace("-", " ") in words or movename.replace("-", "") in words:
                    self.gesture_screen(move)
                    return

                movename =  movename.replace("-", "")
                rhymes = pronouncing.rhymes(movename)
                for rhyme in rhymes:
                    if rhyme in words:
                        self.gesture_screen(move)
                        return

                # for word in words.split(" "):
                #     wordp = pronouncing.phones_for_word(word)
                #     movep = pronouncing.phones_for_word(movename)

                #     if wordp == [] or movep == []:
                #         continue

                #     if self.edit_distance(wordp, movep) < 2:
                #         self.gesture_screen(move)
                #         return

            print("Not a move")
        except sr.UnknownValueError:
            print("Google Speech Recognition could not understand audio")
        except sr.RequestError as e:
            print("Could not request results from Google Speech Recognition service; {0}".format(e))

    def sel_pokemon(self, index):
        self.curr_pokemon = index
        if not self.singleplayer:
            choose_msg = "change,{},{},{}".format(self.user.username, self.battle_id, index)
            self.client.publish("ece180d/pokEEmon/" + self.opp_user.username + "/change", choose_msg)
        self.move_screen(self.choose_frame)

    def quit(self, prev_frame = None):
        if self.stop_listening is not None:
            self.stop_listening(wait_for_stop=False)
            self.stop_listening = None

        self.gameover = True
        self.user.gamestats_df["games_played"] += 1
        self.user.gamestats_df.to_csv(self.user.path + "/gamestats.csv", index=False, quoting=csv.QUOTE_NONNUMERIC)

        if not self.singleplayer:
            quit_msg = "quit,{},{}".format(self.user.username, self.battle_id)
            self.client.publish("ece180d/pokEEmon/" + self.opp_user.username + "/quit", move_msg)

        self.gameover_screen(False,  prev_frame)

    def do_move(self):
        winsound.PlaySound('whoosh.wav', winsound.SND_FILENAME | winsound.SND_ASYNC)
        random_mult = random.randrange(85,100)
        damage = self.calc_damage(self.movename, random_mult, self.user.team_df.iloc[self.curr_pokemon], self.opp_user.team_df.iloc[self.opp_pokemon])
        opp_curr_hp = self.opp_user.team_df.iloc[self.opp_pokemon, self.opp_user.team_df.columns.get_loc("curr_hp")]
        opp_curr_hp -= damage
        if opp_curr_hp < 0:
            opp_curr_hp = 0
        self.opp_user.team_df.iloc[self.opp_pokemon, self.opp_user.team_df.columns.get_loc("curr_hp")] = opp_curr_hp

        if not self.singleplayer:
            move_msg = "move,{},{},{},{}".format(self.user.username, self.battle_id, self.movename, random_mult)
            self.client.publish("ece180d/pokEEmon/" + self.opp_user.username + "/move", move_msg)

        if self.opp_user.team_df[self.opp_user.team_df["curr_hp"] > 0].empty:
            print("You won!")

            xp_reward = sum(self.opp_user.team_df["xp_reward"].values)
            self.user.team_df.drop('curr_hp', axis=1, inplace=True)

            for i in range(self.user.team_df.shape[0]):
                self.user.team_df.loc[i] = level_up(self.user.team_df.loc[i], xp_reward)

            print("Writing updated team to {}".format(self.user.path + "/team.csv"))
            print(self.user.team_df)

            self.user.team_df.to_csv(self.user.path + "/team.csv", index=False, quoting=csv.QUOTE_NONNUMERIC)

            self.user.gamestats_df["games_played"] += 1
            self.user.gamestats_df["wins"] += 1
            self.user.gamestats_df.to_csv(self.user.path + "/gamestats.csv", index=False, quoting=csv.QUOTE_NONNUMERIC)

            self.gameover_screen(True, self.gesture_frame)
        else:
            self.wait_screen(self.gesture_frame, "Your {} played {}".format(self.user.team_df.iloc[self.curr_pokemon, self.user.team_df.columns.get_loc("name")], self.movename))

    def calc_damage(self, movename, random_mult, attack_pk, receive_pk):
        random_mult = float(random_mult) * 0.01  #random multiplier from 0.85 to 1
        multiplier = self.find_effectiveness(attack_pk["type"], receive_pk["type"])
        special = int(self.moves_df.loc[self.moves_df["identifier"] == movename.lower()]["damage_class_id"])
        if (attack_pk["type"] == receive_pk["type"]): #implement same type attack bonus
            stab = 1.5
        else:
            stab = 1
        pwr =  float(self.moves_df.loc[self.moves_df["identifier"] == movename.lower()]["power"])

        #special attack calc
        if (special == 2):
            damage = ((((((2*attack_pk["level"])/5)+2)*pwr*(attack_pk["special_attack"]/receive_pk["special_defense"]))/50)+2)*stab*multiplier*random_mult
        #physical attack calc
        else:
            damage = ((((((2*attack_pk["level"])/5)+2)*pwr*(attack_pk["attack"]/receive_pk["defense"]))/50)+2)*stab*multiplier*random_mult

        return int(math.floor(damage))

    def find_effectiveness(self, attack_type, receive_type):
        effectiveness_array = [[1,   1,   1,   1,   1,   1,   1,   1,   1,   1,   1,   1,   0.5, 0,   1,   1,   0.5, 1],
                               [1,   0.5, 0.5, 1,   2,   2,   1,   1,   1,   1,   1,   2,   0.5, 1,   0.5, 1,   2,   1],
                               [1,   2,   0.5, 1,   0.5, 1,   1,   1,   2,   1,   1,   1,   2,   1,   0.5, 1,   1,   1],
                               [1,   1,   2,   0.5, 0.5, 1,   1,   1,   0,   2,   1,   1,   1,   1,   0.5, 1,   1,   1],
                               [1,   0.5, 2,   1,   0.5, 1,   1,   0.5, 2,   0.5, 1,   0.5, 2,   1,   0.5, 1,   0.5, 1],
                               [1,   0.5, 0.5, 1,   2,   0.5, 1,   1,   2,   2,   1,   1,   1,   1,   2,   1,   0.5, 1],
                               [2,   1,   1,   1,   1,   2,   1,   0.5, 1,   0.5, 0.5, 0.5, 2,   0,   1,   2,   2,   0.5],
                               [1,   1,   1,   1,   2,   1,   1,   0.5, 0.5, 1,   1,   1,   0.5, 0.5, 1,   1,   0,   2],
                               [1,   2,   1,   2,   0.5, 1,   1,   2,   1,   0,   1,   0.5, 2,   1,   1,   1,   2,   1],
                               [1,   1,   1,   0.5, 2,   1,   2,   1,   1,   1,   1,   2,   0.5, 1,   1,   1,   0.5, 1],
                               [1,   1,   1,   1,   1,   1,   2,   2,   1,   1,   0.5, 1,   1,   1,   1,   0,   0.5, 1],
                               [1,   0.5, 1,   1,   2,   1,   0.5, 0.5, 1,   0.5, 2,   1,   1,   0.5, 1,   2,   0.5, 0.5],
                               [1,   2,   1,   1,   1,   2,   0.5, 1,   0.5, 2,   1,   2,   1,   1,   1,   1,   0.5, 1],
                               [0,   1,   1,   1,   1,   1,   1,   1,   1,   1,   2,   1,   1,   2,   1,   0.5, 1,   1],
                               [1,   1,   1,   1,   1,   1,   1,   1,   1,   1,   1,   1,   1,   1,   2,   1,   0.5, 0],
                               [1,   1,   1,   1,   1,   1,   0.5, 1,   1,   1,   2,   1,   1,   2,   1,   0.5, 1,   0.5],
                               [1,   0.5, 0.5, 0.5, 1,   2,   1,   1,   1,   1,   1,   1,   2,   1,   1,   1,   0.5, 2],
                               [1,   0.5, 1,   1,   1,   1,   2,   0.5, 1,   1,   1,   1,   1,   1,   2,   2,   0.5, 1], ]
        typeList = ["Normal", "Fire", "Water", "Electric", "Grass", "Ice", "Fighting", "Poison", "Ground", "Flying", "Psychic", "Bug", "Rock", "Ghost", "Dragon", "Dark", "Steel", "Fairy",]

        multiplier = effectiveness_array[typeList.index(attack_type)][typeList.index(receive_type)]
        return multiplier

    def gesture_screen(self, move):
        print("Waiting for gesture")
        winsound.PlaySound('click.wav', winsound.SND_FILENAME | winsound.SND_ASYNC)
        if self.move_frame:
            self.move_frame.pack_forget()
        if self.gesture_frame:
            self.gesture_frame.destroy()

        if self.stop_listening is not None:
            self.stop_listening(wait_for_stop=False)
            self.stop_listening = None

        self.movename = self.user.team_df.iloc[self.curr_pokemon][move]

        self.client.on_message = self.rcv_gesture_mqtt
        self.client.subscribe("ece180d/pokEEmon/" + self.id, qos=1)
        print("Subscribed to " + "ece180d/pokEEmon/" + self.id)

        self.gesture_frame = tk.Frame(self.window, bg = "#34cfeb")
        gesture_label = tk.Label(self.gesture_frame, text="Do a {} ".format(movegesture[self.movename]), font=("Arial", 25), bg= "#34cfeb")
        back_button = tk.Button(self.gesture_frame, text="Back", command = partial(self.move_screen, self.gesture_frame), height = 4, width = 20, bg = "#ffcc03")
        gesture_label.pack()
        back_button.pack(pady = 10)

        self.gesture_frame.pack()


        # TODO: remove this when using gestures
        self.window.after(1000, self.do_move)

    def wait_screen(self, prev_frame = None, move_update = None):
        '''
        Creating screen that handles waiting for opponent to make a move
        '''
        print("Waiting for opponent move")
        if prev_frame:
            prev_frame.pack_forget()
        if self.wait_frame:
            self.wait_frame.destroy()


        self.client.unsubscribe("ece180d/pokEEmon/" + self.id)
        print("Unsubscribed to " + "ece180d/pokEEmon/" + self.id)

        if not self.singleplayer:
            self.client.on_message = self.rcv_battle_mqtt
            self.client.subscribe("ece180d/pokEEmon/" + self.user.username + "/move", qos=1)
            self.client.subscribe("ece180d/pokEEmon/" + self.user.username + "/change", qos=1)
            self.client.subscribe("ece180d/pokEEmon/" + self.user.username + "/quit", qos = 1)
            print("Subscribed to " + "ece180d/pokEEmon/" + self.user.username + "/move")
            print("Subscribed to " + "ece180d/pokEEmon/" + self.user.username + "/change")
            print("Subscribed to " + "ece180d/pokEEmon/" + self.user.username + "/quit")

        self.wait_frame = tk.Frame(self.window, bg = "#34cfeb")

        if move_update is not None:
            update_label = tk.Label(self.wait_frame, text=move_update, bg = "#34cfeb", font=("Arial", 30))
            update_label.pack()
        else:
            winsound.PlaySound('click.wav', winsound.SND_FILENAME | winsound.SND_ASYNC)

        wait_img =  ImageTk.PhotoImage(Image.open("wait_opponent_move_img.png"))
        wait_label = tk.Label(self.wait_frame, image=wait_img, bg = "#34cfeb")
        wait_label.photo = wait_img
        quit_button = tk.Button(self.wait_frame, text="Quit", command = partial(self.quit, self.wait_frame), height = 4, width = 50, bg="#ffcc03")
        user_pokemon_name = self.user.team_df.iloc[self.curr_pokemon, self.user.team_df.columns.get_loc("name")]
        userteam_string = self.user.team_df.loc[:, ["name", "curr_hp"]].to_string(index=False)
        userteam_string = userteam_string.replace(user_pokemon_name, "**" + user_pokemon_name)
        userteam_label = tk.Label(self.wait_frame, text="\nYour team: \n{}\n".format(userteam_string), bg = "#34cfeb", font=("Arial", 30))
        opp_pokemon_name = self.opp_user.team_df.iloc[self.opp_pokemon, self.opp_user.team_df.columns.get_loc("name")]
        oppteam_string = self.opp_user.team_df.loc[:, ["name", "curr_hp"]].to_string(index=False)
        oppteam_string = oppteam_string.replace(opp_pokemon_name, "**" + opp_pokemon_name)
        oppteam_label = tk.Label(self.wait_frame, text="\nOpponent team: \n{}\n".format(oppteam_string), bg = "#34cfeb", font=("Arial", 30))
        wait_label.pack(pady = 5)
        quit_button.pack(pady = 30)
        userteam_label.pack()
        oppteam_label.pack()
        self.wait_frame.pack()

        if self.singleplayer:
            self.window.after(3000, lambda : self.bot_move(self.wait_frame))

    def gameover_screen(self, won, prev_frame = None):
        if self.stop_listening is not None:
            self.stop_listening(wait_for_stop=False)
            self.stop_listening = None

        if prev_frame:
            prev_frame.pack_forget()

        gameover_frame = tk.Frame(self.window, bg = "#34cfeb")
        if won:
            won_img = ImageTk.PhotoImage(Image.open("won_img.png"))
            gameover_label = tk.Label(gameover_frame, image=won_img, bg = "#34cfeb")
            gameover_label.photo = won_img
        else:
            lost_img = ImageTk.PhotoImage(Image.open("lost_img.png"))
            gameover_label = tk.Label(gameover_frame, image=lost_img, bg = "#34cfeb")
            gameover_label.photo = lost_img

        home_button = tk.Button(gameover_frame, text="Home", command = partial(self.home, gameover_frame), height = 6, width = 70, bg="#ffcc03")

        gameover_label.pack(pady = 5)
        home_button.pack(pady = 5)
        gameover_frame.pack()

    def bot_move(self, prev_frame = None):
        if self.gameover:
            return

        winsound.PlaySound('whoosh.wav', winsound.SND_FILENAME | winsound.SND_ASYNC)
        if prev_frame:
            prev_frame.pack_forget()

        # bot will choose the move with the best damage
        random_mult = random.randrange(85,100)
        best_damage = -1
        best_pk = None
        best_move = None
        for i in range(self.opp_user.team_df.shape[0]):
            pk = self.opp_user.team_df.loc[i]
            if pk["curr_hp"] <= 0:
                continue
            for move in ["move1", "move2", "move3", "move4"]:
                movename = pk[move]
                damage = self.calc_damage(movename, random_mult, pk, self.user.team_df.iloc[self.curr_pokemon])
                if damage > best_damage:
                    best_damage = damage
                    best_pk = i
                    best_move = movename

        self.opp_pokemon = best_pk
        pokeemon_name = self.opp_user.team_df.iloc[self.opp_pokemon, self.opp_user.team_df.columns.get_loc("name")]
        curr_hp = self.user.team_df.iloc[self.curr_pokemon, self.user.team_df.columns.get_loc("curr_hp")]
        curr_hp -= best_damage
        if curr_hp < 0:
            curr_hp = 0
        self.user.team_df.iloc[self.curr_pokemon, self.user.team_df.columns.get_loc("curr_hp")] = curr_hp
        if self.user.team_df[self.user.team_df["curr_hp"] > 0].empty:
            print("You lost")
            self.user.gamestats_df["games_played"] += 1
            self.user.gamestats_df.to_csv(self.user.path + "/gamestats.csv", index=False, quoting=csv.QUOTE_NONNUMERIC)
            self.gameover_screen(False)
        else:
            self.move_screen(move_update = "{}'s {} played {}".format(self.opp_user.username.capitalize(), pokeemon_name, best_move))


    def move_screen(self, prev_frame = None, move_update = None):
        print("Choose your move")

        if prev_frame:
            prev_frame.pack_forget()
        if self.move_frame:
            self.move_frame.destroy()


        self.client.unsubscribe("ece180d/pokEEmon/" + self.id)
        print("Unsubscribed to " + "ece180d/pokEEmon/" + self.id)

        if not self.singleplayer:
            self.client.unsubscribe("ece180d/pokEEmon/" + self.user.username + "/move")
            self.client.unsubscribe("ece180d/pokEEmon/" + self.user.username + "/change")
            self.client.subscribe("ece180d/pokEEmon/" + self.user.username + "/quit", qos = 1)
            print("Unsubscribed to " + "ece180d/pokEEmon/" + self.user.username + "/move")
            print("Unsubscribed to " + "ece180d/pokEEmon/" + self.user.username + "/change")
            print("Subscribed to " + "ece180d/pokEEmon/" + self.user.username + "/quit")

        self.move_frame = tk.Frame(self.window, bg = "#34cfeb")

        if move_update:
            update_label = tk.Label(self.move_frame, text=move_update, bg = "#34cfeb", font=("Arial", 30))
            update_label.pack()
            winsound.PlaySound('whoosh.wav', winsound.SND_FILENAME | winsound.SND_ASYNC)
        else:
            winsound.PlaySound('click.wav', winsound.SND_FILENAME | winsound.SND_ASYNC)

        if self.user.team_df.iloc[self.curr_pokemon, self.user.team_df.columns.get_loc("curr_hp")] > 0:
            img = ImageTk.PhotoImage(Image.open("choose_move_img.png"))
            move_label = tk.Label(self.move_frame, image = img, bg = "#34cfeb")
            move_label.photo = img
            move1_button = tk.Button(self.move_frame, text=self.user.team_df.iloc[self.curr_pokemon]["move1"], command = partial(self.gesture_screen, "move1"), height = 4, width = 50, bg="#ffcc03")
            move2_button = tk.Button(self.move_frame, text=self.user.team_df.iloc[self.curr_pokemon]["move2"], command = partial(self.gesture_screen, "move2"), height = 4, width = 50, bg="#ffcc03")
            move3_button = tk.Button(self.move_frame, text=self.user.team_df.iloc[self.curr_pokemon]["move3"], command = partial(self.gesture_screen, "move3"), height = 4, width = 50, bg="#ffcc03")
            move4_button = tk.Button(self.move_frame, text=self.user.team_df.iloc[self.curr_pokemon]["move4"], command = partial(self.gesture_screen, "move4"), height = 4, width = 50, bg="#ffcc03")
            move_label.pack()
            move1_button.pack(pady=10)
            move2_button.pack(pady=10)
            move3_button.pack(pady=10)
            move4_button.pack(pady=5)

            if self.mic is None:
                print("Setting up mic and receiver for speech recognition")
                self.mic = sr.Microphone()
                self.rec = sr.Recognizer()
                with self.mic as source:
                    self.rec.adjust_for_ambient_noise(source)

            self.stop_listening = self.rec.listen_in_background(self.mic, self.voice_callback, 2)
        else:
            img_2 = ImageTk.PhotoImage(Image.open("change_pokemon.png"))
            change_label = tk.Label(self.move_frame, image = img_2, bg = "#34cfeb")
            change_label.photo = img_2
            change_label.pack()

        user_pokemon_name = self.user.team_df.iloc[self.curr_pokemon, self.user.team_df.columns.get_loc("name")]
        userteam_string = self.user.team_df.loc[:, ["name", "curr_hp"]].to_string(index=False)
        userteam_string = userteam_string.replace(user_pokemon_name, "**" + user_pokemon_name)
        userteam_label = tk.Label(self.move_frame, text="\nYour team: \n{}\n".format(userteam_string), bg = "#34cfeb", font=("Arial", 30), anchor="n")
        opp_pokemon_name = self.opp_user.team_df.iloc[self.opp_pokemon, self.opp_user.team_df.columns.get_loc("name")]
        oppteam_string = self.opp_user.team_df.loc[:, ["name", "curr_hp"]].to_string(index=False)
        oppteam_string = oppteam_string.replace(opp_pokemon_name, "**" + opp_pokemon_name)
        oppteam_label = tk.Label(self.move_frame, text="\nOpponent team: \n{}\n".format(oppteam_string), bg = "#34cfeb", font=("Arial", 30), anchor="n")
        change_button = tk.Button(self.move_frame, text="Change pokEEmon", command = self.choose_screen, height = 4, width = 50, bg="#ffcc03")
        change_button.pack(pady = 30)
        quit_button = tk.Button(self.move_frame, text="Quit", command = partial(self.quit, self.move_frame), height = 4, width = 50, bg="#ffcc03")
        quit_button.pack(pady = 30)
        userteam_label.pack(side=tk.LEFT, padx = 10)
        oppteam_label.pack(side=tk.LEFT, padx = 10)


        self.move_frame.pack()


    def choose_screen(self, prev_frame = None):
        winsound.PlaySound('click.wav', winsound.SND_FILENAME | winsound.SND_ASYNC)
        if self.move_frame:
            self.move_frame.pack_forget()
        if self.choose_frame:
            self.choose_frame.destroy()
        if self.stop_listening is not None:
            self.stop_listening(wait_for_stop=False)
            self.stop_listening = None

        self.choose_frame = tk.Frame(self.window, bg = "#34cfeb")
        img = ImageTk.PhotoImage(Image.open("choose_pokemon_img.png"))
        choose_label = tk.Label(self.choose_frame, image = img, bg = "#34cfeb")
        choose_label.photo = img
        choose_label.pack()
        user_pokemon = self.user.team_df.loc[:,["name","curr_hp"]]
        for row in user_pokemon.itertuples():
            if row.curr_hp > 0:
                pokemon_button = tk.Button(self.choose_frame, text=row.name, command = partial(self.sel_pokemon, row.Index), height=6, width=40, bg = "#ffcc03")
                pokemon_button.pack(pady=10)
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
            basepk_df = pd.read_csv("data/pokemon.csv")
            team_df = basepk_df.sample(n = 3)
            team_df.reset_index(drop=True, inplace=True)
            for i in range(team_df.shape[0]):
                team_df.loc[i] = level_up(team_df.loc[i], 0)
            team_df.to_csv(self.path + "/team.csv", index=False, quoting=csv.QUOTE_NONNUMERIC)
            gamestats_df = pd.read_csv(self.path + "/gamestats.csv")
        else:
            gamestats_df = pd.read_csv(self.path + "/gamestats.csv")
            team_df = pd.read_csv(self.path + "/team.csv")
        return gamestats_df, team_df

class Game:
    def __init__(self, username, id):
        self.user = User(username)
        self.opp_user = None
        self.window = None
        self.home_frame = None
        self.choose_opp_frame = None
        self.receive_frame = None
        self.request_frame = None
        self.response_frame = None
        self.train_frame_begin = None
        self.train_frame = None
        self.working_pokemon = None
        self.desired_pose = None
        self.client = None
        self.connected = False
        self.request_num = None
        self.id = id
        self.battle = None


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
                self.battle = Battle(self.user, self.request_num, self.opp_user, self.window, self.client, self.home_screen, self.id)
                self.battle.wait_screen(self.response_frame)
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

        if self.battle is not None:
            del self.battle
            self.battle = None

        self.client.on_message = self.rcv_request_mqtt
        self.client.unsubscribe("ece180d/pokEEmon/" + self.id)
        self.client.subscribe("ece180d/pokEEmon/" + self.user.username + "/request", qos=1)
        print("Subscribed to " + "ece180d/pokEEmon/" + self.user.username + "/request")
        print("Unsubscribed to " + "ece180d/pokEEmon/" + self.id)

        if not self.window:
            self.window = tk.Tk()
            self.window.configure(bg="#34cfeb")
            self.window.attributes('-fullscreen',True)
        else:
            winsound.PlaySound('click.wav', winsound.SND_FILENAME | winsound.SND_ASYNC)
        if not self.home_frame:
            self.home_frame = tk.Frame(self.window, bg = "#34cfeb")
            img = ImageTk.PhotoImage(Image.open("logo.png"))

            photo_label = tk.Label(self.home_frame, image = img, bg = "#34cfeb")
            photo_label.photo = img
            f = tk.font.Font(size=40)
            battle_button = tk.Button(self.home_frame, text = "Battle", command = partial(self.choose_opp_screen, self.home_frame), height = 2, width = 15, bg="#ffcc03",font=f)
            train_button = tk.Button(self.home_frame, text = "Train", command = partial(self.train_screen_begin, self.home_frame), height = 2, width = 15, bg = "#ffcc03", font=f)
            tutorial_button = tk.Button(self.home_frame, text = "Tutorial", command = partial(self.tutorial_screen, self.home_frame), height = 2, width = 15, bg="#ffcc03", font=f)
            exit_button = tk.Button(self.home_frame, text = "Exit", command = self.exit_game, height = 2, width = 15, bg="#ffcc03", font=f)

            photo_label.pack(pady= 30)
            battle_button.pack(pady=10)
            train_button.pack(pady=10)
            tutorial_button.pack(pady=10)
            exit_button.pack(pady=10)
        self.home_frame.pack(fill='both', expand=True)

    def tutorial_screen(self, prev_screen = None):
        print("Tutorial screen")
        winsound.PlaySound('click.wav', winsound.SND_FILENAME | winsound.SND_ASYNC)

        if prev_screen:
            prev_screen.pack_forget()

        self.client.unsubscribe("ece180d/pokEEmon/" + self.user.username + "/request")
        print("Unsubscribed from " + "ece180d/pokEEmon/" + self.user.username + "/request")

        tutorial_frame = tk.Frame(self.window, bg = "#34cfeb")
        mode_img =  ImageTk.PhotoImage(Image.open("tutorial_img.png"))
        mode_label = tk.Label(tutorial_frame, image=mode_img, bg = "#34cfeb")
        mode_label.photo = mode_img

        # Tutorial Text
        font_tuple = ("Lucida Sans", 16, "bold")
        heading_font_tuple = ("Comic Sans", 20, "bold")
        objective_t = tk.Text(tutorial_frame, height = 6, width = 100, bg = "#34cfeb")
        leveling_t = tk.Text(tutorial_frame, height = 6, width = 100, bg = "#34cfeb")
        training_t = tk.Text(tutorial_frame, height = 6, width = 100, bg = "#34cfeb")
        battling_t = tk.Text(tutorial_frame, height = 6, width = 100, bg = "#34cfeb")
        objective_header = tk.Label(tutorial_frame, text="Objective", bg = "#34cfeb")
        leveling_header = tk.Label(tutorial_frame, text="Leveling System", bg = "#34cfeb")
        training_header = tk.Label(tutorial_frame, text="Training", bg = "#34cfeb")
        battling_header = tk.Label(tutorial_frame, text="Battling", bg = "#34cfeb")
        objective_text = """The objective of PokEEmon is to construct the most powerful team possible by means of battling other players, defeating CPU opponents, and training with your monsters. Players can construct teams of up to six PokEEmon that each possess different strengths and weaknesses including their types and attributes. As prospective trainers play through the game, their PokEEmon will grow with them. """
        leveling_text = """Your PokEEmon gain experience through two methods: training and battling. By gaining experience points through battling opponents and training, each PokEEmon is able to level up, gaining access to new moves and increasing their attribute values for battle. For every 1000 experience points, your PokEEmon will level up. Depending on the species of your PokEEmon, they may learn new moves once they reach certain levels."""
        training_text = """Training entails utilizing a webcam to match poses displayed on the game screen. Before training can begin, players must select a specific team member to train. A yoga pose will be depicted next to your webcam feed, and the goal is to match the depicted pose as closely as possible. For each successfully matched pose, your selected PokEEmon will gain XXXXX experience points. """
        battling_text = """The battling system works identically between multiplayer and CPU battles. In both instances, you will be facing a team of PokEEmon in turn-based combat. A battle ends when either one party forfeits or when all members of a party’s HP reaches zero. Battles progress through a turn-based system. During their turn, players can either select a PokEEmon on their team to switch out or select a move to use in battle. Each PokEEmon will have a unique set of moves depending on their species and level. """
        objective_t.insert(tk.INSERT, objective_text)
        leveling_t.insert(tk.INSERT, leveling_text)
        training_t.insert(tk.INSERT, training_text)
        battling_t.insert(tk.INSERT, battling_text)
        objective_t.configure(font = font_tuple)
        leveling_t.configure(font = font_tuple)
        training_t.configure(font = font_tuple)
        battling_t.configure(font = font_tuple)
        objective_header.configure(font = heading_font_tuple)
        leveling_header.configure(font = heading_font_tuple)
        training_header.configure(font = heading_font_tuple)
        battling_header.configure(font = heading_font_tuple)
        back_button = tk.Button(tutorial_frame, text = "Back", command = partial(self.home_screen, tutorial_frame), height=6, width = 40, bg = "#ffcc03")

        mode_label.pack(pady=10)
        objective_header.pack()
        objective_t.pack()
        leveling_header.pack()
        leveling_t.pack()
        training_header.pack()
        training_t.pack()
        battling_header.pack()
        battling_t.pack()
        back_button.pack(pady=10)
        tutorial_frame.pack()

        os.startfile("tutorial.mp4")

    def choose_opp_screen(self, prev_screen = None):
        print("Choose opp screen")
        winsound.PlaySound('click.wav', winsound.SND_FILENAME | winsound.SND_ASYNC)

        if prev_screen:
            prev_screen.pack_forget()

        self.client.unsubscribe("ece180d/pokEEmon/" + self.user.username + "/request")
        print("Unsubscribed from " + "ece180d/pokEEmon/" + self.user.username + "/request")

        if not self.choose_opp_frame:
            self.choose_opp_frame = tk.Frame(self.window, bg = "#34cfeb")
            mode_img =  ImageTk.PhotoImage(Image.open("choose_battle_mode_img.png"))
            mode_label = tk.Label(self.choose_opp_frame, image=mode_img, bg = "#34cfeb")
            mode_label.photo = mode_img
            single_button = tk.Button(self.choose_opp_frame, text = "Single-player", command = partial(self.single_battle, self.choose_opp_frame), height=6, width=40, bg = "#ffcc03")
            multi_button = tk.Button(self.choose_opp_frame, text = "Multi-player", command = partial(self.request_screen, self.choose_opp_frame), height=6, width=40, bg = "#ffcc03")
            back_button = tk.Button(self.choose_opp_frame, text = "Back", command = partial(self.home_screen, self.choose_opp_frame), height=6, width = 40, bg = "#ffcc03")

            mode_label.pack(pady=10)
            single_button.pack(pady=10)
            multi_button.pack(pady=10)
            back_button.pack(pady=10)

        self.choose_opp_frame.pack()

    def receive_screen(self, opp_username):
        print("Receive screen")
        winsound.PlaySound('click.wav', winsound.SND_FILENAME | winsound.SND_ASYNC)
        self.home_frame.pack_forget()
        if self.receive_frame:
            self.receive_frame.destroy()

        self.client.unsubscribe("ece180d/pokEEmon/" + self.user.username + "/request")
        self.client.on_message = self.rcv_cancel_mqtt
        self.client.subscribe("ece180d/pokEEmon/" + self.user.username + "/cancel")
        print("Unsubscribed from " + "ece180d/pokEEmon/" + self.user.username + "/request")
        print("Subscribed to " + "ece180d/pokEEmon/" + self.user.username + "/cancel")

        self.receive_frame = tk.Frame(self.window, bg = "#34cfeb")

        img = ImageTk.PhotoImage(Image.open("battle_img.png"))
        receive_photo_label = tk.Label(self.receive_frame, image = img, bg = "#34cfeb")
        receive_photo_label.photo = img

        receive_label = tk.Label(self.receive_frame, text=opp_username, font=("Arial", 50), bg = "#34cfeb")
        accept_button = tk.Button(self.receive_frame, text = "Accept", command = partial(self.accept_request, opp_username), height = 6, width = 70, bg="#ffcc03")
        decline_button = tk.Button(self.receive_frame, text = "Decline", command = partial(self.decline_request, opp_username), height = 6, width = 70, bg="#ffcc03")
        receive_photo_label.pack(pady=10)
        receive_label.pack(pady=15)
        accept_button.pack(pady=10)
        decline_button.pack(pady=10)

        self.receive_frame.pack()

    def request_screen(self, prev_screen = None):
        print("Request screen")
        winsound.PlaySound('click.wav', winsound.SND_FILENAME | winsound.SND_ASYNC)

        if prev_screen:
            prev_screen.pack_forget()
        if self.request_frame:
            self.request_frame.destroy()

        self.client.unsubscribe("ece180d/pokEEmon/" + self.user.username + "/response")
        print("Unsubscribed from " + "ece180d/pokEEmon/" + self.user.username + "/response")

        self.request_frame = tk.Frame(self.window, bg = "#34cfeb")
        request_img = ImageTk.PhotoImage(Image.open("request_img.png"))
        request_label = tk.Label(self.request_frame, image=request_img, bg = "#34cfeb")
        request_label.photo = request_img
        username_entry = tk.Entry(self.request_frame, font=("default", 16))
        submit_button = tk.Button(self.request_frame, text = "Submit", command = partial(self.make_request, username_entry), height=6, width=40, bg = "#ffcc03")
        back_button = tk.Button(self.request_frame, text = "Back", command = partial(self.choose_opp_screen, self.request_frame), height=6, width = 40, bg = "#ffcc03")
        request_label.pack(pady=10)
        username_entry.pack(pady=10)
        submit_button.pack(pady=10)
        back_button.pack(pady=10)

        self.request_frame.pack()


    def response_screen(self, opp_username):
        winsound.PlaySound('click.wav', winsound.SND_FILENAME | winsound.SND_ASYNC)
        print("Response screen")
        self.request_frame.pack_forget()
        if self.response_frame:
            self.response_frame.destroy()


        self.client.on_message = self.rcv_response_mqtt
        self.client.subscribe("ece180d/pokEEmon/" + self.user.username + "/response")
        print("Subscribed to " + "ece180d/pokEEmon/" + self.user.username + "/response")

        self.response_frame = tk.Frame(self.window, bg = "#34cfeb")
        waiting_img = ImageTk.PhotoImage(Image.open("waiting_img.png"))
        waiting_label = tk.Label(self.response_frame, image=waiting_img, bg = "#34cfeb")
        waiting_label.photo = waiting_img
        request_label = tk.Label(self.response_frame, text=opp_username, font=("Arial", 25), bg= "#34cfeb")
        cancel_button = tk.Button(self.response_frame, text = "Cancel", command = partial(self.cancel_request, opp_username), height = 6, width = 70, bg = "#ffcc03")
        waiting_label.pack(pady=10)
        request_label.pack(pady=10)
        cancel_button.pack(pady=10)

        self.response_frame.pack()

    def single_battle(self, prev_screen = None):
        print("Starting Single-player battle")
        winsound.PlaySound('click.wav', winsound.SND_FILENAME | winsound.SND_ASYNC)

        if prev_screen:
            prev_screen.pack_forget()

        self.opp_user = User()
        self.opp_user.username = "Bot"
        basepk_df = pd.read_csv("data/pokemon.csv")
        num_pk = random.randint(2, 5)
        self.opp_user.team_df = basepk_df.sample(n = num_pk)
        self.opp_user.team_df.reset_index(drop=True, inplace=True)

        total_xp = sum(self.user.team_df["xp_accumulated"].values)

        for i in range(self.opp_user.team_df.shape[0]):
            xp_boost = max(0, random.randint(total_xp // num_pk - 2000, total_xp // num_pk + 1000))
            self.opp_user.team_df.loc[i] = level_up(self.opp_user.team_df.loc[i], xp_boost)

        print("Generated opponent team:")
        print(self.opp_user.team_df)


        self.battle = Battle(self.user, None, self.opp_user, self.window, self.client, self.home_screen, self.id, True)
        if random.randint(0, 1):
            self.battle.move_screen()
        else:
            self.battle.wait_screen()


    def set_pokemon(self, pokemon_name):
        '''
        Set the current working pokemon that will be used for training
        '''
        self.working_pokemon = pokemon_name
        print(f"switched working pokemon to {pokemon_name}")

    def choose_pose(self):
        '''
        Randomly returns a string pose to be printed and to be done
        '''
        poses = ["Warrior Pose", "T Pose", "Tree Pose"]
        return poses[random.randint(0,2)]

    def train_screen_begin(self, prev_screen = None, camera = None):
        winsound.PlaySound('click.wav', winsound.SND_FILENAME | winsound.SND_ASYNC)
        '''
        Creates the screen that gives choices for pokemon to train
        '''
        print("Training screen Beginning")
        if prev_screen:
            prev_screen.pack_forget()
        if camera:
            camera.release()

        if not self.train_frame_begin:
            f = tk.font.Font(size=30)
            self.train_frame_begin = tk.Frame(self.window, bg = "#34cfeb")
            choose_img =  ImageTk.PhotoImage(Image.open("choose_img.png"))
            choose_label = tk.Label(self.train_frame_begin, image=choose_img, bg = "#34cfeb")
            choose_label.photo = choose_img
            pokemon_list = self.user.team_df["name"].tolist()
            choose_label.pack()
            for pokemon_name in pokemon_list:
                tk.Button(self.train_frame_begin, text = pokemon_name, command = partial(self.train_screen, pokemon_name), height = 2, width = 15, bg="#ffcc03", font=f).pack(pady=10)
            tk.Button(self.train_frame_begin, text = "Back", command = partial(self.home_screen, self.train_frame_begin), height = 2, width = 15, bg="#ffcc03", font = f).pack(pady=10)
        self.train_frame_begin.pack()

    def train_screen(self, pokemon_name):
        winsound.PlaySound('click.wav', winsound.SND_FILENAME | winsound.SND_ASYNC)
        '''
        Training that starts after pokemon is selected through having 2 windows,
        one of the camera and one of the pose to be matched.
        '''
        cap = cv2.VideoCapture(0)
        self.working_pokemon = pokemon_name
        self.train_frame_begin.pack_forget()
        if self.train_frame:
            self.train_frame.destroy()
        self.train_frame = tk.Frame(self.window, bg = "#34cfeb")
        self.train_frame.pack()

        tk.Button(self.train_frame, text="Switch Pokemon", command = partial(self.train_screen_begin, self.train_frame, cap), height = 2, width = 20, bg="#ffcc03").pack(pady=10)

        self.desired_pose = self.choose_pose()

        xp_label = tk.Label(self.train_frame, bg = "#34cfeb")
        xp = self.user.team_df.loc[self.user.team_df["name"]==pokemon_name, "xp_accumulated"].values[0]
        xp_label.config(text=f"Current XP of {pokemon_name}: {xp}", font=("Arial", 25))
        xp_label.pack()

        desired_pose_label = tk.Label(self.train_frame, bg = "#34cfeb")
        desired_pose_label.config(text = f"Match the pose of: {self.desired_pose}", font=("Arial", 25))
        desired_pose_label.pack()
        #Initializing mediapipe pose class.
        mp_pose = mp.solutions.pose
        #Setting up the Pose function.
        #Initializing mediapipe drawing class, useful for annotation.
        mp_drawing = mp.solutions.drawing_utils

        #create label for cv image feed
        label = tk.Label(self.train_frame)
        #create label for pose reference image
        ref_img_label = tk.Label(self.train_frame)

        pose_video = mp_pose.Pose(static_image_mode=False, min_detection_confidence=0.5, model_complexity=1)

        #reference image switch statement
        def pull_image(chosen_pose):
            '''
            pulls the referenced image to show as the pose to match
            '''
            if (chosen_pose == "Warrior Pose"):
                return "warrior2.png"
            if (chosen_pose == "T Pose"):
                return "tpose.png"
            if (chosen_pose == "Tree Pose"):
                return "tree.jpg"
            else:
                return "error.jpg"

        def show_frames():
            '''
            function to show live video feed with the Computer Vision on Top
            '''
            # Get the latest frame and convert into Image
            if cap:
                frame = cap.read()[1]
                frame = cv2.flip(frame, 1)
                self.height, self.width, _ = frame.shape
                frame, landmarks = ps.detectPose(frame, pose_video, mp_drawing, mp_pose, display=False)
                returned_pose = None
                if landmarks:
                    frame, returned_pose = ps.classifyPose(landmarks, frame, mp_pose, display=False)
                else:
                    cv2.putText(frame, 'No Human Detected', (10, 30), cv2.FONT_HERSHEY_PLAIN, 2, (0, 0, 255), 2)
                if returned_pose == self.desired_pose:
                    print("matched pose!")
                    #### LEVELING UP ####
                    for i in range(self.user.team_df.shape[0]):
                        self.user.team_df.loc[i] = level_up(self.user.team_df.loc[i], 20)

                    print("Writing updated team to {}".format(self.user.path + "/team.csv"))
                    print(self.user.team_df)

                    self.user.team_df.to_csv(self.user.path + "/team.csv", index=False, quoting=csv.QUOTE_NONNUMERIC)

                    self.desired_pose = self.choose_pose()
                    desired_pose_label.config(text = f"Match the pose of: {self.desired_pose}")
                    xp = self.user.team_df.loc[self.user.team_df["name"]==self.working_pokemon, "xp_accumulated"].values[0]
                    xp_label.config(text=f"Current XP of {self.working_pokemon}: {xp}", font=("Arial", 25))

                cv2image= cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)
                img = Image.fromarray(cv2image)
                # Convert image to PhotoImage
                imgtk = ImageTk.PhotoImage(image = img)
                label.imgtk = imgtk
                label.configure(image=imgtk)
                label.pack(side = tk.LEFT)
                #access and pack reference image
                ref_img = ImageTk.PhotoImage(file = pull_image(self.desired_pose))
                ref_img_label.imgtk = ref_img
                ref_img_label.configure(image = ref_img)
                ref_img_label.pack(side = tk.RIGHT)

                label.after(1, show_frames)

        label.after(1, show_frames)



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
        self.battle = Battle(self.user, self.request_num, self.opp_user, self.window, self.client, self.home_screen, self.id)
        self.battle.move_screen(self.receive_frame)

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
        winsound.PlaySound('click.wav', winsound.SND_FILENAME)
        self.window.destroy()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Start the game by typing ./pokEEmon.py <username> <id>"
    )

    parser.add_argument("username", type=str, help="your in-game username")
    parser.add_argument("id", type=str, help="your pi id")
    args = parser.parse_args()
    print("Welcome " + args.username)

    game = Game(args.username, args.id)
    game.connect_mqtt()
    game.home_screen()
    game.start_game()
