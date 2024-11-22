import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from PIL import Image, ImageTk
import os

class ImageGalleryApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Image Gallery App")
        self.root.geometry("1000x800")  # Adjusted for the wider right panel

        # Configure the layout
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(1, weight=1)

        # User Guide and Gesture Panel (Left)
        self.guide_panel = tk.Frame(self.root, width=500, bg="gray")
        self.guide_panel.grid(row=0, column=0, sticky="ns")
        
        self.guide_label = tk.Label(
            self.guide_panel,
            text="User Guide:\n\n1. Scroll to browse images.\n2. Click an image to view.\n3. Use Zoom/Rotate buttons.",
            bg="gray",
            fg="white",
            font=("Arial", 10),
            justify="left",
        )
        self.guide_label.pack(pady=10, padx=10)

        # Display Gesture Images Dynamically
        self.load_gesture_images()

        # Main Image Gallery Area (Middle)
        self.gallery_frame = tk.Frame(self.root, bg="white")
        self.gallery_frame.grid(row=0, column=1, sticky="nsew")

        # Scrollbars for the gallery
        self.canvas = tk.Canvas(self.gallery_frame, bg="white", highlightthickness=0)
        self.scroll_y = ttk.Scrollbar(self.gallery_frame, orient="vertical", command=self.canvas.yview)
        self.scroll_x = ttk.Scrollbar(self.gallery_frame, orient="horizontal", command=self.canvas.xview)
        self.scroll_y.pack(side="right", fill="y")
        self.scroll_x.pack(side="bottom", fill="x")
        self.canvas.pack(fill="both", expand=True)
        self.canvas.configure(yscrollcommand=self.scroll_y.set, xscrollcommand=self.scroll_x.set)

        # Gallery Content Frame
        self.gallery_content = tk.Frame(self.canvas, bg="white")
        self.canvas.create_window((0, 0), window=self.gallery_content, anchor="nw")
        self.gallery_content.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        # Bind mouse wheel scrolling
        self.canvas.bind("<MouseWheel>", self._on_mouse_wheel_vertical)  # Vertical scrolling
        self.canvas.bind("<Shift-MouseWheel>", self._on_mouse_wheel_horizontal)  # Horizontal scrolling with Shift key

        # Buttons Panel (Right)
        self.buttons_panel = tk.Frame(self.root, width=300, bg="lightgray")  # Wider right panel
        self.buttons_panel.grid(row=0, column=2, sticky="ns")

        self.load_button = tk.Button(self.buttons_panel, text="Load Images", command=self.load_images, width=20)
        self.load_button.pack(pady=10)

        # A list to hold image paths
        self.image_files = []

    def load_gesture_images(self):
        """Load and display gesture images dynamically from the 'gestures' folder."""
        gestures_folder = "gestures"  # Specify the folder name
        if not os.path.exists(gestures_folder):
            os.makedirs(gestures_folder)  # Create the folder if it doesn't exist
            print(f"Created folder '{gestures_folder}' to store gesture images.")
            return

        gesture_files = os.listdir(gestures_folder)
        gesture_images = [
            f for f in gesture_files if f.lower().endswith(('.png', '.jpg', '.jpeg'))
        ]

        if not gesture_images:
            tk.Label(
                self.guide_panel,
                text="No gesture images found.\nAdd images to the 'gestures' folder.",
                bg="gray",
                fg="yellow",
                font=("Arial", 10),
            ).pack(pady=10)
            return

        for gesture_image in gesture_images:
            img_path = os.path.join(gestures_folder, gesture_image)
            frame = tk.Frame(self.guide_panel, bg="gray", pady=5)
            frame.pack()

            try:
                img = Image.open(img_path)
                img.thumbnail((100, 100))  # Thumbnail size
                img = ImageTk.PhotoImage(img)
                img_label = tk.Label(frame, image=img, bg="gray")
                img_label.image = img  # Keep a reference
                img_label.pack(side="left", padx=5)
            except Exception as e:
                print(f"Error loading {img_path}: {e}")
                img_label = tk.Label(frame, text="No Image", bg="gray", fg="red")
                img_label.pack(side="left", padx=5)

            # Display the filename without extension
            name = os.path.splitext(gesture_image)[0]
            name_label = tk.Label(frame, text=name, bg="gray", fg="white")
            name_label.pack(side="left")

    def _on_mouse_wheel_vertical(self, event):
        """Scroll vertically using the mouse wheel."""
        self.canvas.yview_scroll(-1 * int(event.delta / 120), "units")

    def _on_mouse_wheel_horizontal(self, event):
        """Scroll horizontally using Shift + mouse wheel."""
        self.canvas.xview_scroll(-1 * int(event.delta / 120), "units")

    def load_images(self):
        """Use a file dialog to select images."""
        files = filedialog.askopenfilenames(filetypes=[("Image Files", "*.png;*.jpg;*.jpeg")])
        if not files:
            return

        # Clear previous thumbnails
        for widget in self.gallery_content.winfo_children():
            widget.destroy()

        self.image_files = list(files)

        # Display thumbnails with names or numbered labels
        for index, file in enumerate(self.image_files):
            img = Image.open(file)
            img.thumbnail((100, 100))  # Create a small thumbnail
            img = ImageTk.PhotoImage(img)

            frame = tk.Frame(self.gallery_content, bg="white", padx=5, pady=5)
            frame.grid(row=index // 6, column=index % 6, padx=10, pady=10)

            label = tk.Label(frame, image=img)
            label.image = img  # Keep a reference to avoid garbage collection
            label.pack()
            label.bind("<Button-1>", lambda e, path=file: self.open_image(path))

            # Add name or numbered label below
            name = file.split("/")[-1]  # Extract file name
            name_label = tk.Label(frame, text=name if name else str(index + 1), bg="white")
            name_label.pack()

    def open_image(self, image_path):
        """Open the image in a new window."""
        viewer = tk.Toplevel(self.root)
        viewer.title("Image Viewer")
        viewer.geometry("600x400")

        original_image = Image.open(image_path)
        transformed_image = original_image.copy()
        img_display = ImageTk.PhotoImage(transformed_image)
        label = tk.Label(viewer, image=img_display)
        label.image = img_display  # Keep a reference
        label.pack(fill="both", expand=True)

        btn_frame = tk.Frame(viewer)
        btn_frame.pack(fill="x")

        def update_display():
            """Update the displayed image."""
            nonlocal transformed_image, img_display
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

        def rotate_image():
            nonlocal transformed_image
            transformed_image = transformed_image.rotate(90, expand=True)
            update_display()

        tk.Button(btn_frame, text="Zoom In", command=zoom_in).pack(side="left", padx=5, pady=5)
        tk.Button(btn_frame, text="Zoom Out", command=zoom_out).pack(side="left", padx=5, pady=5)
        tk.Button(btn_frame, text="Rotate", command=rotate_image).pack(side="left", padx=5, pady=5)


# Run the application
if __name__ == "__main__":
    root = tk.Tk()
    app = ImageGalleryApp(root)
    root.mainloop()
