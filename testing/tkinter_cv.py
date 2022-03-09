import tkinter
import cv2
import PIL.Image, PIL.ImageTk
import time
import math
import numpy as np
import mediapipe as mp
import matplotlib.pyplot as plt


class App:
     def __init__(self, window, window_title, video_source=0):
         self.window = window
         self.window.title(window_title)
         self.video_source = video_source

         # open video source (by default this will try to open the computer webcam)
         self.vid = MyVideoCapture(self.video_source)

         # Create a canvas that can fit the above video source size
         self.canvas = tkinter.Canvas(window, width = self.vid.width, height = self.vid.height)
         self.canvas.pack()

         # Button that lets the user take a snapshot
         self.btn_snapshot=tkinter.Button(window, text="Snapshot", width=50, command=self.snapshot)
         self.btn_snapshot.pack(anchor=tkinter.CENTER, expand=True)

         # After it is called once, the update method will be automatically called every delay milliseconds
         self.update()

         self.window.mainloop()

     def snapshot(self):
         # Get a frame from the video source
         ret, frame = self.vid.get_frame()

         if ret:
             cv2.imwrite("frame-" + time.strftime("%d-%m-%Y-%H-%M-%S") + ".jpg", cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))

     def update(self):
         # Get a frame from the video source
         ret, frame = self.vid.get_frame()

         if ret:
             self.photo = PIL.ImageTk.PhotoImage(image = PIL.Image.fromarray(frame))
             self.canvas.create_image(0, 0, image = self.photo, anchor = tkinter.NW)

         self.window.after(self.delay, self.update)


class MyVideoCapture:
     def __init__(self, video_source=0):
         #initialize mediapipe pose and functions
         self.mp_pose = mp.solutions.pose
         self.pose = self.mp_pose.Pose(static_image_mode = True, min_detection_confidence=0.3, model_complexity=2)
         self.mp_drawing = mp.solutions.drawing_utils

         # Open the video source
         self.vid = cv2.VideoCapture(video_source)
         if not self.vid.isOpened():
             raise ValueError("Unable to open video source", video_source)

         # Get video source width and height
         self.width = self.vid.get(cv2.CAP_PROP_FRAME_WIDTH)
         self.height = self.vid.get(cv2.CAP_PROP_FRAME_HEIGHT)

     def get_frame(self):
         pose_video = self.mp_pose.Pose(static_image_mode=False, min_detection_confidence=0.5, model_complexity=1)
         if self.vid.isOpened():
             ret, frame = self.vid.read()
             if ret:
                 # send back success and frame
                 frame = cv2.flip(frame, 1)
                 self.height, self.width, _ = frame.shape
                 frame, landmarks = self.detectPose(frame, pose_video, display=False)
                 if landmarks:
                     frame, _ = self.classifyPose(landmarks, frame, display=False)
                 return (ret, frame)
             else:
                 return (ret, None)
         else:
             return (ret, None)

     # Release the video source when the object is destroyed
     def __del__(self):
         if self.vid.isOpened():
             self.vid.release()

     def detectPose(self, image, pose, display=True):
         '''
         performs pose detection on an image.

             image: The input image
             pose: The pose setup function required to perform the pose detection.
             display: A boolean value that is if set to true the function displays the original input image, the resultant image,
                      and the pose landmarks in 3D plot and returns nothing.

             output_image: input image with the detected pose landmarks drawn.
             landmarks: list of detected landmarks converted into their original scale.
         '''

         #Create a copy of the input image.
         output_image = image.copy()

         #Convert the image from BGR into RGB format.
         imageRGB = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

         #Perform the Pose Detection.
         results = self.pose.process(imageRGB)

         #Retrieve the height and width of the input image.
         height, width, _ = image.shape

         #Initialize a list to store the detected landmarks.
         landmarks = []

         #Check if any landmarks are detected.
         if results.pose_landmarks:

             #Draw Pose landmarks on the output image.
             self.mp_drawing.draw_landmarks(image=output_image, landmark_list=results.pose_landmarks,
                                       connections=self.mp_pose.POSE_CONNECTIONS)

             #Iterate over the detected landmarks.
             for landmark in results.pose_landmarks.landmark:

                 #Append the landmark into the list.
                 landmarks.append((int(landmark.x * width), int(landmark.y * height),
                                       (landmark.z * width)))

         #Check if the original input image and the resultant image are specified to be displayed.
         if display:

             #Display the original input image and the resultant image.
             plt.figure(figsize=[22,22])
             plt.subplot(121);plt.imshow(image[:,:,::-1]);plt.title("Original Image");plt.axis('off');
             plt.subplot(122);plt.imshow(output_image[:,:,::-1]);plt.title("Output Image");plt.axis('off');

             #Also Plot the Pose landmarks in 3D.
             self.mp_drawing.plot_landmarks(results.pose_world_landmarks, self.mp_pose.POSE_CONNECTIONS)

         #Otherwise
         else:

             #Return the output image and the found landmarks.
             return output_image, landmarks


     def calculateAngle(self, landmark1, landmark2, landmark3):
         '''
             landmark1: The first landmark containing the x,y and z coordinates.
             landmark2: The second landmark containing the x,y and z coordinates.
             landmark3: The third landmark containing the x,y and z coordinates.
         Returns:
             angle: The calculated angle between the three landmarks.
         '''

         #Get the landmark coordinates.
         x1, y1, _ = landmark1
         x2, y2, _ = landmark2
         x3, y3, _ = landmark3

         #Calculate the angle between the three points
         angle = math.degrees(math.atan2(y3 - y2, x3 - x2) - math.atan2(y1 - y2, x1 - x2))

         #Check if the angle is less than zero.
         if angle < 0:

             #Add 360 to the found angle.
             angle += 360

         #Return the calculated angle.
         return angle


     def classifyPose(self, landmarks, output_image, display=False):
         '''
         function classifies yoga poses depending upon the angles of specific body joints.

             landmarks: list of detected landmarks of the person whose pose needs to be classified.
             output_image: image of the person with the detected pose landmarks drawn.
             display: boolean value that is if set to true the function displays the resultant image with the pose label
             written on it and returns nothing.
         Returns:
             output_image: image with the detected pose landmarks drawn and pose label written.
             label: classified pose label of the person in the output_image.
         '''

         #Initialize the label of the pose. It is not known at this stage.
         label = 'Unknown Pose'


         color = (0, 0, 255)         #red label for unknown pose

         #Calculate the required angles.


         #Get the angle between the left shoulder, elbow and wrist points.
         left_elbow_angle = self.calculateAngle(landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value],
                                           landmarks[self.mp_pose.PoseLandmark.LEFT_ELBOW.value],
                                           landmarks[self.mp_pose.PoseLandmark.LEFT_WRIST.value])

         #Get the angle between the right shoulder, elbow and wrist points.
         right_elbow_angle = self.calculateAngle(landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER.value],
                                            landmarks[self.mp_pose.PoseLandmark.RIGHT_ELBOW.value],
                                            landmarks[self.mp_pose.PoseLandmark.RIGHT_WRIST.value])

         #Get the angle between the left elbow, shoulder and hip points.
         left_shoulder_angle = self.calculateAngle(landmarks[self.mp_pose.PoseLandmark.LEFT_ELBOW.value],
                                              landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value],
                                              landmarks[self.mp_pose.PoseLandmark.LEFT_HIP.value])

         #Get the angle between the right hip, shoulder and elbow points.
         right_shoulder_angle = self.calculateAngle(landmarks[self.mp_pose.PoseLandmark.RIGHT_HIP.value],
                                               landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER.value],
                                               landmarks[self.mp_pose.PoseLandmark.RIGHT_ELBOW.value])

         #Get the angle between the left hip, knee and ankle points.
         left_knee_angle = self.calculateAngle(landmarks[self.mp_pose.PoseLandmark.LEFT_HIP.value],
                                          landmarks[self.mp_pose.PoseLandmark.LEFT_KNEE.value],
                                          landmarks[self.mp_pose.PoseLandmark.LEFT_ANKLE.value])

         #Get the angle between the right hip, knee and ankle points
         right_knee_angle = self.calculateAngle(landmarks[self.mp_pose.PoseLandmark.RIGHT_HIP.value],
                                           landmarks[self.mp_pose.PoseLandmark.RIGHT_KNEE.value],
                                           landmarks[self.mp_pose.PoseLandmark.RIGHT_ANKLE.value])



         #Check if it is the warrior II pose or the T pose.
         #As for both of them, both arms should be straight and shoulders should be at the specific angle.

         #Check if the both arms are straight.
         if left_elbow_angle > 165 and left_elbow_angle < 195 and right_elbow_angle > 165 and right_elbow_angle < 195:

             #Check if shoulders are at the required angle.
             if left_shoulder_angle > 80 and left_shoulder_angle < 110 and right_shoulder_angle > 80 and right_shoulder_angle < 110:

                 #Check if it is the warrior II pose.

                 #Check if one leg is straight.
                 if left_knee_angle > 165 and left_knee_angle < 195 or right_knee_angle > 165 and right_knee_angle < 195:

                     #Check if the other leg is bended at the required angle.
                     if left_knee_angle > 90 and left_knee_angle < 120 or right_knee_angle > 90 and right_knee_angle < 120:

                         #Specify the label of the pose that is Warrior II pose.
                         label = 'Warrior Pose'


                 #Check if it is the T pose.

                 #Check if both legs are straight
                 if left_knee_angle > 160 and left_knee_angle < 195 and right_knee_angle > 160 and right_knee_angle < 195:

                     #Specify the label of the pose that is tree pose.
                     label = 'T Pose'


         #Check if it is the tree pose.

         #Check if one leg is straight
         if left_knee_angle > 165 and left_knee_angle < 195 or right_knee_angle > 165 and right_knee_angle < 195:

             #Check if the other leg is bended at the required angle.
             if left_knee_angle > 315 and left_knee_angle < 335 or right_knee_angle > 25 and right_knee_angle < 45:

                 #Specify the label of the pose that is tree pose.
                 label = 'Tree Pose'


         #Check if the pose is classified successfully
         if label != 'Unknown Pose':

             color = (0, 255, 0)     #if a pose is found, text is green

         #Write the label on the output image.
         cv2.putText(output_image, label, (10, 30),cv2.FONT_HERSHEY_PLAIN, 2, color, 2)

         #Check if the resultant image is specified to be displayed.
         if display:

             #Display the resultant image.
             plt.figure(figsize=[10,10])
             plt.imshow(output_image[:,:,::-1]);plt.title("Output Image");plt.axis('off');

         else:

             #Return the output image and the classified label.
             return output_image, label

 # Create a window and pass it to the Application object
App(tkinter.Tk(), "Tkinter and OpenCV")
