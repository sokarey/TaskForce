import customtkinter as ctk
import json
import os
from tkinter import messagebox

class PathManagerDialog(ctk.CTkToplevel):
    def __init__(self, parent, callback=None):
        super().__init__(parent)
        
        self.callback = callback
        self.title("Application Paths Manager")
        self.geometry("600x400")
        
        # Make dialog modal
        self.transient(parent)
        self.grab_set()
        
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Create widgets
        self.create_widgets()
        
        # Load existing paths
        self.load_paths()
        
    def create_widgets(self):
        # Title
        self.title_label = ctk.CTkLabel(
            self,
            text="Manage Application Paths",
            font=("Roboto", 20, "bold")
        )
        self.title_label.grid(row=0, column=0, padx=20, pady=(20, 10))
        
        # Paths frame
        self.paths_frame = ctk.CTkScrollableFrame(
            self,
            width=560,
            height=280
        )
        self.paths_frame.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        
        # Buttons frame
        self.buttons_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.buttons_frame.grid(row=2, column=0, padx=20, pady=10)
        
        # Add button
        self.add_button = ctk.CTkButton(
            self.buttons_frame,
            text="Add Path",
            command=self.add_path
        )
        self.add_button.grid(row=0, column=0, padx=5)
        
        # Save button
        self.save_button = ctk.CTkButton(
            self.buttons_frame,
            text="Save Changes",
            command=self.save_changes
        )
        self.save_button.grid(row=0, column=1, padx=5)
        
    def load_paths(self):
        try:
            with open('app_paths.json', 'r') as f:
                self.paths_data = json.load(f)
                
            # Clear existing widgets
            for widget in self.paths_frame.winfo_children():
                widget.destroy()
                
            # Create entry for each path
            for i, path_info in enumerate(self.paths_data['paths']):
                self.create_path_entry(i, path_info)
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load paths: {str(e)}")
            
    def create_path_entry(self, index, path_info):
        frame = ctk.CTkFrame(self.paths_frame)
        frame.pack(fill="x", padx=5, pady=5)
        
        # Name entry
        name_label = ctk.CTkLabel(frame, text="Name:")
        name_label.grid(row=0, column=0, padx=5, pady=5)
        
        name_entry = ctk.CTkEntry(frame, width=150)
        name_entry.insert(0, path_info.get('name', ''))
        name_entry.grid(row=0, column=1, padx=5, pady=5)
        
        # Path entry
        path_label = ctk.CTkLabel(frame, text="Path:")
        path_label.grid(row=0, column=2, padx=5, pady=5)
        
        path_entry = ctk.CTkEntry(frame, width=250)
        path_entry.insert(0, path_info.get('path', ''))
        path_entry.grid(row=0, column=3, padx=5, pady=5)
        
        # Delete button
        delete_btn = ctk.CTkButton(
            frame,
            text="X",
            width=30,
            command=lambda: self.delete_path(frame)
        )
        delete_btn.grid(row=0, column=4, padx=5, pady=5)
        
    def add_path(self):
        self.create_path_entry(len(self.paths_frame.winfo_children()), {
            'name': '',
            'path': '',
            'description': ''
        })
        
    def delete_path(self, frame):
        frame.destroy()
        
    def save_changes(self):
        try:
            # Collect all paths
            paths = []
            for frame in self.paths_frame.winfo_children():
                entries = [w for w in frame.winfo_children() if isinstance(w, ctk.CTkEntry)]
                if len(entries) >= 2:
                    paths.append({
                        'name': entries[0].get(),
                        'path': entries[1].get(),
                        'description': ''
                    })
            
            # Save to file
            with open('app_paths.json', 'w') as f:
                json.dump({'paths': paths}, f, indent=4)
                
            if self.callback:
                self.callback(paths)
                
            self.destroy()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save paths: {str(e)}")
