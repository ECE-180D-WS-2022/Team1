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

#os.system("start click.wav")
################################# SETUP ########################################################################
##### Command line interface to pass in name #####
parser = argparse.ArgumentParser(
    description="Start the game by typing ./pokEEmon.py <username> <id>"
)

movedamage = {"Thunderbolt" : 5, "Tackle" : 10, "Ice" : 2, "Flamethrower" : 6}
movegesture = {"Thunderbolt" : "slash", "Tackle" : "block", "Ice" : "whip", "Flamethrower" : "scratch"}

parser.add_argument("username", type=str, help="your in-game username")
parser.add_argument("id", type=str, help="your pi id")
args = parser.parse_args()
print("Welcome " + args.username)

class Battle:
    def __init__(self, user, battle_id, opp_user, window, client, home, id):
        self.user = copy.deepcopy(user)
        self.battle_id = battle_id
        self.opp_user = copy.deepcopy(opp_user)
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
        print("Received move message")
        msg = message.payload
        print(msg)

        msg = str(msg.decode()).split(",")
        print(msg)

        if msg and msg[0] == "move" and int(msg[2]) == self.battle_id:
            movename = msg[3]
            pokeemon_name = self.opp_user.team_df.iloc[self.opp_pokemon, self.opp_user.team_df.columns.get_loc("name")]
            #TODO get damage
            damage = movedamage[movename]
            hp = self.user.team_df.iloc[self.curr_pokemon, self.user.team_df.columns.get_loc("hp")]
            hp -= damage
            if hp < 0:
                hp = 0
            self.user.team_df.iloc[self.curr_pokemon, self.user.team_df.columns.get_loc("hp")] = hp
            if  self.user.team_df[self.user.team_df["hp"] > 0].empty:
                print("You lost")
                self.home(self.wait_frame)
            else:
                self.move_screen(self.wait_frame, "{}'s {} played {}".format(self.opp_user.username.capitalize(), pokeemon_name, movename))
        elif msg and msg[0] == "change" and int(msg[2]) == self.battle_id:
            self.opp_pokemon = int(msg[3])
            self.wait_screen(self.wait_frame)
        else:
            print("Received unexpected message")

    def voice_callback(self, recognizer, audio):
        try:
            words = recognizer.recognize_google(audio)
            print("Heard: " + words)
            for move in ["move1", "move2", "move3", "move4"]:
                if self.user.team_df.iloc[self.curr_pokemon][move].lower() in words.lower():
                    self.gesture_screen(move)
                    return

            print("Not a move")
        except sr.UnknownValueError:
            print("Google Speech Recognition could not understand audio")
        except sr.RequestError as e:
            print("Could not request results from Google Speech Recognition service; {0}".format(e))

    def sel_pokemon(self, index):
        self.curr_pokemon = index
        choose_msg = "change,{},{},{}".format(self.user.username, self.battle_id, index)
        self.client.publish("ece180d/pokEEmon/" + self.opp_user.username + "/change", choose_msg)
        self.move_screen(self.choose_frame)

    def do_move(self):
        #TODO get damage
        winsound.PlaySound('whoosh.wav', winsound.SND_FILENAME | winsound.SND_ASYNC)
        damage = movedamage[self.movename]
        opp_hp = self.opp_user.team_df.iloc[self.opp_pokemon, self.opp_user.team_df.columns.get_loc("hp")]
        opp_hp -= damage
        if opp_hp < 0:
            opp_hp = 0
        self.opp_user.team_df.iloc[self.opp_pokemon, self.opp_user.team_df.columns.get_loc("hp")] = opp_hp
        move_msg = "move,{},{},{}".format(self.user.username, self.battle_id, self.movename)
        self.client.publish("ece180d/pokEEmon/" + self.opp_user.username + "/move", move_msg)
        if self.opp_user.team_df[self.opp_user.team_df["hp"] > 0].empty:
            print("You won!")
            self.home(self.gesture_frame)
        else:
            self.wait_screen(self.gesture_frame)

    def gesture_screen(self, move):
        print("Waiting for gesture")
        winsound.PlaySound('click.wav', winsound.SND_FILENAME | winsound.SND_ASYNC)
        if self.move_frame:
            self.move_frame.pack_forget()
        if self.gesture_frame:
            self.gesture_frame.destroy()

        if self.stop_listening:
            self.stop_listening(wait_for_stop=False)
            self.stop_listening = None

        self.movename = self.user.team_df.iloc[self.curr_pokemon][move]

        self.client.on_message = self.rcv_gesture_mqtt
        self.client.subscribe("ece180d/pokEEmon/" + self.id, qos=1)
        print("Subscribed to " + "ece180d/pokEEmon/" + self.id)

        self.gesture_frame = tk.Frame(self.window)
        gesture_label = tk.Label(self.gesture_frame, text="Do a {} ".format(movegesture[self.movename]))
        back_button = tk.Button(self.gesture_frame, text="Back", command = partial(self.move_screen, self.gesture_frame))
        gesture_label.pack()
        back_button.pack()

        self.gesture_frame.pack()

    def wait_screen(self, prev_frame = None):
        print("Waiting for opponent move")
        if prev_frame:
            prev_frame.pack_forget()
        if self.wait_frame:
            self.wait_frame.destroy()

        self.client.on_message = self.rcv_battle_mqtt
        self.client.unsubscribe("ece180d/pokEEmon/" + self.id)
        self.client.subscribe("ece180d/pokEEmon/" + self.user.username + "/move", qos=1)
        self.client.subscribe("ece180d/pokEEmon/" + self.user.username + "/change", qos=1)
        self.client.unsubscribe("ece180d/pokEEmon/" + self.id)
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

    def move_screen(self, prev_frame = None, move_update = None):
        print("Choose your move")
        winsound.PlaySound('click.wav', winsound.SND_FILENAME | winsound.SND_ASYNC)
        if prev_frame:
            prev_frame.pack_forget()
        if self.move_frame:
            self.move_frame.destroy()

        #TODO check for cancel
        self.client.unsubscribe("ece180d/pokEEmon/" + self.id)
        self.client.unsubscribe("ece180d/pokEEmon/" + self.user.username + "/move")
        self.client.unsubscribe("ece180d/pokEEmon/" + self.user.username + "/change")
        print("Unsubscribed to " + "ece180d/pokEEmon/" + self.id)
        print("Unsubscribed to " + "ece180d/pokEEmon/" + self.user.username + "/move")
        print("Unsubscribed to " + "ece180d/pokEEmon/" + self.user.username + "/change")

        self.move_frame = tk.Frame(self.window)

        if move_update:
            update_label = tk.Label(self.move_frame, text=move_update)
            update_label.pack()

        if self.user.team_df.iloc[self.curr_pokemon, self.user.team_df.columns.get_loc("hp")] > 0:
            move_label = tk.Label(self.move_frame, text="Choose your move")
            move1_button = tk.Button(self.move_frame, text=self.user.team_df.iloc[self.curr_pokemon]["move1"], command = partial(self.gesture_screen, "move1"))
            move2_button = tk.Button(self.move_frame, text=self.user.team_df.iloc[self.curr_pokemon]["move2"], command = partial(self.gesture_screen, "move2"))
            move3_button = tk.Button(self.move_frame, text=self.user.team_df.iloc[self.curr_pokemon]["move3"], command = partial(self.gesture_screen, "move3"))
            move4_button = tk.Button(self.move_frame, text=self.user.team_df.iloc[self.curr_pokemon]["move4"], command = partial(self.gesture_screen, "move4"))
            move_label.pack()
            move1_button.pack()
            move2_button.pack()
            move3_button.pack()
            move4_button.pack()
        else:
            change_label = tk.Label(self.move_frame, text="Change your pokemon")
            change_label.pack()

        user_pokemon_name = self.user.team_df.iloc[self.curr_pokemon, self.user.team_df.columns.get_loc("name")]
        userteam_string = self.user.team_df.loc[:, ["name", "hp"]].to_string(index=False)
        userteam_string = userteam_string.replace(user_pokemon_name, "**" + user_pokemon_name)
        userteam_label = tk.Label(self.move_frame, text="\nYour team: \n{}\n".format(userteam_string))
        opp_pokemon_name = self.opp_user.team_df.iloc[self.opp_pokemon, self.opp_user.team_df.columns.get_loc("name")]
        oppteam_string = self.opp_user.team_df.loc[:, ["name", "hp"]].to_string(index=False)
        oppteam_string = oppteam_string.replace(opp_pokemon_name, "**" + opp_pokemon_name)
        oppteam_label = tk.Label(self.move_frame, text="\nOpponent team: \n{}\n".format(oppteam_string))
        change_button = tk.Button(self.move_frame, text="Change pokEEmon", command = self.choose_screen)
        userteam_label.pack()
        oppteam_label.pack()
        change_button.pack()

        self.move_frame.pack()


        self.mic = sr.Microphone()
        self.rec = sr.Recognizer()
        with self.mic as source:
            self.rec.adjust_for_ambient_noise(source)

        self.stop_listening = self.rec.listen_in_background(self.mic, self.voice_callback, 3)


    def choose_screen(self, prev_frame = None):
        winsound.PlaySound('click.wav', winsound.SND_FILENAME | winsound.SND_ASYNC)
        if self.move_frame:
            self.move_frame.pack_forget()
        if self.choose_frame:
            self.choose_frame.destroy()
        if self.stop_listening:
            self.stop_listening(wait_for_stop=False)
            self.stop_listening = None

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
            all_pokemon_df = pd.read_csv("data/pokemon.csv")
            gamestats_df = pd.read_csv(self.path + "/gamestats.csv")
            team_df = pd.read_csv(self.path + "/team.csv")
            team_df = team_df.append(all_pokemon_df.iloc[[random.randrange(0,799)]], ignore_index=True)
            team_df = team_df.append(all_pokemon_df.iloc[[random.randrange(0,799)]], ignore_index=True)
            print(team_df)
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
                b = Battle(self.user, self.request_num, self.opp_user, self.window, self.client, self.home_screen, self.id)
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
        self.client.unsubscribe("ece180d/pokEEmon/" + self.id)
        self.client.subscribe("ece180d/pokEEmon/" + self.user.username + "/request", qos=1)
        print("Subscribed to " + "ece180d/pokEEmon/" + self.user.username + "/request")
        print("Unsubscribed to " + "ece180d/pokEEmon/" + self.id)

        if not self.window:
            self.window = tk.Tk()
            self.window.attributes('-fullscreen',True)
        else:
            winsound.PlaySound('click.wav', winsound.SND_FILENAME | winsound.SND_ASYNC)
        if not self.home_frame:
            self.home_frame = tk.Frame(self.window)
            battle_button = tk.Button(self.home_frame, text = "Battle", command = partial(self.request_screen, self.home_frame))
            train_button = tk.Button(self.home_frame, text = "Train", command = partial(self.train_screen_begin, self.home_frame))
            exit_button = tk.Button(self.home_frame, text = "Exit", command = self.exit_game)
            battle_button.pack()
            train_button.pack()
            exit_button.pack()

        self.home_frame.pack()

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
        winsound.PlaySound('click.wav', winsound.SND_FILENAME | winsound.SND_ASYNC)

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
        winsound.PlaySound('click.wav', winsound.SND_FILENAME | winsound.SND_ASYNC)
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
        Giving choices for pokemon to train
        '''
        print("Training screen Beginning")
        if prev_screen:
            prev_screen.pack_forget()
        if camera:
            camera.release()

        if not self.train_frame_begin:
            self.train_frame_begin = tk.Frame(self.window)
            tk.Label(self.train_frame_begin, text="Choose Pokemon").pack()
            pokemon_list = self.user.team_df["name"].tolist()
            for pokemon_name in pokemon_list:
                tk.Button(self.train_frame_begin, text = pokemon_name, command = partial(self.train_screen, pokemon_name)).pack()
            # tk.Button(self.train_frame_ begin, text="Finish Training", command = partial(self.set_pokemon, "poopoopeepee")).pack()
            tk.Button(self.train_frame_begin, text = "Back", command = partial(self.home_screen, self.train_frame_begin)).pack()
        self.train_frame_begin.pack()

    def train_screen(self, working_pokemon):
        winsound.PlaySound('click.wav', winsound.SND_FILENAME | winsound.SND_ASYNC)
        '''
        Training that starts after pokemon is selected
        '''
        cap = cv2.VideoCapture(0)
        self.working_pokemen = working_pokemon
        self.train_frame_begin.pack_forget()
        if self.train_frame:
            self.train_frame.destroy()
        self.train_frame = tk.Frame(self.window)
        self.train_frame.pack()

        tk.Button(self.train_frame, text="Switch Pokemon", command = partial(self.train_screen_begin, self.train_frame, cap)).pack()

        self.desired_pose = self.choose_pose()

        desired_pose_label = tk.Label(self.train_frame)
        desired_pose_label.config(text = f"Match the pose of: {self.desired_pose}")
        desired_pose_label.pack()
        #Initializing mediapipe pose class.
        mp_pose = mp.solutions.pose
        #Setting up the Pose function.
        #pose = mp_pose.Pose(static_image_mode=True, min_detection_confidence=0.3, model_complexity=2)
        #Initializing mediapipe drawing class, useful for annotation.
        mp_drawing = mp.solutions.drawing_utils

        #create label for cv image feed
        label = tk.Label(self.train_frame)
        #create label for pose reference image
        ref_img_label = tk.Label(self.train_frame)

        pose_video = mp_pose.Pose(static_image_mode=False, min_detection_confidence=0.5, model_complexity=1)

        #reference image switch statement
        def pull_image(chosen_pose):
            if (chosen_pose == "Warrior Pose"):
                return "warrior2.png"
            if (chosen_pose == "T Pose"):
                return "tpose.png"
            if (chosen_pose == "Tree Pose"):
                return "tree.jpg"
            else:
                return "error.jpg"

        def show_frames():
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
                    self.user.team_df.loc[self.user.team_df.name == self.working_pokemon, "xp_accumulated"] += 20
                    self.desired_pose = self.choose_pose()
                    desired_pose_label.config(text = f"Match the pose of: {self.desired_pose}")

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
        b = Battle(self.user, self.request_num, self.opp_user, self.window, self.client, self.home_screen, self.id)
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
        winsound.PlaySound('click.wav', winsound.SND_FILENAME)
        self.user.gamestats_df.to_csv(self.user.path + "/gamestats.csv", index = False, quoting=csv.QUOTE_NONNUMERIC)
        self.user.team_df.to_csv(self.user.path + "/team.csv", index=False, quoting=csv.QUOTE_NONNUMERIC)
        self.window.destroy()


game = Game(args.username, args.id)
game.connect_mqtt()
game.home_screen()
game.start_game()
