import tkinter as tk
from PIL import Image, ImageTk
import json

class BoundingBoxApp:
    def __init__(self, root, image_path):
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
        self.start_x = event.x
        self.start_y = event.y
        self.rect = self.canvas.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y, outline='red')

    def on_mouse_drag(self, event):
        cur_x, cur_y = (event.x, event.y)
        self.canvas.coords(self.rect, self.start_x, self.start_y, cur_x, cur_y)

    def on_button_release(self, event):
        end_x, end_y = (event.x, event.y)
        self.bboxes.append((self.start_x, self.start_y, end_x, end_y))

    def save_bboxes(self):
        with open(f"{self.image_path}_bboxes.json", "w") as f:
            json.dump(self.bboxes, f)
        print(f"Bounding boxes saved to {self.image_path}_bboxes.json")

if __name__ == "__main__":
    image_path = input("Enter the path to the image: ")
    root = tk.Tk()
    app = BoundingBoxApp(root, image_path)
    root.mainloop()