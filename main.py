import tkinter as tk
from tkinter import ttk, scrolledtext
import customtkinter as ctk
import requests
import io
import json
from PIL import Image, ImageTk
import threading
from datetime import datetime
import os
import base64

class TextToImageGenerator:
    def __init__(self):
        # Set theme and appearance
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Initialize main window
        self.window = ctk.CTk()
        self.window.title("AI Text to Image Generator")
        self.window.geometry("1200x800")
        
        # Configure grid
        self.window.grid_columnconfigure(1, weight=1)
        self.window.grid_rowconfigure(0, weight=1)
        
        self.create_widgets()
        self.setup_api()
        
    def setup_api(self):
        # Hugging Face API setup
        self.API_URL = "https://api-inference.huggingface.co/models/ZB-Tech/Text-to-Image"
        # IMPORTANT: Replace with your actual Hugging Face token
        self.headers = {"Authorization": "Enter token here"}
        
    def create_widgets(self):
        # Create left panel for controls
        left_panel = ctk.CTkFrame(self.window, width=300)
        left_panel.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        # Title
        title_label = ctk.CTkLabel(left_panel, 
                                 text="Text to Image Generator",
                                 font=("Helvetica", 20, "bold"))
        title_label.pack(pady=20)
        
        # Prompt input
        prompt_label = ctk.CTkLabel(left_panel, text="Enter your prompt:")
        prompt_label.pack(pady=5)
        
        self.prompt_text = ctk.CTkTextbox(left_panel, height=100)
        self.prompt_text.pack(padx=10, pady=5, fill="x")
        
        # Advanced settings frame
        settings_frame = ctk.CTkFrame(left_panel)
        settings_frame.pack(padx=10, pady=10, fill="x")
        
        # Image size selection
        size_label = ctk.CTkLabel(settings_frame, text="Image Size:")
        size_label.pack(pady=5)
        
        self.size_var = ctk.StringVar(value="512x512")
        size_options = ["256x256", "512x512", "768x768"]
        size_menu = ctk.CTkOptionMenu(settings_frame, 
                                    values=size_options,
                                    variable=self.size_var)
        size_menu.pack(pady=5)
        
        # Generate button
        self.generate_button = ctk.CTkButton(left_panel,
                                           text="Generate Image",
                                           command=self.generate_image)
        self.generate_button.pack(pady=20)
        
        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(left_panel)
        self.progress_bar.pack(pady=10, padx=10, fill="x")
        self.progress_bar.set(0)
        
        # Status label
        self.status_label = ctk.CTkLabel(left_panel, text="Ready")
        self.status_label.pack(pady=5)
        
        # Create right panel for image display
        right_panel = ctk.CTkFrame(self.window)
        right_panel.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        
        # Image display area
        self.image_frame = ctk.CTkFrame(right_panel)
        self.image_frame.pack(expand=True, fill="both", padx=10, pady=10)
        
        # Save button (initially hidden)
        self.save_button = ctk.CTkButton(right_panel,
                                       text="Save Image",
                                       command=self.save_image)
        self.save_button.pack(pady=10)
        self.save_button.pack_forget()
        
    def generate_image(self):
        # Disable generate button and show progress
        self.generate_button.configure(state="disabled")
        self.status_label.configure(text="Generating image...")
        self.progress_bar.set(0)
        self.progress_bar.start()
        
        # Get prompt text
        prompt = self.prompt_text.get("1.0", tk.END).strip()
        
        if not prompt:
            self.status_label.configure(text="Please enter a prompt")
            self.generate_button.configure(state="normal")
            self.progress_bar.stop()
            return
        
        # Start generation in separate thread
        thread = threading.Thread(target=self.generate_image_thread, args=(prompt,))
        thread.start()
        
    def generate_image_thread(self, prompt):
        try:
            # Prepare payload
            payload = {
                "inputs": prompt,
                "parameters": {
                    "num_inference_steps": 50,
                    "guidance_scale": 7.5,
                    "width": int(self.size_var.get().split('x')[0]),
                    "height": int(self.size_var.get().split('x')[1])
                }
            }
            
            # Make API request
            response = requests.post(self.API_URL, headers=self.headers, json=payload)
            
            if response.status_code != 200:
                raise Exception(f"API request failed with status code: {response.status_code}")
            
            # Process response
            image_bytes = response.content
            image = Image.open(io.BytesIO(image_bytes))
            
            # Display image
            self.window.after(0, self.display_image, image)
            
        except Exception as e:
            self.window.after(0, self.handle_error, str(e))
        
    def display_image(self, image):
        # Resize image to fit display area while maintaining aspect ratio
        display_size = (800, 600)
        image.thumbnail(display_size, Image.Resampling.LANCZOS)
        
        # Convert to PhotoImage
        photo = ImageTk.PhotoImage(image)
        
        # Clear previous image
        for widget in self.image_frame.winfo_children():
            widget.destroy()
        
        # Create new image label without text
        image_label = ctk.CTkLabel(self.image_frame, text="", image=photo)
        image_label.image = photo  # Keep reference
        image_label.pack(expand=True)
        
        # Show save button
        self.save_button.pack(pady=10)
        
        # Reset UI
        self.generate_button.configure(state="normal")
        self.progress_bar.stop()
        self.progress_bar.set(1)
        self.status_label.configure(text="Image generated successfully!")
        
    def save_image(self):
        # Create images directory if it doesn't exist
        if not os.path.exists("generated_images"):
            os.makedirs("generated_images")
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"generated_images/image_{timestamp}.png"
        
        # Get the currently displayed image
        image_label = self.image_frame.winfo_children()[0]
        image = ImageTk.getimage(image_label.image)
        
        # Save image
        image.save(filename)
        self.status_label.configure(text=f"Image saved as {filename}")
        
    def handle_error(self, error_message):
        self.status_label.configure(text=f"Error: {error_message}")
        self.generate_button.configure(state="normal")
        self.progress_bar.stop()
        self.progress_bar.set(0)
        
    def run(self):
        self.window.mainloop()

if __name__ == "__main__":
    app = TextToImageGenerator()
    app.run()
