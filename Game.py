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
import Battle as bt
import User as usr
import PkUtils as ut


class Game:
    def __init__(self, username, id):
        self.learnset = ut.import_learnset()
        self.user = usr.User(self.learnset, username)
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
        if self.connected:
            return
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
            self.opp_user = usr.User(self.learnset)
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
                self.opp_user = usr.User(self.learnset)
                self.opp_user.username = msg[1]
                self.opp_user.team_df = pd.read_csv(io.StringIO(msg[4]), sep='\s+')
                self.battle = bt.Battle(self.user, self.request_num, self.opp_user, self.window, self.client, self.home_screen, self.id, self.learnset)
                self.response_frame.pack_forget()
                self.battle.wait_screen()
            else:
                print("Battle declined by: " + msg[1])
                self.client.unsubscribe("ece180d/pokEEmon/" + self.user.username + "/response")
                self.request_screen(self.response_frame)
        else:
            print("Received unexpected message")


    def home_screen(self, prev_frame = None):
        print("Home screen")

        if not mixer.get_init():
            mixer.init()

        if not mixer.music.get_busy():
            mixer.music.load("sounds/menu music.mp3")
            mixer.music.set_volume(0.25)
            mixer.music.play(-1)

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
            winsound.PlaySound('sounds/click.wav', winsound.SND_FILENAME | winsound.SND_ASYNC)
        if not self.home_frame:
            self.home_frame = tk.Frame(self.window, bg = "#34cfeb")
            img = ImageTk.PhotoImage(Image.open("images/logo.png"))

            photo_label = tk.Label(self.home_frame, image = img, bg = "#34cfeb")
            photo_label.photo = img
            f = tkfont.Font(size=40)
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
        winsound.PlaySound('sounds/click.wav', winsound.SND_FILENAME | winsound.SND_ASYNC)

        if prev_screen:
            prev_screen.pack_forget()

        self.client.unsubscribe("ece180d/pokEEmon/" + self.user.username + "/request")
        print("Unsubscribed from " + "ece180d/pokEEmon/" + self.user.username + "/request")

        tutorial_frame = tk.Frame(self.window, bg = "#34cfeb")
        mode_img =  ImageTk.PhotoImage(Image.open("images/tutorial_img.png"))
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


        mixer.music.stop()

        os.startfile("tutorial.mp4")

    def choose_opp_screen(self, prev_screen = None):
        print("Choose opp screen")
        winsound.PlaySound('sounds/click.wav', winsound.SND_FILENAME | winsound.SND_ASYNC)

        if prev_screen:
            prev_screen.pack_forget()

        self.client.unsubscribe("ece180d/pokEEmon/" + self.user.username + "/request")
        print("Unsubscribed from " + "ece180d/pokEEmon/" + self.user.username + "/request")

        if not self.choose_opp_frame:
            self.choose_opp_frame = tk.Frame(self.window, bg = "#34cfeb")
            mode_img =  ImageTk.PhotoImage(Image.open("images/choose_battle_mode_img.png"))
            mode_label = tk.Label(self.choose_opp_frame, image=mode_img, bg = "#34cfeb")
            mode_label.photo = mode_img
            f = tk.font.Font(size=30)
            single_button = tk.Button(self.choose_opp_frame, text = "Single-player", command = partial(self.single_battle, self.choose_opp_frame), height = 2, width = 15, bg="#ffcc03", font=f)
            multi_button = tk.Button(self.choose_opp_frame, text = "Multi-player", command = partial(self.request_screen, self.choose_opp_frame), height = 2, width = 15, bg="#ffcc03", font=f)
            back_button = tk.Button(self.choose_opp_frame, text = "Back", command = partial(self.home_screen, self.choose_opp_frame), height = 2, width = 15, bg="#ffcc03", font=f)

            mode_label.pack(pady=10)
            single_button.pack(pady=10)
            multi_button.pack(pady=10)
            back_button.pack(pady=10)

        self.choose_opp_frame.pack()

    def receive_screen(self, opp_username):
        print("Receive screen")
        winsound.PlaySound('sounds/click.wav', winsound.SND_FILENAME | winsound.SND_ASYNC)
        self.home_frame.pack_forget()
        if self.receive_frame:
            self.receive_frame.destroy()

        self.client.unsubscribe("ece180d/pokEEmon/" + self.user.username + "/request")
        self.client.on_message = self.rcv_cancel_mqtt
        self.client.subscribe("ece180d/pokEEmon/" + self.user.username + "/cancel")
        print("Unsubscribed from " + "ece180d/pokEEmon/" + self.user.username + "/request")
        print("Subscribed to " + "ece180d/pokEEmon/" + self.user.username + "/cancel")

        self.receive_frame = tk.Frame(self.window, bg = "#34cfeb")

        img = ImageTk.PhotoImage(Image.open("images/battle_img.png"))
        receive_photo_label = tk.Label(self.receive_frame, image = img, bg = "#34cfeb")
        receive_photo_label.photo = img

        f = tk.font.Font(size=30)
        receive_label = tk.Label(self.receive_frame, text=opp_username, font=("Arial", 50), bg = "#34cfeb")
        accept_button = tk.Button(self.receive_frame, text = "Accept", command = partial(self.accept_request, opp_username), height = 2, width = 15, bg="#ffcc03", font=f)
        decline_button = tk.Button(self.receive_frame, text = "Decline", command = partial(self.decline_request, opp_username), height = 2, width = 15, bg="#ffcc03", font=f)
        receive_photo_label.pack(pady=10)
        receive_label.pack(pady=15)
        accept_button.pack(pady=10)
        decline_button.pack(pady=10)

        self.receive_frame.pack()

    def request_screen(self, prev_screen = None):
        print("Request screen")
        winsound.PlaySound('sounds/click.wav', winsound.SND_FILENAME | winsound.SND_ASYNC)

        if prev_screen:
            prev_screen.pack_forget()
        if self.request_frame:
            self.request_frame.destroy()

        self.client.unsubscribe("ece180d/pokEEmon/" + self.user.username + "/response")
        print("Unsubscribed from " + "ece180d/pokEEmon/" + self.user.username + "/response")

        f = tk.font.Font(size=30)
        self.request_frame = tk.Frame(self.window, bg = "#34cfeb")
        request_img = ImageTk.PhotoImage(Image.open("images/request_img.png"))
        request_label = tk.Label(self.request_frame, image=request_img, bg = "#34cfeb")
        request_label.photo = request_img
        username_entry = tk.Entry(self.request_frame, font=("default", 16))
        submit_button = tk.Button(self.request_frame, text = "Submit", command = partial(self.make_request, username_entry), height = 2, width = 15, bg="#ffcc03", font=f)
        back_button = tk.Button(self.request_frame, text = "Back", command = partial(self.choose_opp_screen, self.request_frame), height = 2, width = 15, bg="#ffcc03", font=f)
        request_label.pack(pady=10)
        username_entry.pack(pady=10)
        submit_button.pack(pady=10)
        back_button.pack(pady=10)

        self.request_frame.pack()


    def response_screen(self, opp_username):
        winsound.PlaySound('sounds/click.wav', winsound.SND_FILENAME | winsound.SND_ASYNC)
        print("Response screen")
        self.request_frame.pack_forget()
        if self.response_frame:
            self.response_frame.destroy()


        self.client.on_message = self.rcv_response_mqtt
        self.client.subscribe("ece180d/pokEEmon/" + self.user.username + "/response")
        print("Subscribed to " + "ece180d/pokEEmon/" + self.user.username + "/response")

        f = tk.font.Font(size=30)
        self.response_frame = tk.Frame(self.window, bg = "#34cfeb")
        waiting_img = ImageTk.PhotoImage(Image.open("images/waiting_img.png"))
        waiting_label = tk.Label(self.response_frame, image=waiting_img, bg = "#34cfeb")
        waiting_label.photo = waiting_img
        request_label = tk.Label(self.response_frame, text=opp_username, font=("Arial", 25), bg= "#34cfeb")
        cancel_button = tk.Button(self.response_frame, text = "Cancel", command = partial(self.cancel_request, opp_username), height = 2, width = 15, bg="#ffcc03", font=f)
        waiting_label.pack(pady=10)
        request_label.pack(pady=10)
        cancel_button.pack(pady=10)

        self.response_frame.pack()

    def single_battle(self, prev_screen = None):
        print("Starting Single-player battle")
        winsound.PlaySound('sounds/click.wav', winsound.SND_FILENAME | winsound.SND_ASYNC)

        if prev_screen:
            prev_screen.pack_forget()

        self.opp_user = usr.User(self.learnset)
        self.opp_user.username = "Bot"
        basepk_df = pd.read_csv("data/new_pokemon_withMoves.csv")
        num_pk = random.randint(1, 6)
        self.opp_user.team_df = basepk_df.sample(n = num_pk)
        self.opp_user.team_df.reset_index(drop=True, inplace=True)

        total_xp = sum(self.user.team_df["xp_accumulated"].values)

        if num_pk == 1:
            xp_boost = max(0, random.randint(total_xp // self.user.team_df.shape[0] - 1000, total_xp // self.user.team_df.shape[0] + 2000))
            self.opp_user.team_df.loc[0] = ut.bot_level_up(self.opp_user.team_df.loc[0], xp_boost, self.learnset)
        else:
            for i in range(self.opp_user.team_df.shape[0]):
                xp_boost = max(0, random.randint(total_xp // num_pk - 2000, total_xp // num_pk + 1000))
                self.opp_user.team_df.loc[i] = ut.bot_level_up(self.opp_user.team_df.loc[i], xp_boost, self.learnset)

        print("Generated opponent team:")
        print(self.opp_user.team_df)


        self.battle = bt.Battle(self.user, None, self.opp_user, self.window, self.client, self.home_screen, self.id, self.learnset, True)
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
        winsound.PlaySound('sounds/click.wav', winsound.SND_FILENAME | winsound.SND_ASYNC)
        '''
        Creates the screen that gives choices for pokemon to train
        '''
        print("Training screen Beginning")
        if prev_screen:
            prev_screen.pack_forget()
        if camera:
            camera.release()
            mixer.music.stop()
            mixer.music.load("sounds/menu music.mp3")
            mixer.music.set_volume(0.25)
            mixer.music.play(-1)

        if not self.train_frame_begin:
            f = tk.font.Font(size=30)
            self.train_frame_begin = tk.Frame(self.window, bg = "#34cfeb")
            choose_img =  ImageTk.PhotoImage(Image.open("images/choose_img.png"))
            choose_label = tk.Label(self.train_frame_begin, image=choose_img, bg = "#34cfeb")
            choose_label.photo = choose_img
            pokemon_list = self.user.team_df["name"].tolist()
            choose_label.pack(pady=10)
            for pokemon_name in pokemon_list:
                tk.Button(self.train_frame_begin, text = pokemon_name.capitalize(), command = partial(self.train_screen, pokemon_name), height = 2, width = 15, bg="#ffcc03", font=f).pack(pady=10)
            tk.Button(self.train_frame_begin, text = "Back", command = partial(self.home_screen, self.train_frame_begin), height = 2, width = 15, bg="#ffcc03", font = f).pack(pady=10)
        self.train_frame_begin.pack()

    def train_screen(self, pokemon_name):
        winsound.PlaySound('sounds/click.wav', winsound.SND_FILENAME | winsound.SND_ASYNC)
        '''
        Training that starts after pokemon is selected through having 2 windows,
        one of the camera and one of the pose to be matched.
        '''
        mixer.music.stop()
        mixer.music.load("sounds/train music.mp3")
        mixer.music.set_volume(0.25)
        mixer.music.play(-1)

        cap = cv2.VideoCapture(0)
        self.working_pokemon = pokemon_name
        self.train_frame_begin.pack_forget()
        if self.train_frame:
            self.train_frame.destroy()
        self.train_frame = tk.Frame(self.window, bg = "#34cfeb")
        self.train_frame.pack()

        tk.Button(self.train_frame, text="Switch Pokemon", command = partial(self.train_screen_begin, self.train_frame, cap), height = 1, width = 18, bg="#ffcc03", font=("Arial", 30)).pack(pady=10)

        self.desired_pose = self.choose_pose()

        xp_label = tk.Label(self.train_frame, bg = "#34cfeb")
        xp = self.user.team_df.loc[self.user.team_df["name"]==pokemon_name, "xp_accumulated"].values[0]
        xp_label.config(text=f"Current XP of {pokemon_name.capitalize()}: {xp}", font=("Arial", 25))
        xp_label.pack()

        desired_pose_label = tk.Label(self.train_frame, bg = "#34cfeb")
        desired_pose_label.config(text = f"Match the pose of: {self.desired_pose}", font=("Arial", 25))
        desired_pose_label.pack()

        ## Adding sprites
        user_pokemon_id = self.user.team_df.loc[self.user.team_df["name"]==self.working_pokemon,"id"].item()
        if os.path.isfile("sprites/"+str(user_pokemon_id)+".png"):
            user_pokemon_img_path = "sprites/"+str(user_pokemon_id)+".png"
        else:
            user_pokemon_img_path = "sprites/1.png"
        user_pokemon_img = ImageTk.PhotoImage(Image.open(user_pokemon_img_path).convert("RGBA"))
        user_pokemon_img_label = tk.Label(self.train_frame, image = user_pokemon_img, bg = "#34cfeb")
        user_pokemon_img_label.photo = user_pokemon_img
        user_pokemon_img_label.pack()

        #Initializing mediapipe pose class.
        mp_pose = mp.solutions.pose
        #Setting up the Pose function.
        #Initializing mediapipe drawing class, useful for annotation.
        mp_drawing = mp.solutions.drawing_utils

        #create label for cv image feed
        label = tk.Label(self.train_frame)
        #create label for pose reference image
        ref_img_label = tk.Label(self.train_frame, bg = "#34cfeb")

        pose_video = mp_pose.Pose(static_image_mode=False, min_detection_confidence=0.5, model_complexity=1)

        #reference image switch statement
        def pull_image(chosen_pose):
            '''
            pulls the referenced image to show as the pose to match
            '''
            if (chosen_pose == "Warrior Pose"):
                return "images/warrior2.png"
            if (chosen_pose == "T Pose"):
                return "images/tpose.png"
            if (chosen_pose == "Tree Pose"):
                return "images/tree.jpg"

            return "images/tree.jpg"

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
                    i = self.user.team_df.index[self.user.team_df["name"] == self.working_pokemon].item()
                    self.user.team_df.loc[i] = ut.level_up(self.user.team_df.loc[i], 20, self.learnset)

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
        self.battle = bt.Battle(self.user, self.request_num, self.opp_user, self.window, self.client, self.home_screen, self.id, self.learnset)
        self.receive_frame.pack_forget()
        self.battle.move_screen()

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
        winsound.PlaySound('sounds/click.wav', winsound.SND_FILENAME)
        self.window.destroy()
