import tkinter as tk
from tkinter import ttk, filedialog
from PIL import Image, ImageTk
import os
import cv2
import threading
import time
import mediaPipeHandler as mph

class ImageGalleryApp:
    
    def __init__(self, root):
        # Initialize the main application window
        self.root = root
        self.root.title("Image Gallery App")
        self.root.geometry("1000x800")  # Set the window size

        # Configure layout of the main window with resizable grids
        self.root.rowconfigure(0, weight=1)  # Row 0 is expandable
        self.root.columnconfigure(1, weight=1)  # Column 1 is expandable

        # User Guide and Gesture Panel (Left side)
        self.guide_panel = tk.Frame(self.root, width=500, bg="gray")
        self.guide_panel.grid(row=0, column=0, sticky="ns")  # The left panel will stretch vertically

        # Label for user instructions in the guide panel
        self.guide_label = tk.Label(
            self.guide_panel,
            text="User Guide:\n\n1. Scroll to browse images.\n2. Click an image to view.\n3. Use Zoom buttons.",
            bg="gray",
            fg="white",
            font=("Arial", 10),
            justify="left",
        )
        self.guide_label.pack(pady=10, padx=10)

        # Button to load gesture images
        self.load_gestures_button = tk.Button(self.guide_panel, text="Load Gestures", command=self.load_gesture_images, width=20)
        self.load_gestures_button.pack(pady=10)

        # Load gesture images by default when the app starts
        self.load_gesture_images()

        # Main Image Gallery Area (Middle section)
        self.gallery_frame = tk.Frame(self.root, bg="white")
        self.gallery_frame.grid(row=0, column=1, sticky="nsew")  # Center the gallery frame

        # Scrollable canvas for displaying thumbnails
        self.canvas = tk.Canvas(self.gallery_frame, bg="white", highlightthickness=0)
        self.scroll_y = ttk.Scrollbar(self.gallery_frame, orient="vertical", command=self.canvas.yview)
        self.scroll_x = ttk.Scrollbar(self.gallery_frame, orient="horizontal", command=self.canvas.xview)
        self.scroll_y.pack(side="right", fill="y")
        self.scroll_x.pack(side="bottom", fill="x")
        self.canvas.pack(fill="both", expand=True)
        self.canvas.configure(yscrollcommand=self.scroll_y.set, xscrollcommand=self.scroll_x.set)

        # Content frame inside the canvas to hold images
        self.gallery_content = tk.Frame(self.canvas, bg="white")
        self.canvas.create_window((0, 0), window=self.gallery_content, anchor="nw")
        self.gallery_content.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        # Mouse wheel scrolling
        self.canvas.bind("<MouseWheel>", self._on_mouse_wheel_vertical)
        self.canvas.bind("<Shift-MouseWheel>", self._on_mouse_wheel_horizontal)

        # Buttons Panel (Right side)
        self.buttons_panel = tk.Frame(self.root, width=400, bg="lightgray")
        self.buttons_panel.grid(row=0, column=2, sticky="ns")  # The right panel will stretch vertically

        # Label to show the camera feed
        self.camera_label = tk.Label(self.buttons_panel, text="Loading Camera...", bg="lightgray")
        self.camera_label.pack(pady=10)

        self.camera_label = tk.Label(self.buttons_panel, bg="lightgray", width=400, height=400)
        self.camera_label.pack(pady=10)


        # # Image Viewer Area (Bottom section)
        # self.viewer_label = tk.Label(self.root, text="Selected Image will appear here", bg="white")
        # self.viewer_label.grid(row=1, column=1, sticky="nsew")

        # Image Viewer Area (Bottom section)
        self.viewer_label = tk.Label(
            self.root, 
            text="Selected Image will appear here", 
            bg="white"
        )
        self.viewer_label.grid(row=1, column=1, sticky="nsew")


        # Store the currently displayed image
        self.current_image = None
        self.transformed_image = None
        self.original_image = None  # To keep a reference of the original image

        self.selected_index = None  # Track the index of the selected image
        

        self.cursor = tk.Label(self.root, text="O", bg="red", fg="white")
        self.cursor.place(x=0, y=0)  # Initialize at (0, 0)

        # Button to load images from files
        self.load_button = tk.Button(self.buttons_panel, text="Load Images", command=self.load_images, width=20)
        self.load_button.pack(pady=10, side="bottom")


        # List to store loaded image file paths
        self.setup_camera_feed()

    def update_selected_image(self, image_path):
        try:
            self.original_image = Image.open(image_path)

            # Fixed dimensions for the viewer
            target_width, target_height = 400, 300
            original_width, original_height = self.original_image.size

            # Calculate scale to fit the image within the target dimensions
            scale = min(target_width / original_width, target_height / original_height)
            new_width = int(original_width * scale)
            new_height = int(original_height * scale)

            # Resize the image while maintaining aspect ratio
            self.transformed_image = self.original_image.resize((new_width, new_height), Image.Resampling.LANCZOS)

            # Center the resized image in the fixed dimensions
            centered_image = Image.new("RGB", (target_width, target_height), "white")
            x_offset = (target_width - new_width) // 2
            y_offset = (target_height - new_height) // 2
            centered_image.paste(self.transformed_image, (x_offset, y_offset))

            # Update the viewer with the centered image
            self.current_image = ImageTk.PhotoImage(centered_image)
            self.viewer_label.config(image=self.current_image, text="")
        except Exception as e:
         print(f"Error loading image: {e}")
        
        
    def _update_image_in_fixed_window(self):
        """Ensure the image is displayed within the fixed viewer window."""
        try:
            # Fixed dimensions for the viewer
            target_width, target_height = 400, 300  # Example fixed dimensions

            # Create a blank canvas to center the image
            centered_image = Image.new("RGB", (target_width, target_height), "white")

            # Calculate offsets to center the image
            image_width, image_height = self.transformed_image.size
            x_offset = max(0, (target_width - image_width) // 2)
            y_offset = max(0, (target_height - image_height) // 2)

            # Paste the resized image onto the blank canvas
            centered_image.paste(self.transformed_image, (x_offset, y_offset))

            # Update the viewer label with the centered image
            self.current_image = ImageTk.PhotoImage(centered_image)
            self.viewer_label.config(image=self.current_image)
        except Exception as e:
            print(f"Error updating image: {e}")


    def update_cursor(self, x, y):
        self.cursor.place(x=x, y=y)

    def detect_hover(self, cursor_x, cursor_y):
        positions = self.get_thumbnail_positions()
        for index, (x1, y1, x2, y2) in enumerate(positions):
            if x1 <= cursor_x <= x2 and y1 <= cursor_y <= y2:
                return index
        return None

    def load_gesture_images(self):
        # Open a folder selection dialog for gesture images
        gestures_folder = filedialog.askdirectory(title="Select Gesture Folder")
        
        if not gestures_folder:  # If the user cancels the folder selection
            return
        
        # Get all gesture image files from the selected folder
        gesture_files = os.listdir(gestures_folder)
        gesture_images = [f for f in gesture_files if f.lower().endswith(('.png', '.jpg', '.jpeg'))]

        # Notify user if no gesture images are found
        if not gesture_images:
            tk.Label(
                self.guide_panel,
                text="No gesture images found.\nAdd images to the selected folder.",
                bg="gray",
                fg="yellow",
                font=("Arial", 10),
            ).pack(pady=10)
            return

        # Display each gesture image as a thumbnail
        for gesture_image in gesture_images:
            img_path = os.path.join(gestures_folder, gesture_image)
            frame = tk.Frame(self.guide_panel, bg="gray", pady=5)
            frame.pack()

            try:
                # Load and display thumbnail image
                img = Image.open(img_path)
                img.thumbnail((100, 100))
                img = ImageTk.PhotoImage(img)
                img_label = tk.Label(frame, image=img, bg="gray")
                img_label.image = img  # Keep a reference to avoid garbage collection
                img_label.pack(side="left", padx=5)
            except Exception as e:
                print(f"Error loading {img_path}: {e}")
                img_label = tk.Label(frame, text="No Image", bg="gray", fg="red")
                img_label.pack(side="left", padx=5)

            # Display the name of each gesture image
            name = os.path.splitext(gesture_image)[0]
            name_label = tk.Label(frame, text=name, bg="gray", fg="white")
            name_label.pack(side="left")

    def setup_camera_feed(self):
        self.stop_event = threading.Event()
        self.gesture_detection = mph.GestureDetection(self.stop_event, self.camera_label, self.root,self)
        self.gesture_detection.start()


    def on_closing(self, stop_event):
        # Stop the camera feed thread and close the application window
        stop_event.set()
        self.root.destroy()
    
    #######################
    def gesture_click(self, index):
        print("Clicking Event")
        # thumbnails = self.gallery_content.winfo_children()
        # if index != None:
        #     frame = thumbnails[index]
        #     label = frame.winfo_children()[0]  # Get the image label
        #     file_path = self.image_files[index]
        #     self.update_selected_image(file_path)  # Open the image

        """Handle the clicking gesture and update the selection highlight."""
        thumbnails = self.gallery_content.winfo_children()

        # Reset the background color of the previously selected image
        if self.selected_index is not None:
            thumbnails[self.selected_index].configure(bg="white")

        # Highlight the newly selected image
        if index is not None:
            frame = thumbnails[index]
            frame.configure(bg="green")  # Use a distinct color for selection highlight
            self.selected_index = index  # Update the selected index

            # Open the selected image
            file_path = self.image_files[index]
            self.update_selected_image(file_path)

    def gesture_scroll(self, direction):
        """Simulate scrolling in the specified direction."""
        if direction == "up":
            self.canvas.yview_scroll(-1, "units")
        elif direction == "down":
            self.canvas.yview_scroll(1, "units")
        elif direction == "left":
            self.canvas.xview_scroll(-1, "units")
        elif direction == "right":
            self.canvas.xview_scroll(1, "units")

    def get_thumbnail_positions(self):
        positions = []
        for widget in self.gallery_content.winfo_children():
            x1 = widget.winfo_rootx() - self.root.winfo_rootx()
            y1 = widget.winfo_rooty() - self.root.winfo_rooty()
            x2 = x1 + widget.winfo_width()
            y2 = y1 + widget.winfo_height()
            positions.append((x1, y1, x2, y2))
        return positions

    def gesture_hover(self, index): 
        # thumbnails = self.gallery_content.winfo_children()
        # for i, widget in enumerate(thumbnails):
        #     widget.configure(bg="white")  # Reset background color
        # if 0 <= index < len(thumbnails):
        #     thumbnails[index].configure(bg="lightblue")
        """Simulate hovering over an image thumbnail."""
        thumbnails = self.gallery_content.winfo_children()
        
        for i, widget in enumerate(thumbnails):
            # Reset to white unless the image is selected
            if i != self.selected_index:
                widget.configure(bg="white")
        
        # Highlight hover if it's not the selected image
        if index is not None and index != self.selected_index:
            thumbnails[index].configure(bg="lightblue")  # Hover color

    def _on_mouse_wheel_vertical(self, event):
        # Scroll vertically using the mouse wheel.
        self.canvas.yview_scroll(-1 * int(event.delta / 120), "units")

    def _on_mouse_wheel_horizontal(self, event):
        # Scroll horizontally using Shift + mouse wheel.
        self.canvas.xview_scroll(-1 * int(event.delta / 120), "units")

    def load_images(self):
        # Use a file dialog to select multiple image files
        files = filedialog.askopenfilenames(filetypes=[("Image Files", "*.png;*.jpg;*.jpeg")])
        if not files:
            return

        # Clear existing thumbnails in the gallery
        for widget in self.gallery_content.winfo_children():
            widget.destroy()

        self.image_files = list(files)

        # Display the selected images as thumbnails
        for index, file in enumerate(self.image_files):
            img = Image.open(file)
            img.thumbnail((100, 100))  # Create a thumbnail of each image
            img = ImageTk.PhotoImage(img)

            frame = tk.Frame(self.gallery_content, bg="white", padx=5, pady=5)
            frame.grid(row=index // 6, column=index % 6, padx=10, pady=10)

            label = tk.Label(frame, image=img)
            label.image = img  # Keep a reference
            label.pack()
            label.bind("<Button-1>", lambda e, path=file: self.open_image(path))

            # Display the image file name under the thumbnail
            name = file.split("/")[-1]  # Get the file name
            name_label = tk.Label(frame, text=name if name else str(index + 1), bg="white")
            name_label.pack()

    def open_image(self, image_path):
        print("New Image Opened")
        # Open an image in a new window for viewing
        viewer = tk.Toplevel(self.root)
        viewer.title("Image Viewer")
        viewer.geometry("600x400")

        # Open and transform the image
        original_image = Image.open(image_path)
        transformed_image = original_image.copy()
        img_display = ImageTk.PhotoImage(transformed_image)
        label = tk.Label(viewer, image=img_display)
        label.image = img_display  # Keep a reference to avoid garbage collection
        label.pack(fill="both", expand=True)

        # Control buttons for zooming
        btn_frame = tk.Frame(viewer)
        btn_frame.pack(side="bottom", fill="x", padx=10, pady=5)

    def zoom_in(self):
        """Zoom in on the displayed image."""

        if self.original_image:
            # Increase the scale of the image
            width, height = self.transformed_image.size
            scale = 1.2
            new_width, new_height = int(width * scale), int(height * scale)

            # Resize the image
            self.transformed_image = self.original_image.resize((new_width, new_height), Image.Resampling.LANCZOS)

            # Fit the scaled image within the fixed viewer dimensions
            self._update_image_in_fixed_window()

    def zoom_out(self):
        """Zoom out on the displayed image."""
        if self.original_image:
            # Decrease the scale of the image
            width, height = self.transformed_image.size
            scale = 0.8
            new_width, new_height = int(width * scale), int(height * scale)

            # Resize the image
            self.transformed_image = self.original_image.resize((new_width, new_height), Image.Resampling.LANCZOS)

            # Fit the scaled image within the fixed viewer dimensions
            self._update_image_in_fixed_window()


    def gesture_zoom(self, zoom_direction):

        print("Zoom Direction" + zoom_direction)
        """Handle zoom gestures."""
        if zoom_direction == "in":
            self.zoom_in()
        elif zoom_direction == "out":
            self.zoom_out()

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageGalleryApp(root)
    root.protocol("WM_DELETE_WINDOW", lambda: app.on_closing(app.stop_event))  # Ensure camera is released when closing the app
    root.mainloop()
