import paho.mqtt.client as mqtt
import os
import csv
import io
import time
import pandas as pd
import tkinter as tk
import tkinter.font as tkfont
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
import pronouncing
from pygame import mixer
import PkUtils as ut

class Battle:
    def __init__(self, user, battle_id, opp_user, window, client, home, id, learn_set, singleplayer = False):
        self.user = user
        self.user.team_df["curr_hp"] = self.user.team_df["hp"]
        self.user_teamsize = len(self.user.team_df.index)
        self.user_statuses = [[0] * 4] * self.user_teamsize
        self.battle_id = battle_id
        self.opp_user = opp_user
        self.opp_user.team_df["curr_hp"] = self.opp_user.team_df["hp"]
        self.opp_teamsize = len(self.opp_user.team_df.index)
        self.opp_statuses = [[0] * 4] * self.opp_teamsize
        self.window = window
        self.client = client
        self.home = home
        self.curr_pokemon = 0
        self.opp_pokemon = 0
        self.stop_listening = None
        self.id = id
        self.movename = None
        self.moves_df = pd.read_csv("data/moves.csv")
        self.singleplayer = singleplayer
        self.gameover = False
        self.curr_frame = None
        self.timeout_num = None
        self.learnset = learn_set
        print("Setting up mic and receiver for speech recognition")
        self.mic = sr.Microphone()
        self.rec = sr.Recognizer()
        with self.mic as source:
            self.rec.adjust_for_ambient_noise(source)
        self.gesturelist = ["slash", "block", "whip", "scratch"]
        mixer.music.stop()
        mixer.music.load("sounds/battle song.mp3")
        mixer.music.set_volume(0.25)
        mixer.music.play(-1)

        print(self.user.team_df)
        print(self.user_statuses)
        print(self.opp_statuses)

        #burn: physical damage halved, loses 1/16 of health per turn
        #paralyze: speed halved, 25% chance of losing turn
        #freeze: cannot move, 20% chance per turn of thawing out
        #poison: lose 1/8 of max hp each turn


    def rcv_gesture_mqtt(self, client, userdata, message):
        print("Received move message")
        msg = message.payload
        print(msg)

        msg = str(msg.decode())

        if msg == self.gesturelist[hash(self.movename)%4]:
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
            winsound.PlaySound('sounds/whoosh.wav', winsound.SND_FILENAME | winsound.SND_ASYNC)
            self.timeout_num = None
            movename = msg[3]
            pokeemon_name = self.opp_user.team_df.iloc[self.opp_pokemon, self.opp_user.team_df.columns.get_loc("name")]
            damage = self.calc_damage(movename, int(msg[4]), self.opp_user.team_df.iloc[self.opp_pokemon], self.user.team_df.iloc[self.curr_pokemon])
            curr_hp = self.user.team_df.iloc[self.curr_pokemon, self.user.team_df.columns.get_loc("curr_hp")]
            curr_hp -= damage
            #do status update after damage calculation
            self.update_status(movename, pokeemon_name)
            if curr_hp < 0:
                curr_hp = 0
            self.user.team_df.iloc[self.curr_pokemon, self.user.team_df.columns.get_loc("curr_hp")] = curr_hp
            if self.user.team_df[self.user.team_df["curr_hp"] > 0].empty:
                print("You lost")
                self.user.gamestats_df["games_played"] += 1
                self.user.gamestats_df.to_csv(self.user.path + "/gamestats.csv", index=False, quoting=csv.QUOTE_NONNUMERIC)
                self.gameover_screen(False)
            else:
                self.move_screen("{}'s {} played {}".format(self.opp_user.username, pokeemon_name.capitalize(), movename.capitalize()))
        elif msg and msg[0] == "change" and int(msg[2]) == self.battle_id:
            self.opp_pokemon = int(msg[3])
            self.wait_screen("{} changed their PokEEmon to {}".format(self.opp_user.username, self.opp_user.team_df.iloc[self.opp_pokemon, self.opp_user.team_df.columns.get_loc("name")].capitalize()), self.curr_frame)
        elif msg and msg[0] == "quit" and int(msg[2]) == self.battle_id:
            print("You won")
            self.user.gamestats_df["games_played"] += 1
            self.user.gamestats_df["wins"] += 1
            self.user.gamestats_df.to_csv(self.user.path + "/gamestats.csv", index=False, quoting=csv.QUOTE_NONNUMERIC)
            self.gameover_screen(True)
            print("Here")
        else:
            print("Received unexpected message")


    def voice_callback(self, recognizer, audio):
        try:
            words = recognizer.recognize_google(audio).lower()
            print("Heard: " + words)
            for move in ["move1", "move2", "move3", "move4"]:
                movename = self.user.team_df.iloc[self.curr_pokemon][move]
                if movename != movename: # true for movename of NaN
                    continue

                if movename.replace("-", " ") in words or movename.replace("-", "") in words:
                    self.gesture_screen(move)
                    return

                movename =  movename.replace("-", "")
                rhymes = pronouncing.rhymes(movename)
                for rhyme in rhymes:
                    if rhyme in words:
                        self.gesture_screen(move)
                        return

            print("Not a move")
        except sr.UnknownValueError:
            print("Google Speech Recognition could not understand audio")
        except sr.RequestError as e:
            print("Could not request results from Google Speech Recognition service; {0}".format(e))

    def sel_pokemon(self, index, prev_move_frame):
        self.curr_pokemon = index
        if not self.singleplayer:
            choose_msg = "change,{},{},{}".format(self.user.username, self.battle_id, index)
            self.client.publish("ece180d/pokEEmon/" + self.opp_user.username + "/change", choose_msg)
        self.move_screen(prev_move_frame = prev_move_frame)

    def quit(self):
        if self.stop_listening is not None:
            self.stop_listening(wait_for_stop=False)
            self.stop_listening = None

        self.user.gamestats_df["games_played"] += 1
        self.user.gamestats_df.to_csv(self.user.path + "/gamestats.csv", index=False, quoting=csv.QUOTE_NONNUMERIC)

        if not self.singleplayer:
            quit_msg = "quit,{},{}".format(self.user.username, self.battle_id)
            self.client.publish("ece180d/pokEEmon/" + self.opp_user.username + "/quit", quit_msg)

        self.gameover_screen(False)

    def timeout(self, timeout_num, win):
        if self.timeout_num != timeout_num:
            return

        self.timeout_num = None

        if self.stop_listening is not None:
            self.stop_listening(wait_for_stop=False)
            self.stop_listening = None

        self.user.gamestats_df["games_played"] += 1
        if win:
            self.user.gamestats_df["wins"] += 1
        self.user.gamestats_df.to_csv(self.user.path + "/gamestats.csv", index=False, quoting=csv.QUOTE_NONNUMERIC)

        self.gameover_screen(win)

    def do_move(self):
        winsound.PlaySound('sounds/whoosh.wav', winsound.SND_FILENAME | winsound.SND_ASYNC)
        self.timeout_num = None
        random_mult = random.randrange(85,100)
        damage = self.calc_damage(self.movename, random_mult, self.user.team_df.iloc[self.curr_pokemon], self.opp_user.team_df.iloc[self.opp_pokemon])
        opp_curr_hp = self.opp_user.team_df.iloc[self.opp_pokemon, self.opp_user.team_df.columns.get_loc("curr_hp")]
        opp_curr_hp -= damage
        #do status update after damage calculation
        self.update_status(self.movename, self.opp_user.team_df.iloc[self.opp_pokemon, self.opp_user.team_df.columns.get_loc("name")])
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
                self.user.team_df.loc[i] = ut.level_up(self.user.team_df.loc[i], xp_reward, self.learnset)

            print("Writing updated team to {}".format(self.user.path + "/team.csv"))
            print(self.user.team_df)

            self.user.team_df.to_csv(self.user.path + "/team.csv", index=False, quoting=csv.QUOTE_NONNUMERIC)

            self.user.gamestats_df["games_played"] += 1
            self.user.gamestats_df["wins"] += 1
            self.user.gamestats_df.to_csv(self.user.path + "/gamestats.csv", index=False, quoting=csv.QUOTE_NONNUMERIC)

            self.gameover_screen(True)
        else:
            self.wait_screen("Your {} played {}".format(self.user.team_df.iloc[self.curr_pokemon, self.user.team_df.columns.get_loc("name")].capitalize(), self.movename.capitalize()))

    def calc_damage(self, movename, random_mult, attack_pk, receive_pk):
        random_mult = float(random_mult) * 0.01  #random multiplier from 0.85 to 1
        multiplier = self.find_effectiveness(self.moves_df.loc[self.moves_df["identifier"] == movename]["type"].values[0], receive_pk["type"])
        special = int(self.moves_df.loc[self.moves_df["identifier"] == movename]["damage_class_id"])
        if (attack_pk["type"] == self.moves_df.loc[self.moves_df["identifier"] == movename]["type"].values[0]): #implement same type attack bonus
            stab = 1.5
        else:
            stab = 1
        pwr =  float(self.moves_df.loc[self.moves_df["identifier"] == movename]["power"])

        #special attack calc
        if (special == 2):
            damage = ((((((2*attack_pk["level"])/5)+2)*pwr*(attack_pk["special_attack"]/receive_pk["special_defense"]))/50)+2)*stab*multiplier*random_mult
        #physical attack calc
        else:
            damage = ((((((2*attack_pk["level"])/5)+2)*pwr*(attack_pk["attack"]/receive_pk["defense"]))/50)+2)*stab*multiplier*random_mult

        return int(math.floor(damage))

    def update_status(self, move_name, receive_pk_name):
        test = 0

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
        typeList = ["normal", "fire", "water", "electric", "grass", "ice", "fighting", "poison", "ground", "flying", "psychic", "bug", "rock", "ghost", "dragon", "dark", "steel", "fairy",]

        multiplier = effectiveness_array[typeList.index(attack_type)][typeList.index(receive_type)]
        return multiplier

    def gesture_screen(self, move):
        print("Waiting for gesture")
        winsound.PlaySound('sounds/click.wav', winsound.SND_FILENAME | winsound.SND_ASYNC)
        if self.curr_frame:
            self.curr_frame.pack_forget()

        prev_move_frame = self.curr_frame

        if self.stop_listening is not None:
            self.stop_listening(wait_for_stop=False)
            self.stop_listening = None

        self.movename = self.user.team_df.iloc[self.curr_pokemon][move]

        self.client.on_message = self.rcv_gesture_mqtt
        self.client.subscribe("ece180d/pokEEmon/" + self.id, qos=1)
        print("Subscribed to " + "ece180d/pokEEmon/" + self.id)

        movename = self.gesturelist[hash(self.movename)%4]
        gesture_frame = tk.Frame(self.window, bg = "#34cfeb")
        gesture_label = tk.Label(gesture_frame, text="Do a {} ".format(movename.capitalize()), font=("Arial", 25), bg= "#34cfeb")
        gesture_img =  ImageTk.PhotoImage(Image.open("images/{}.png".format(movename)))
        gesture_img_label = tk.Label(gesture_frame, image=gesture_img, bg = "#34cfeb")
        gesture_img_label.photo = gesture_img

        back_button = tk.Button(gesture_frame, text="Back", command = partial(self.move_screen, None, prev_move_frame), height = 2, width = 18, bg = "#ffcc03", font = tk.font.Font(size=30))
        gesture_label.pack(pady = 5)
        gesture_img_label.pack(pady = 5)
        back_button.pack(pady = 10)

        gesture_frame.pack()
        self.curr_frame = gesture_frame

        # TODO: remove this when using gestures
        self.window.after(1000, self.do_move)

    def wait_screen(self, move_update = None, prev_wait_frame = None):
        '''
        Creating screen that handles waiting for opponent to make a move
        '''
        print("Waiting for opponent move")


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


        if prev_wait_frame is not None:
            prev_wait_frame.pack_forget()
            wait_frame = prev_wait_frame
            for widget in wait_frame.winfo_children():
                widget.destroy()
        else:
            if self.curr_frame:
                self.curr_frame.destroy()
            wait_frame = tk.Frame(self.window, bg = "#34cfeb")
            randnum = random.randint(0,1000000000)
            self.timeout_num = randnum
            if not self.singleplayer:
                self.window.after(30000, lambda : self.timeout(randnum, True))

        if move_update is not None:
            update_label = tk.Label(wait_frame, text=move_update, bg = "#34cfeb", font=("Arial", 30))
            update_label.pack()
        else:
            winsound.PlaySound('sounds/click.wav', winsound.SND_FILENAME | winsound.SND_ASYNC)

        wait_img =  ImageTk.PhotoImage(Image.open("images/wait_opponent_move_img.png"))
        wait_label = tk.Label(wait_frame, image=wait_img, bg = "#34cfeb")
        wait_label.photo = wait_img
        quit_button = tk.Button(wait_frame, text="Quit", command = self.quit, height = 2, width = 18, bg="#ffcc03", font = tk.font.Font(size=30))

        user_pokemon_name = self.user.team_df.iloc[self.curr_pokemon, self.user.team_df.columns.get_loc("name")]
        user_pokemon_id = self.user.team_df.iloc[self.curr_pokemon, self.user.team_df.columns.get_loc("id")]
        user_pokemon_hp = self.user.team_df.iloc[self.curr_pokemon, self.user.team_df.columns.get_loc("curr_hp")]

        opp_pokemon_name = self.opp_user.team_df.iloc[self.opp_pokemon, self.opp_user.team_df.columns.get_loc("name")]
        opp_pokemon_id = self.opp_user.team_df.iloc[self.opp_pokemon, self.opp_user.team_df.columns.get_loc("id")]
        opp_pokemon_hp = self.opp_user.team_df.iloc[self.opp_pokemon, self.opp_user.team_df.columns.get_loc("curr_hp")]

        wait_label.pack(pady = 5)

        wait_subframe = tk.Frame(wait_frame, bg = "#34cfeb")
        wait_subframel = tk.Frame(wait_subframe, bg = "#34cfeb")
        wait_subframer = tk.Frame(wait_subframe, bg = "#34cfeb")

        userteam_label = tk.Label(wait_subframel, text=f"Your Pokemon: {user_pokemon_name.capitalize()} \n HP: {user_pokemon_hp}", bg = "#34cfeb", font=("Arial", 30))
        userteam_label.pack()

        oppteam_label = tk.Label(wait_subframer, text=f"Opponent Pokemon: {opp_pokemon_name.capitalize()} \n HP: {opp_pokemon_hp}", bg = "#34cfeb", font=("Arial", 30))
        oppteam_label.pack()

        # Adding Sprites
        if os.path.isfile("sprites/"+str(user_pokemon_id)+".png"):
            user_pokemon_img_path = "sprites/"+str(user_pokemon_id)+".png"
        else:
            user_pokemon_img_path = "sprites/1.png"
        if os.path.isfile("sprites/"+str(opp_pokemon_id)+".png"):
            opp_pokemon_img_path = "sprites/"+str(opp_pokemon_id)+".png"
        else:
            opp_pokemon_img_path = "sprites/1.png"


        user_pokemon_img = ImageTk.PhotoImage(Image.open(user_pokemon_img_path).convert("RGBA"))
        user_pokemon_img_label = tk.Label(wait_subframel, image = user_pokemon_img, bg = "#34cfeb")
        user_pokemon_img_label.photo = user_pokemon_img
        user_pokemon_img_label.pack()

        opp_pokemon_img = ImageTk.PhotoImage(Image.open(opp_pokemon_img_path).convert("RGBA"))
        opp_pokemon_img_label = tk.Label(wait_subframer, image = opp_pokemon_img, bg = "#34cfeb")
        opp_pokemon_img_label.photo = opp_pokemon_img
        opp_pokemon_img_label.pack()

        wait_subframel.pack(side=tk.LEFT, padx = 40)
        wait_subframer.pack(side=tk.RIGHT, padx = 40)
        wait_subframe.pack(pady=30)


        quit_button.pack(pady = 5)

        wait_frame.pack()
        self.curr_frame = wait_frame

        if self.singleplayer:
            self.window.after(3000, self.bot_move)

    def gameover_screen(self, won, back = False):
        if self.gameover and not back:
            return

        if back:
            winsound.PlaySound('sounds/click.wav', winsound.SND_FILENAME | winsound.SND_ASYNC)
        else:
            if won:
                winsound.PlaySound('sounds/win chime.wav', winsound.SND_FILENAME | winsound.SND_ASYNC)
            else:
                winsound.PlaySound('sounds/lose chime.wav', winsound.SND_FILENAME | winsound.SND_ASYNC)

            self.gameover = True
            mixer.music.stop()
            mixer.music.load("sounds/menu music.mp3")
            mixer.music.set_volume(0.25)
            mixer.music.play(-1)

            if not self.singleplayer:
                self.client.unsubscribe("ece180d/pokEEmon/" + self.id)
                self.client.unsubscribe("ece180d/pokEEmon/" + self.user.username + "/move")
                self.client.unsubscribe("ece180d/pokEEmon/" + self.user.username + "/change")
                self.client.unsubscribe("ece180d/pokEEmon/" + self.user.username + "/quit")

            if self.stop_listening is not None:
                self.stop_listening(wait_for_stop=False)
                self.stop_listening = None

        if self.curr_frame:
            self.curr_frame.destroy()

        f = tkfont.Font(size=40)
        gameover_frame = tk.Frame(self.window, bg = "#34cfeb")
        if won:
            won_img = ImageTk.PhotoImage(Image.open("images/won_img.png"))
            gameover_label = tk.Label(gameover_frame, image=won_img, bg = "#34cfeb")
            gameover_label.photo = won_img
        else:
            lost_img = ImageTk.PhotoImage(Image.open("images/lost_img.png"))
            gameover_label = tk.Label(gameover_frame, image=lost_img, bg = "#34cfeb")
            gameover_label.photo = lost_img

        gameover_label.pack(pady = 5)

        if won and self.singleplayer and self.opp_user.team_df.shape[0] == 1:
            #add button to capture pokEEmon
            add_button = tk.Button(gameover_frame, text="Capture {}".format(self.opp_user.team_df.iloc[0]["name"].capitalize()), command = self.add_screen, height = 2, width = 18, bg="#ffcc03",font=f)
            add_button.pack(pady = 5)
        see_button = tk.Button(gameover_frame, text="View Team", command = self.see_screen, height = 2, width = 18, bg="#ffcc03",font=f)
        home_button = tk.Button(gameover_frame, text="Home", command = partial(self.home, gameover_frame), height = 2, width = 18, bg="#ffcc03",font=f)

        see_button.pack(pady = 5)
        home_button.pack(pady = 5)
        gameover_frame.pack()
        self.curr_frame = gameover_frame

    def bot_move(self):
        if self.gameover:
            return

        winsound.PlaySound('sounds/whoosh.wav', winsound.SND_FILENAME | winsound.SND_ASYNC)
        if self.curr_frame:
            self.curr_frame.destroy()

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
                if movename != movename: #returns true for movename of NaN
                    continue
                damage = self.calc_damage(movename, random_mult, pk, self.user.team_df.iloc[self.curr_pokemon])
                if damage > best_damage:
                    best_damage = damage
                    best_pk = i
                    best_move = movename

        self.opp_pokemon = best_pk
        pokeemon_name = self.opp_user.team_df.iloc[self.opp_pokemon, self.opp_user.team_df.columns.get_loc("name")]
        curr_hp = self.user.team_df.iloc[self.curr_pokemon, self.user.team_df.columns.get_loc("curr_hp")]
        curr_hp -= best_damage
        #update status after damage calculations
        self.update_status(best_move, pokeemon_name)
        if curr_hp < 0:
            curr_hp = 0
        self.user.team_df.iloc[self.curr_pokemon, self.user.team_df.columns.get_loc("curr_hp")] = curr_hp
        if self.user.team_df[self.user.team_df["curr_hp"] > 0].empty:
            print("You lost")
            self.user.gamestats_df["games_played"] += 1
            self.user.gamestats_df.to_csv(self.user.path + "/gamestats.csv", index=False, quoting=csv.QUOTE_NONNUMERIC)
            self.gameover_screen(False)
        else:
            self.move_screen(move_update = "{}'s {} played {}".format(self.opp_user.username, pokeemon_name.capitalize(), best_move.capitalize()))


    def move_screen(self, move_update = None, prev_move_frame = None):
        print("Choose your move")
        f = tk.font.Font(size=30)

        if self.curr_frame:
            self.curr_frame.destroy()

        self.client.unsubscribe("ece180d/pokEEmon/" + self.id)
        print("Unsubscribed to " + "ece180d/pokEEmon/" + self.id)

        if not self.singleplayer:
            self.client.unsubscribe("ece180d/pokEEmon/" + self.user.username + "/move")
            self.client.unsubscribe("ece180d/pokEEmon/" + self.user.username + "/change")
            self.client.on_message = self.rcv_battle_mqtt
            self.client.subscribe("ece180d/pokEEmon/" + self.user.username + "/quit", qos = 1)
            print("Unsubscribed to " + "ece180d/pokEEmon/" + self.user.username + "/move")
            print("Unsubscribed to " + "ece180d/pokEEmon/" + self.user.username + "/change")
            print("Subscribed to " + "ece180d/pokEEmon/" + self.user.username + "/quit")

        if prev_move_frame is not None:
            move_frame = prev_move_frame
            for widget in move_frame.winfo_children():
                widget.destroy()
        else:
            move_frame = tk.Frame(self.window, bg = "#34cfeb")

            randnum = random.randint(0,1000000000)
            self.timeout_num = randnum
            if not self.singleplayer:
                self.window.after(30000, lambda : self.timeout(randnum, False))


        if move_update:
            update_label = tk.Label(move_frame, text=move_update, bg = "#34cfeb", font=("Arial", 30))
            update_label.pack()
            winsound.PlaySound('sounds/whoosh.wav', winsound.SND_FILENAME | winsound.SND_ASYNC)
        else:
            winsound.PlaySound('sounds/click.wav', winsound.SND_FILENAME | winsound.SND_ASYNC)

        if self.user.team_df.iloc[self.curr_pokemon, self.user.team_df.columns.get_loc("curr_hp")] > 0:
            img = ImageTk.PhotoImage(Image.open("images/choose_move_img.png"))
            move_label = tk.Label(move_frame, image = img, bg = "#34cfeb")
            move_label.photo = img
            move_label.pack(pady=5)
            for i in range(1,5):
                move_name = self.user.team_df.iloc[self.curr_pokemon]["move"+str(i)]
                if move_name == move_name:  #returns false for NaN
                    button = tk.Button(move_frame, text=move_name.capitalize(), command = partial(self.gesture_screen, "move"+str(i)), height = 1, width = 18, bg="#ffcc03", font=f)
                    button.pack(pady = 5)

            if self.mic is None:
                print("Setting up mic and receiver for speech recognition")
                self.mic = sr.Microphone()
                self.rec = sr.Recognizer()
                with self.mic as source:
                    self.rec.adjust_for_ambient_noise(source)

            self.stop_listening = self.rec.listen_in_background(self.mic, self.voice_callback, 2)
        else:
            img_2 = ImageTk.PhotoImage(Image.open("images/change_pokemon.png"))
            change_label = tk.Label(move_frame, image = img_2, bg = "#34cfeb")
            change_label.photo = img_2
            change_label.pack()

        user_pokemon_name = self.user.team_df.iloc[self.curr_pokemon, self.user.team_df.columns.get_loc("name")]
        user_pokemon_id = self.user.team_df.iloc[self.curr_pokemon, self.user.team_df.columns.get_loc("id")]
        user_pokemon_hp = self.user.team_df.iloc[self.curr_pokemon, self.user.team_df.columns.get_loc("curr_hp")]

        opp_pokemon_name = self.opp_user.team_df.iloc[self.opp_pokemon, self.opp_user.team_df.columns.get_loc("name")]
        opp_pokemon_id = self.opp_user.team_df.iloc[self.opp_pokemon, self.opp_user.team_df.columns.get_loc("id")]
        opp_pokemon_hp = self.opp_user.team_df.iloc[self.opp_pokemon, self.opp_user.team_df.columns.get_loc("curr_hp")]

        move_subframe = tk.Frame(move_frame, bg = "#34cfeb")
        move_subframel = tk.Frame(move_subframe, bg = "#34cfeb")
        move_subframer = tk.Frame(move_subframe, bg = "#34cfeb")

        userteam_label = tk.Label(move_subframel, text=f"Your Pokemon: {user_pokemon_name.capitalize()} \n HP: {user_pokemon_hp}", bg = "#34cfeb", font=("Arial", 30))
        userteam_label.pack()

        oppteam_label = tk.Label(move_subframer, text=f"Opponent Pokemon: {opp_pokemon_name.capitalize()} \n HP: {opp_pokemon_hp}", bg = "#34cfeb", font=("Arial", 30))
        oppteam_label.pack()

        # Adding Sprites
        # user Pokemon
        if os.path.isfile("sprites/"+str(user_pokemon_id)+".png"):
            user_pokemon_img_path = "sprites/"+str(user_pokemon_id)+".png"
        else:
            user_pokemon_img_path = "sprites/1.png"
        if os.path.isfile("sprites/"+str(opp_pokemon_id)+".png"):
            opp_pokemon_img_path = "sprites/"+str(opp_pokemon_id)+".png"
        else:
            opp_pokemon_img_path = "sprites/1.png"


        user_pokemon_img = ImageTk.PhotoImage(Image.open(user_pokemon_img_path).convert("RGBA"))
        user_pokemon_img_label = tk.Label(move_subframel, image = user_pokemon_img, bg = "#34cfeb")
        user_pokemon_img_label.photo = user_pokemon_img
        user_pokemon_img_label.pack()

        opp_pokemon_img = ImageTk.PhotoImage(Image.open(opp_pokemon_img_path).convert("RGBA"))
        opp_pokemon_img_label = tk.Label(move_subframer, image = opp_pokemon_img, bg = "#34cfeb")
        opp_pokemon_img_label.photo = opp_pokemon_img
        opp_pokemon_img_label.pack()

        move_subframel.pack(side=tk.LEFT, padx = 40)
        move_subframer.pack(side=tk.RIGHT, padx = 40)
        move_subframe.pack(pady=30)

        change_button = tk.Button(move_frame, text="Change PokEEmon", command = self.choose_screen, height = 1, width = 18, bg="#ffcc03", font=f)
        change_button.pack(pady=5)
        quit_button = tk.Button(move_frame, text="Quit", command = self.quit, height = 1, width = 18, bg="#ffcc03", font=f)
        quit_button.pack(pady=5)


        move_frame.pack()
        self.curr_frame = move_frame

    def choose_screen(self):
        winsound.PlaySound('sounds/click.wav', winsound.SND_FILENAME | winsound.SND_ASYNC)
        if self.curr_frame:
            self.curr_frame.pack_forget()

        f = tk.font.Font(size=30)

        prev_move_frame = self.curr_frame

        if self.stop_listening is not None:
            self.stop_listening(wait_for_stop=False)
            self.stop_listening = None

        choose_frame = tk.Frame(self.window, bg = "#34cfeb")
        img = ImageTk.PhotoImage(Image.open("images/choose_pokemon_img.png"))
        choose_label = tk.Label(choose_frame, image = img, bg = "#34cfeb")
        choose_label.photo = img
        choose_label.pack()
        user_pokemon = self.user.team_df.loc[:,["name","curr_hp"]]
        for row in user_pokemon.itertuples():
            if row.curr_hp > 0:
                pokemon_button = tk.Button(choose_frame, text="{} | HP : {}".format(row.name.capitalize(), row.curr_hp), command = partial(self.sel_pokemon, row.Index, prev_move_frame), height = 1, width = 25, bg="#ffcc03", font=f)
                pokemon_button.pack(pady=5)
        choose_frame.pack()
        self.curr_frame = choose_frame

    def see_screen(self):
        winsound.PlaySound('sounds/click.wav', winsound.SND_FILENAME | winsound.SND_ASYNC)
        if self.curr_frame:
            self.curr_frame.destroy()

        f = tk.font.Font(size=30)

        see_frame = tk.Frame(self.window, bg = "#34cfeb")
        img = ImageTk.PhotoImage(Image.open("images/your_team_img.png")) #TODO: replace with "Your Team"
        choose_label = tk.Label(see_frame, image = img, bg = "#34cfeb")
        choose_label.photo = img
        choose_label.pack()
        user_pokemon = self.user.team_df.loc[:,["name","xp_accumulated"]]
        for row in user_pokemon.itertuples():
            pokemon_label = tk.Label(see_frame, text="{} | XP : {}".format(row.name.capitalize(), row.xp_accumulated), height = 2, bg = "#34cfeb", font=f)
            pokemon_label.pack(pady=10)

        home_button = tk.Button(see_frame, text="Home", command = partial(self.home, see_frame), height = 2, width = 18, bg="#ffcc03",font=f)
        home_button.pack(pady=5)
        see_frame.pack()
        self.curr_frame = see_frame

    def add_screen(self):
        if self.user.team_df.shape[0] < 6:
            self.opp_user.team_df.drop('curr_hp', axis=1, inplace=True)
            self.user.team_df = pd.concat([self.user.team_df, self.opp_user.team_df], ignore_index = True)
            print("Writing updated team to {}".format(self.user.path + "/team.csv"))
            print(self.user.team_df)
            self.user.team_df.to_csv(self.user.path + "/team.csv", index=False, quoting=csv.QUOTE_NONNUMERIC)
            self.see_screen()
            return

        winsound.PlaySound('sounds/click.wav', winsound.SND_FILENAME | winsound.SND_ASYNC)
        if self.curr_frame:
            self.curr_frame.destroy()

        f = tk.font.Font(size=30)

        add_frame = tk.Frame(self.window, bg = "#34cfeb")
        img = ImageTk.PhotoImage(Image.open("images/discard_pokeemon_img.png")) #TODO: replace with "Discard PokEEmon"
        choose_label = tk.Label(add_frame, image = img, bg = "#34cfeb")
        choose_label.photo = img
        choose_label.pack()
        user_pokemon = self.user.team_df.loc[:,["name","xp_accumulated"]]
        for i in range(self.user.team_df.shape[0]):
            pokemon_button = tk.Button(add_frame, text="{} | XP : {}".format(self.user.team_df.iloc[i]["name"].capitalize(), self.user.team_df.iloc[i]["xp_accumulated"]), command = partial(self.replace_pk, i), height = 1, width = 25, bg="#ffcc03", font=f)
            pokemon_button.pack(pady=5)

        back_button = tk.Button(add_frame, text="Back", command = partial(self.gameover_screen, True, True), height = 2, width = 18, bg="#ffcc03",font=f)
        back_button.pack(pady=10)

        add_frame.pack()
        self.curr_frame = add_frame

    def replace_pk(self, i):
        self.opp_user.team_df.drop('curr_hp', axis=1, inplace=True)
        self.user.team_df.loc[i,:] = self.opp_user.team_df.iloc[0,:].values
        print("Writing updated team to {}".format(self.user.path + "/team.csv"))
        print(self.user.team_df)
        self.user.team_df.to_csv(self.user.path + "/team.csv", index=False, quoting=csv.QUOTE_NONNUMERIC)
        self.see_screen()
