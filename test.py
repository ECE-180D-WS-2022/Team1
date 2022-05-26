import tkinter as tk
from PIL import Image, ImageTk
from pygame import mixer

win = tk.Tk()
win.configure(bg="#34cfeb")
frame = tk.Frame(win, bg = "#34cfeb")
im = Image.open("sprites/25.png")
photoimage = ImageTk.PhotoImage(im.convert("RGBA"))
canvas = tk.Canvas(frame, bg = "#34cfeb", width=photoimage.width(), height=photoimage.height())
canvas.pack()
canvas.create_image(0,0, image=photoimage, anchor=tk.NW)
frame.pack()
print("Hello")
mixer.init()
mixer.music.load("menu music.mp3")
mixer.music.play(-1)
win.mainloop()
