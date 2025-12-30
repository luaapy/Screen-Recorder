import tkinter as tk
import customtkinter as ctk

class RegionSelectionWindow(tk.Toplevel):
    def __init__(self, master, on_select_callback):
        super().__init__(master)
        self.on_select_callback = on_select_callback
        
        # Remove window decorations and set fullscreen
        self.overrideredirect(True)
        self.attributes('-alpha', 0.3)  # Transparency
        self.attributes('-topmost', True)
        
        # Get screen dimensions
        self.screen_width = self.winfo_screenwidth()
        self.screen_height = self.winfo_screenheight()
        self.geometry(f"{self.screen_width}x{self.screen_height}+0+0")
        
        self.configure(bg="black", cursor="cross")
        
        # State
        self.start_x = None
        self.start_y = None
        self.rect_id = None
        
        # Canvas for drawing
        self.canvas = tk.Canvas(self, width=self.screen_width, height=self.screen_height, bg="black", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        
        # Bindings
        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.bind("<Escape>", self.cancel)
        
        # Info label
        self.info_label = tk.Label(self, text="Drag to select region (ESC to cancel)", bg="white", fg="black")
        self.info_label.place(x=10, y=10)

    def on_press(self, event):
        self.start_x = event.x
        self.start_y = event.y
        if self.rect_id:
            self.canvas.delete(self.rect_id)
        self.rect_id = self.canvas.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y, outline="red", width=2)

    def on_drag(self, event):
        cur_x, cur_y = (event.x, event.y)
        self.canvas.coords(self.rect_id, self.start_x, self.start_y, cur_x, cur_y)
        
        width = abs(cur_x - self.start_x)
        height = abs(cur_y - self.start_y)
        self.info_label.config(text=f"Size: {width}x{height} | Pos: {self.start_x},{self.start_y}")

    def on_release(self, event):
        end_x, end_y = (event.x, event.y)
        
        # Normalize coordinates
        x1 = min(self.start_x, end_x)
        y1 = min(self.start_y, end_y)
        x2 = max(self.start_x, end_x)
        y2 = max(self.start_y, end_y)
        
        width = x2 - x1
        height = y2 - y1
        
        if width < 10 or height < 10:
            # Too small, maybe accidental click
            return
            
        region = (x1, y1, width, height)
        self.on_select_callback(region)
        self.destroy()

    def cancel(self, event=None):
        self.destroy()
        
if __name__ == "__main__":
    root = tk.Tk()
    def callback(r): print(f"Selected: {r}")
    btn = tk.Button(root, text="Select", command=lambda: RegionSelectionWindow(root, callback))
    btn.pack()
    root.mainloop()
