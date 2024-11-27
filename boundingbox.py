import tkinter as tk
from PIL import Image, ImageTk
import json

class BoundingBoxApp:
    def __init__(self, root, image_path):
        """
        Initialize the BoundingBoxApp with a Tkinter root and an image path.

        Parameters:
        - root (tk.Tk): The root window of the Tkinter application.
        - image_path (str): The file path to the image to be displayed and annotated.

        Attributes:
        - image (PIL.Image): The image object loaded from the image path.
        - tk_image (ImageTk.PhotoImage): The Tkinter-compatible image object.
        - canvas (tk.Canvas): The canvas widget for displaying the image and drawing bounding boxes.
        - rect (int): The ID of the current rectangle being drawn.
        - start_x (int): The x-coordinate where the mouse button was pressed.
        - start_y (int): The y-coordinate where the mouse button was pressed.
        - bboxes (list): A list to store the coordinates of drawn bounding boxes.
        """
        self.root = root
        self.image_path = image_path
        self.image = Image.open(image_path)
        self.tk_image = ImageTk.PhotoImage(self.image)
        
        self.canvas = tk.Canvas(root, width=self.image.width, height=self.image.height)
        self.canvas.pack()
        
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_image)
        
        self.rect = None
        self.start_x = None
        self.start_y = None
        self.bboxes = []
        
        self.canvas.bind("<ButtonPress-1>", self.on_button_press)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_button_release)
        
        self.save_button = tk.Button(root, text="Save", command=self.save_bboxes)
        self.save_button.pack()

    def on_button_press(self, event):
        """
        Handle the event when the mouse button is pressed.

        Parameters:
        - event (tk.Event): The event object containing information about the mouse event.

        Functionality:
        - Records the starting coordinates of the mouse press.
        - Initializes a rectangle on the canvas at the starting coordinates.
        """
        self.start_x = event.x
        self.start_y = event.y
        self.rect = self.canvas.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y, outline='red')

    def on_mouse_drag(self, event):
        """
        Handle the event when the mouse is dragged with the button pressed.

        Parameters:
        - event (tk.Event): The event object containing information about the mouse event.

        Functionality:
        - Updates the coordinates of the rectangle being drawn as the mouse is dragged.
        """
        cur_x, cur_y = (event.x, event.y)
        self.canvas.coords(self.rect, self.start_x, self.start_y, cur_x, cur_y)

    def on_button_release(self, event):
        """
        Handle the event when the mouse button is released.

        Parameters:
        - event (tk.Event): The event object containing information about the mouse event.

        Functionality:
        - Finalizes the coordinates of the rectangle and adds it to the list of bounding boxes.
        """
        end_x, end_y = (event.x, event.y)
        self.bboxes.append((self.start_x, self.start_y, end_x, end_y))

    def save_bboxes(self):
        """
        Save the list of bounding boxes to a JSON file.

        Functionality:
        - Writes the bounding box coordinates to a JSON file named after the image path.
        - Prints a confirmation message upon successful save.
        """
        with open(f"{self.image_path}_bboxes.json", "w") as f:
            json.dump(self.bboxes, f)
        print(f"Bounding boxes saved to {self.image_path}_bboxes.json")

if __name__ == "__main__":
    image_path = input("Enter the path to the image: ")
    root = tk.Tk()
    app = BoundingBoxApp(root, image_path)
    root.mainloop()