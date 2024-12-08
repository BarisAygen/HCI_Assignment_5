import mediapipe as mp
import cv2
import gestures
import time
import mediaPipeHandler as mph
import tkinter as tk
from tkinter import ttk, filedialog
from PIL import Image, ImageTk

mpHands = mp.solutions.hands
hands = mpHands.Hands(max_num_hands=1, min_detection_confidence=0.7)
mpDraw = mp.solutions.drawing_utils

default_landmark_spec = mpDraw.DrawingSpec(color=(0, 0, 255), thickness=2, circle_radius=2)  # Red color
default_connection_spec = mpDraw.DrawingSpec(color=(255, 255, 255), thickness=2)  # White color

# Printing Commands on the screen 
def print_command(frame,command_text):
    cv2.putText(frame, command_text, (50,50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

class GestureDetection:
    def __init__(self, stop_event, camera_label, root,app):
        self.stop_event = stop_event
        self.camera_label = camera_label
        self.root = root
        self.camera = cv2.VideoCapture(0)
        self.trail = []
        self.trail_max_length = 10
        self.trail_color = (0, 255, 0)
        self.trail_start_radius = 10
        self.previous_index_x = None
        self.previous_index_y = None
        self.previous_distance = None
        self.last_gesture_time = time.time()
        self.app = app 


    def move_cursor(self, index_tip):
        gui_width = self.root.winfo_width()
        gui_height = self.root.winfo_height()
        cursor_x = int(index_tip[0] / 400 * gui_width)
        cursor_y = int(index_tip[1] / 400 * gui_height)

        # Update the cursor position in the GUI
        self.app.update_cursor(cursor_x, cursor_y)

        # Check for hover over thumbnails
        hovered_index = self.app.detect_hover(cursor_x, cursor_y)
        if hovered_index is not None:
            self.app.gesture_hover(hovered_index)

    
    def update_frame(self):
        if self.stop_event.is_set():
            self.camera.release()
            return

        isCapturedFrameSuccessful, frame = self.camera.read()
        if not isCapturedFrameSuccessful:
            print("An error happened.")
            self.camera.release()
            return

        frame = cv2.resize(frame, (400, 400))
        frame = cv2.flip(frame, 1)
        framergb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Process hand landmarks
        hand_process_result = mph.hands.process(framergb)

        if hand_process_result.multi_hand_landmarks:
            for hand_landmarks in hand_process_result.multi_hand_landmarks:
                landmarks = []
                for idx, lm in enumerate(hand_landmarks.landmark):  # Iterate through each landmark
                    x = int(lm.x * frame.shape[1])  # Get x coordinate
                    y = int(lm.y * frame.shape[0])  # Get y coordinate
                    landmarks.append([x, y])

                # Detect hover gesture
                hovered_index = gestures.is_hover_gesture(landmarks, self.app.get_thumbnail_positions())
                if hovered_index != -1:  # Ensure hovered_index is valid
                    self.app.gesture_hover(hovered_index)

                # Draw connections first
                mph.mpDraw.draw_landmarks(frame, hand_landmarks, mph.mpHands.HAND_CONNECTIONS, mph.default_landmark_spec, mph.default_connection_spec)

                # Draw the filled green circle for the index finger tip
                index_tip = landmarks[8]
                cv2.circle(frame, (index_tip[0], index_tip[1]), 5, (0, 255, 0), -1)
                self.move_cursor(index_tip)

                # Add the index finger position to the trail
                self.trail.append(index_tip)
                if len(self.trail) > self.trail_max_length:
                    self.trail.pop(0)

                # Draw the ripple trail
                for i, point in enumerate(self.trail):
                    radius = self.trail_start_radius - int((i / self.trail_max_length) * self.trail_start_radius)
                    cv2.circle(frame, point, radius, self.trail_color, 1)

                # Gesture detection with visual feedback
                if gestures.is_click_gesture(landmarks) and time.time() - self.last_gesture_time > 1:
                    cv2.putText(frame, "Click", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)
                    gui_width = self.root.winfo_width()
                    gui_height = self.root.winfo_height()
                    cursor_x = int(index_tip[0] / 400 * gui_width)
                    cursor_y = int(index_tip[1] / 400 * gui_height)
                    hovered_index = self.app.detect_hover(cursor_x, cursor_y)
                    self.app.gesture_click(hovered_index)
                    self.last_gesture_time = time.time()

                elif gestures.is_scroll_gesture(landmarks) and time.time() - self.last_gesture_time > 1:
                    direction, self.previous_index_x, self.previous_index_y = gestures.detect_scroll_direction(
                        landmarks, self.previous_index_x, self.previous_index_y
                    )
                    if direction != "none":
                        cv2.putText(frame, f"Scrolling: {direction}", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)
                        self.last_gesture_time = time.time()
                        self.app.gesture_scroll(direction)

                elif gestures.is_zoom_detected(landmarks) and time.time() - self.last_gesture_time > 1:
                    zoom_direction, self.previous_distance = gestures.detect_zoom_direction(landmarks, self.previous_distance)
                    if zoom_direction != "":
                        cv2.putText(frame, f"Zooming: {zoom_direction}", (50, 150), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)
                        self.app.gesture_zoom(zoom_direction)
                        self.last_gesture_time = time.time()

        # Convert frame to ImageTk format
        img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        img_tk = ImageTk.PhotoImage(image=img)

        # Update the label
        self.camera_label.img_tk = img_tk  # Keep a reference
        self.camera_label.configure(image=img_tk)

        # Schedule the next frame update
        self.root.after(10, self.update_frame)

    def start(self):
        self.update_frame()

