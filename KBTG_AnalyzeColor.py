import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from PIL import Image, ImageTk
import numpy as np
import math
import os

class ColorGridAnalyzer:
    def __init__(self, root):
        self.root = root
        self.root.title("KBTG Color Analyzer")
        self.root.geometry("1200x800")
        
        # Variables
        self.image = None
        self.image_tk = None  # Renamed from display_image to avoid method name conflict
        self.photo = None
        self.reference_color = None
        self.rect_start_x = None
        self.rect_start_y = None
        self.rect_end_x = None
        self.rect_end_y = None
        self.drawing = False
        self.grid_colors = []
        self.scale_factor = 1.0
        
        # Create main layout
        self.create_layout()
        
    def create_layout(self):
        # Main frames
        self.left_frame = tk.Frame(self.root, width=800)
        self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.right_frame = tk.Frame(self.root, width=400)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=10, pady=10)
        
        # Left frame - Image and controls
        self.control_frame = tk.Frame(self.left_frame)
        self.control_frame.pack(fill=tk.X, pady=5)
        
        self.load_image_btn = tk.Button(self.control_frame, text="Load Image", command=self.load_image)
        self.load_image_btn.pack(side=tk.LEFT, padx=5)
        
        self.sample_ref_btn = tk.Button(self.control_frame, text="Sample Reference Color", command=self.enable_reference_sampling)
        self.sample_ref_btn.pack(side=tk.LEFT, padx=5)
        
        self.clear_btn = tk.Button(self.control_frame, text="Clear Selection", command=self.clear_selection)
        self.clear_btn.pack(side=tk.LEFT, padx=5)
        
        self.analyze_btn = tk.Button(self.control_frame, text="Analyze Grid", command=self.analyze_grid)
        self.analyze_btn.pack(side=tk.LEFT, padx=5)
        
        self.status_label = tk.Label(self.control_frame, text="Load an image to begin")
        self.status_label.pack(side=tk.RIGHT, padx=10)
        
        # Reference color display
        self.ref_frame = tk.Frame(self.left_frame)
        self.ref_frame.pack(fill=tk.X, pady=5)
        
        self.ref_label = tk.Label(self.ref_frame, text="Reference Color:")
        self.ref_label.pack(side=tk.LEFT)
        
        self.ref_color_display = tk.Label(self.ref_frame, width=6, height=2, bg="white", relief="sunken")
        self.ref_color_display.pack(side=tk.LEFT, padx=5)
        
        self.ref_rgb_label = tk.Label(self.ref_frame, text="RGB: -")
        self.ref_rgb_label.pack(side=tk.LEFT, padx=5)
        
        self.ref_hex_label = tk.Label(self.ref_frame, text="HEX: -")
        self.ref_hex_label.pack(side=tk.LEFT, padx=5)
        
        # Canvas for image display
        self.canvas_frame = tk.Frame(self.left_frame)
        self.canvas_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.canvas = tk.Canvas(self.canvas_frame, bg="white", cursor="crosshair")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind("<ButtonPress-1>", self.on_mouse_down)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)
        
        # Right frame - Results
        self.results_label = tk.Label(self.right_frame, text="Color Matching Results", font=("Arial", 12, "bold"))
        self.results_label.pack(pady=10)
        
        # Create treeview for results
        self.create_results_treeview()
        
    def create_results_treeview(self):
        columns = ("position", "color", "rgb", "hex", "similarity")
        self.results_tree = ttk.Treeview(self.right_frame, columns=columns, show="headings", height=30)
        
        # Define headings
        self.results_tree.heading("position", text="Position")
        self.results_tree.heading("color", text="Color")
        self.results_tree.heading("rgb", text="RGB")
        self.results_tree.heading("hex", text="HEX")
        self.results_tree.heading("similarity", text="Match %")
        
        # Define columns
        self.results_tree.column("position", width=80, anchor=tk.CENTER)
        self.results_tree.column("color", width=50, anchor=tk.CENTER)
        self.results_tree.column("rgb", width=100, anchor=tk.CENTER)
        self.results_tree.column("hex", width=80, anchor=tk.CENTER)
        self.results_tree.column("similarity", width=80, anchor=tk.CENTER)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(self.right_frame, orient=tk.VERTICAL, command=self.results_tree.yview)
        self.results_tree.configure(yscroll=scrollbar.set)
        
        # Pack everything
        self.results_tree.pack(fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind click event
        self.results_tree.bind("<ButtonRelease-1>", self.on_result_click)
        
    def load_image(self):
        # Print current working directory for debugging
        print("Current working directory:", os.getcwd())
        
        file_path = filedialog.askopenfilename(
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp *.gif")]
        )
        
        # Debug: Print the selected file path
        print(f"Selected file path: {file_path}")
        
        if not file_path:
            print("No file selected.")
            return
        
        try:
            # Try to open the image
            print(f"Attempting to open image: {file_path}")
            img = Image.open(file_path)
            
            # Convert to RGB mode if needed
            if img.mode != "RGB":
                img = img.convert("RGB")
                
            self.image = img
            print(f"Image loaded successfully. Size: {img.size}")
            
            # Show the image
            self.show_image()
            self.status_label.config(text="Image loaded. Draw rectangle around grid.")
            self.clear_selection()
            
        except Exception as e:
            error_msg = f"Failed to load image: {str(e)}"
            print(error_msg)
            messagebox.showerror("Error", error_msg)
    
    def show_image(self):  # Renamed from display_image to avoid conflict
        if self.image is None:
            print("No image to display")
            return
            
        try:
            # Get canvas dimensions
            canvas_width = self.canvas.winfo_width() or 700
            canvas_height = self.canvas.winfo_height() or 500
            
            # Calculate scaling factor
            img_width, img_height = self.image.size
            width_scale = canvas_width / img_width
            height_scale = canvas_height / img_height
            self.scale_factor = min(width_scale, height_scale)
            
            # Resize image for display
            new_width = int(img_width * self.scale_factor)
            new_height = int(img_height * self.scale_factor)
            
            print(f"Resizing image to: {new_width}x{new_height}")
            self.image_tk = self.image.resize((new_width, new_height), Image.LANCZOS)
            self.photo = ImageTk.PhotoImage(self.image_tk)
            
            # Display on canvas
            self.canvas.delete("all")
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)
            print("Image displayed successfully")
        except Exception as e:
            error_msg = f"Error displaying image: {str(e)}"
            print(error_msg)
            messagebox.showerror("Error", error_msg)
    
    def enable_reference_sampling(self):
        if not self.image:
            messagebox.showinfo("Info", "Please load an image first.")
            return
            
        self.status_label.config(text="Click on image to sample reference color")
        self.canvas.bind("<ButtonPress-1>", self.sample_color)
        self.drawing = False
    
    def sample_color(self, event):
        if not self.image:
            return
        
        # Convert canvas coordinates to image coordinates
        img_x = int(event.x / self.scale_factor)
        img_y = int(event.y / self.scale_factor)
        
        try:
            # Make sure coordinates are within image bounds
            img_width, img_height = self.image.size
            if img_x < 0 or img_x >= img_width or img_y < 0 or img_y >= img_height:
                print(f"Click coordinates out of bounds: ({img_x}, {img_y})")
                return
                
            # Get pixel color
            pixel = self.image.getpixel((img_x, img_y))
            if len(pixel) > 3:  # RGBA format
                pixel = pixel[:3]
            
            # Set as reference color
            self.reference_color = pixel
            hex_color = f"#{pixel[0]:02X}{pixel[1]:02X}{pixel[2]:02X}"
            
            # Update UI
            self.ref_color_display.config(bg=hex_color)
            self.ref_rgb_label.config(text=f"RGB: {pixel}")
            self.ref_hex_label.config(text=f"HEX: {hex_color}")
            
            self.status_label.config(text="Reference color set. Draw rectangle around grid.")
            
            # Reset canvas bindings
            self.canvas.bind("<ButtonPress-1>", self.on_mouse_down)
            self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
            self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)
            
            print(f"Reference color set: RGB={pixel}, HEX={hex_color}")
            
        except Exception as e:
            error_msg = f"Failed to sample color: {str(e)}"
            print(error_msg)
            messagebox.showerror("Error", error_msg)
    
    def on_mouse_down(self, event):
        if not self.image:
            return
            
        self.rect_start_x = event.x
        self.rect_start_y = event.y
        self.drawing = True
        
        # Clear any existing rectangle
        self.canvas.delete("rect")
    
    def on_mouse_drag(self, event):
        if not self.drawing or not self.image:
            return
            
        self.rect_end_x = event.x
        self.rect_end_y = event.y
        
        # Update rectangle
        self.canvas.delete("rect")
        self.canvas.create_rectangle(
            self.rect_start_x, self.rect_start_y,
            self.rect_end_x, self.rect_end_y,
            outline="red", width=2, tags="rect"
        )
    
    def on_mouse_up(self, event):
        if not self.drawing or not self.image:
            return
            
        self.rect_end_x = event.x
        self.rect_end_y = event.y
        self.drawing = False
        
        # Ensure rectangle coordinates are ordered
        if self.rect_start_x > self.rect_end_x:
            self.rect_start_x, self.rect_end_x = self.rect_end_x, self.rect_start_x
        
        if self.rect_start_y > self.rect_end_y:
            self.rect_start_y, self.rect_end_y = self.rect_end_y, self.rect_start_y
        
        self.status_label.config(text="Rectangle drawn. Click 'Analyze Grid' to process.")
    
    def clear_selection(self):
        self.canvas.delete("rect")
        self.canvas.delete("grid")
        self.canvas.delete("highlight")
        self.rect_start_x = None
        self.rect_start_y = None
        self.rect_end_x = None
        self.rect_end_y = None
        self.drawing = False
        self.grid_colors = []
        
        # Clear results
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
    
    def analyze_grid(self):
        if not self.image:
            messagebox.showinfo("Info", "Please load an image first.")
            return
            
        if not self.reference_color:
            messagebox.showinfo("Info", "Please set a reference color first.")
            return
        
        if not (self.rect_start_x and self.rect_start_y and self.rect_end_x and self.rect_end_y):
            messagebox.showinfo("Info", "Please draw a rectangle around the color grid first.")
            return
        
        # Convert canvas coordinates to image coordinates
        img_start_x = int(self.rect_start_x / self.scale_factor)
        img_start_y = int(self.rect_start_y / self.scale_factor)
        img_end_x = int(self.rect_end_x / self.scale_factor)
        img_end_y = int(self.rect_end_y / self.scale_factor)
        
        # Make sure coordinates are within image bounds
        img_width, img_height = self.image.size
        img_start_x = max(0, min(img_start_x, img_width-1))
        img_start_y = max(0, min(img_start_y, img_height-1))
        img_end_x = max(0, min(img_end_x, img_width-1))
        img_end_y = max(0, min(img_end_y, img_height-1))
        
        # Ask user for grid dimensions
        grid_dims = self.ask_grid_dimensions()
        if not grid_dims:
            return
        
        rows, cols = grid_dims
        
        # Extract grid colors
        self.extract_grid_colors(img_start_x, img_start_y, img_end_x, img_end_y, rows, cols)
        
        # Calculate color similarities and display results
        self.calculate_and_display_results()
    
    def ask_grid_dimensions(self):
        # Create a dialog to ask for grid dimensions
        dialog = tk.Toplevel(self.root)
        dialog.title("Grid Dimensions")
        dialog.geometry("300x150")
        dialog.transient(self.root)
        dialog.grab_set()
        
        tk.Label(dialog, text="Enter grid dimensions:").pack(pady=10)
        
        frame = tk.Frame(dialog)
        frame.pack(pady=5)
        
        tk.Label(frame, text="Rows:").grid(row=0, column=0, padx=5, pady=5)
        rows_var = tk.StringVar(value="8")  # Default rows (A-H)
        rows_entry = tk.Entry(frame, textvariable=rows_var, width=5)
        rows_entry.grid(row=0, column=1, padx=5, pady=5)
        
        tk.Label(frame, text="Columns:").grid(row=0, column=2, padx=5, pady=5)
        cols_var = tk.StringVar(value="12")  # Default columns (1-12)
        cols_entry = tk.Entry(frame, textvariable=cols_var, width=5)
        cols_entry.grid(row=0, column=3, padx=5, pady=5)
        
        result = [None]
        
        def on_ok():
            try:
                rows = int(rows_var.get())
                cols = int(cols_var.get())
                if rows <= 0 or cols <= 0:
                    raise ValueError("Values must be positive")
                result[0] = (rows, cols)
                dialog.destroy()
            except ValueError as e:
                messagebox.showerror("Error", f"Invalid input: {str(e)}")
        
        def on_cancel():
            dialog.destroy()
        
        btn_frame = tk.Frame(dialog)
        btn_frame.pack(pady=10)
        
        tk.Button(btn_frame, text="OK", command=on_ok).pack(side=tk.LEFT, padx=10)
        tk.Button(btn_frame, text="Cancel", command=on_cancel).pack(side=tk.LEFT, padx=10)
        
        # Wait for dialog to close
        self.root.wait_window(dialog)
        
        return result[0]
    
    def extract_grid_colors(self, start_x, start_y, end_x, end_y, rows, cols):
        # Clear old grid
        self.canvas.delete("grid")
        self.grid_colors = []
        
        # Calculate cell dimensions
        width = end_x - start_x
        height = end_y - start_y
        cell_width = width / cols
        cell_height = height / rows
        
        # Extract colors for each cell
        for row in range(rows):
            row_colors = []
            for col in range(cols):
                # Calculate cell bounds
                cell_x1 = start_x + col * cell_width
                cell_y1 = start_y + row * cell_height
                cell_x2 = cell_x1 + cell_width
                cell_y2 = cell_y1 + cell_height
                
                # Calculate center point for sampling
                center_x = int(cell_x1 + cell_width / 2)
                center_y = int(cell_y1 + cell_height / 2)
                
                # Make sure coordinates are within image bounds
                img_width, img_height = self.image.size
                center_x = max(0, min(center_x, img_width-1))
                center_y = max(0, min(center_y, img_height-1))
                
                # Sample color (average of small area)
                sample_size = 3
                x_min = max(0, center_x - sample_size)
                x_max = min(img_width - 1, center_x + sample_size)
                y_min = max(0, center_y - sample_size)
                y_max = min(img_height - 1, center_y + sample_size)
                
                colors = []
                for x in range(x_min, x_max + 1):
                    for y in range(y_min, y_max + 1):
                        try:
                            pixel = self.image.getpixel((x, y))
                            if len(pixel) > 3:  # RGBA format
                                pixel = pixel[:3]
                            colors.append(pixel)
                        except Exception as e:
                            print(f"Error sampling pixel at ({x},{y}): {str(e)}")
                
                # Average the colors
                if colors:
                    avg_color = tuple(int(sum(c[i] for c in colors) / len(colors)) for i in range(3))
                else:
                    avg_color = (128, 128, 128)  # Default gray if no colors sampled
                
                # Store color and position
                position = f"{chr(65 + row)}{col + 1}"  # A1, B2, etc.
                row_colors.append({
                    'position': position,
                    'color': avg_color,
                    'canvas_x1': self.scale_factor * cell_x1,
                    'canvas_y1': self.scale_factor * cell_y1,
                    'canvas_x2': self.scale_factor * cell_x2,
                    'canvas_y2': self.scale_factor * cell_y2
                })
                
                # Draw grid cell on canvas
                scaled_x1 = self.scale_factor * cell_x1
                scaled_y1 = self.scale_factor * cell_y1
                scaled_x2 = self.scale_factor * cell_x2
                scaled_y2 = self.scale_factor * cell_y2
                
                self.canvas.create_rectangle(
                    scaled_x1, scaled_y1, scaled_x2, scaled_y2,
                    outline="white", width=1, tags="grid"
                )
                
                # Add label
                self.canvas.create_text(
                    (scaled_x1 + scaled_x2) / 2,
                    (scaled_y1 + scaled_y2) / 2,
                    text=position,
                    fill="white",
                    font=("Arial", 8),
                    tags="grid"
                )
            
            self.grid_colors.append(row_colors)
        
        self.status_label.config(text=f"Grid analyzed: {rows} rows x {cols} columns")
    
    def calculate_and_display_results(self):
        if not self.grid_colors or not self.reference_color:
            return
        
        # Clear existing results
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        
        # Flatten grid colors into a list
        all_cells = []
        for row in self.grid_colors:
            all_cells.extend(row)
        
        # Calculate similarity for each cell
        for cell in all_cells:
            color = cell['color']
            similarity = self.calculate_color_similarity(color, self.reference_color)
            cell['similarity'] = similarity
        
        # Sort by similarity (highest first)
        all_cells.sort(key=lambda x: x['similarity'], reverse=True)
        
        # Add to treeview
        for i, cell in enumerate(all_cells):
            pos = cell['position']
            color = cell['color']
            rgb = f"({color[0]}, {color[1]}, {color[2]})"
            hex_color = f"#{color[0]:02X}{color[1]:02X}{color[2]:02X}"
            similarity = f"{cell['similarity']:.2f}%"
            
            # Add row to treeview
            item_id = self.results_tree.insert(
                "", "end", 
                values=(pos, "", rgb, hex_color, similarity)
            )
            
            # Configure tag for this item
            tag_name = f"color_{i}"
            self.results_tree.tag_configure(tag_name, background=hex_color)
            self.results_tree.item(item_id, tags=(tag_name,))
    
    def calculate_color_similarity(self, color1, color2):
        try:
            # Simple Euclidean distance in RGB space
            rgb_distance = math.sqrt(sum((c1 - c2) ** 2 for c1, c2 in zip(color1, color2)))
            max_rgb_distance = math.sqrt(3 * 255 * 255)  # Maximum possible distance
            rgb_similarity = 100 * (1 - (rgb_distance / max_rgb_distance))
            
            return rgb_similarity
            
        except Exception as e:
            print(f"Error calculating color similarity: {str(e)}")
            return 0  # Return 0% similarity on error
    
    def on_result_click(self, event):
        # Get selected item
        item_id = self.results_tree.focus()
        if not item_id:
            return
        
        # Get values
        values = self.results_tree.item(item_id, 'values')
        if not values:
            return
            
        position = values[0]
        
        # Find the corresponding cell in grid_colors
        selected_cell = None
        for row in self.grid_colors:
            for cell in row:
                if cell['position'] == position:
                    selected_cell = cell
                    break
            if selected_cell:
                break
        
        if selected_cell:
            # Highlight the cell on the canvas
            self.canvas.delete("highlight")
            self.canvas.create_rectangle(
                selected_cell['canvas_x1'], selected_cell['canvas_y1'],
                selected_cell['canvas_x2'], selected_cell['canvas_y2'],
                outline="red", width=2, tags="highlight"
            )

if __name__ == "__main__":
    print("Starting KBTG Color Analyzer")
    print("Python version:", str(Image.__version__))
    print("Current working directory:", os.getcwd())
    
    root = tk.Tk()
    app = ColorGridAnalyzer(root)
    
    # Configure window resize handler
    def on_resize(event):
        # Only handle canvas frame resizes
        if event.widget == app.canvas_frame and app.image:
            try:
                app.show_image()
            except Exception as e:
                print(f"Error in resize handler: {e}")
    
    # Bind the resize event to canvas frame, not the whole window
    app.canvas_frame.bind("<Configure>", on_resize)
    
    root.mainloop()