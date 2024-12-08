import tkinter as tk
from tkinter import ttk, filedialog
from PIL import Image, ImageTk
import os
import cv2

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

        # Button to load images from files
        self.load_button = tk.Button(self.buttons_panel, text="Load Images", command=self.load_images, width=20)
        self.load_button.pack(pady=10, side="bottom")

        # Label to show the camera feed status
        self.camera_label = tk.Label(self.buttons_panel, text="Loading Camera...", bg="lightgray")
        self.camera_label.pack(pady=10)

        # List to store loaded image file paths
        self.setup_camera_feed()

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
        # Initialize webcam feed (use DirectShow backend for Windows compatibility)
        self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        if not self.cap.isOpened():
            self.camera_label.config(text="Error: Unable to access the camera.")
            return

        # Set camera resolution (optional, adjust as needed)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        def update_frame():
            if self.cap.isOpened():
                ret, frame = self.cap.read()
                if ret:
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # Convert to RGB
                    img = Image.fromarray(frame)
                    img = img.resize((300, 225))  # Resize for display
                    imgtk = ImageTk.PhotoImage(image=img)
                    self.camera_label.config(image=imgtk, text="")  # Clear text
                    self.camera_label.image = imgtk  # Keep a reference
                else:
                    self.camera_label.config(text="Error: Unable to capture frame.")
            else:
                self.camera_label.config(text="Error: Camera disconnected.")
            self.camera_label.after(10, update_frame)  # Refresh the frame every 10ms

        update_frame()

    def on_closing(self):
        # Release the camera feed when the window is closed
        if self.cap.isOpened():
            self.cap.release()
        self.root.destroy()

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

        def update_display():
            # Update the display with the transformed image
            img_display = ImageTk.PhotoImage(transformed_image)
            label.config(image=img_display)
            label.image = img_display

        def zoom_in():
            nonlocal transformed_image
            width, height = transformed_image.size
            transformed_image = transformed_image.resize((int(width * 1.2), int(height * 1.2)), Image.Resampling.LANCZOS)
            update_display()

        def zoom_out():
            nonlocal transformed_image
            width, height = transformed_image.size
            transformed_image = transformed_image.resize((int(width * 0.8), int(height * 0.8)), Image.Resampling.LANCZOS)
            update_display()

        # Add buttons for zoom actions
        tk.Button(btn_frame, text="Zoom In", command=zoom_in).pack(side="left", padx=5, pady=5)
        tk.Button(btn_frame, text="Zoom Out", command=zoom_out).pack(side="left", padx=5, pady=5)

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageGalleryApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)  # Ensure camera is released when closing the app
    root.mainloop()
