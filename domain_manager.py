import customtkinter as ctk
import json
import os
from tkinter import messagebox

class DomainManagerDialog(ctk.CTkToplevel):
    def __init__(self, parent, callback=None):
        super().__init__(parent)
        
        self.callback = callback
        self.title("Domain Manager")
        self.geometry("400x400")
        
        # Make dialog modal
        self.transient(parent)
        self.grab_set()
        
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Create widgets
        self.create_widgets()
        
        # Load existing domains
        self.load_domains()
        
    def create_widgets(self):
        # Title
        self.title_label = ctk.CTkLabel(
            self,
            text="Manage Domains",
            font=("Roboto", 20, "bold")
        )
        self.title_label.grid(row=0, column=0, padx=20, pady=(20, 10))
        
        # Domains frame
        self.domains_frame = ctk.CTkScrollableFrame(
            self,
            width=360,
            height=280
        )
        self.domains_frame.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        
        # Buttons frame
        self.buttons_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.buttons_frame.grid(row=2, column=0, padx=20, pady=10)
        
        # Add button
        self.add_button = ctk.CTkButton(
            self.buttons_frame,
            text="Add Domain",
            command=self.add_domain
        )
        self.add_button.grid(row=0, column=0, padx=5)
        
        # Save button
        self.save_button = ctk.CTkButton(
            self.buttons_frame,
            text="Save Changes",
            command=self.save_changes
        )
        self.save_button.grid(row=0, column=1, padx=5)
        
    def load_domains(self):
        try:
            if os.path.exists('domains.json'):
                with open('domains.json', 'r') as f:
                    self.domains_data = json.load(f)
            else:
                # Default domains if file doesn't exist
                self.domains_data = {
                    'domains': [
                        {'name': 'test\\'},
                        {'name': 'hitachi\\'},
                        {'name': 'domain\\'}
                    ]
                }
                
            # Clear existing widgets
            for widget in self.domains_frame.winfo_children():
                widget.destroy()
                
            # Create entry for each domain
            for i, domain_info in enumerate(self.domains_data['domains']):
                self.create_domain_entry(i, domain_info)
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load domains: {str(e)}")
            
    def create_domain_entry(self, index, domain_info):
        frame = ctk.CTkFrame(self.domains_frame)
        frame.pack(fill="x", padx=5, pady=5)
        
        # Domain entry
        domain_entry = ctk.CTkEntry(frame, width=300)
        domain_entry.insert(0, domain_info.get('name', ''))
        domain_entry.grid(row=0, column=0, padx=5, pady=5)
        
        # Delete button
        delete_btn = ctk.CTkButton(
            frame,
            text="X",
            width=30,
            command=lambda: self.delete_domain(frame)
        )
        delete_btn.grid(row=0, column=1, padx=5, pady=5)
        
    def add_domain(self):
        self.create_domain_entry(len(self.domains_frame.winfo_children()), {
            'name': ''
        })
        
    def delete_domain(self, frame):
        frame.destroy()
        
    def save_changes(self):
        try:
            # Collect all domains
            domains = []
            for frame in self.domains_frame.winfo_children():
                entries = [w for w in frame.winfo_children() if isinstance(w, ctk.CTkEntry)]
                if entries:
                    domain_name = entries[0].get().strip()
                    # Ensure domain ends with backslash
                    if domain_name and not domain_name.endswith('\\'):
                        domain_name += '\\'
                    domains.append({'name': domain_name})
            
            # Save to file
            with open('domains.json', 'w') as f:
                json.dump({'domains': domains}, f, indent=4)
                
            if self.callback:
                self.callback([d['name'] for d in domains])
                
            self.destroy()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save domains: {str(e)}")
