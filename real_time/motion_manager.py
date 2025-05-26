import customtkinter as ctk
from database import MotionDatabase
import threading

class MotionSelectionDialog(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        
        self.title("Select Motion")
        self.geometry("500x400") # Set initial size
        self.resizable(False, False) # Prevent resizing
        
        # Make dialog modal
        self.transient(parent)
        self.grab_set()
        
        # Initialize database
        self.db = MotionDatabase()
        
        # Selected motion ID
        self.selected_motion_id = None
        
        # Create UI elements
        self.create_widgets()
        
        # Load motions
        self.load_motions()
        
    def create_widgets(self):
        # Motion list
        self.list_frame = ctk.CTkFrame(self)
        self.list_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Motion list label
        self.list_label = ctk.CTkLabel(self.list_frame, text="Available Motions:", anchor="w")
        self.list_label.pack(anchor="w", padx=5, pady=5)
        
        # Motion listbox (using CTkScrollableFrame as workaround)
        self.scrollable_frame = ctk.CTkScrollableFrame(self.list_frame)
        self.scrollable_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Button frame
        self.button_frame = ctk.CTkFrame(self)
        self.button_frame.pack(fill="x", padx=10, pady=10)
        
        # Buttons
        self.cancel_button = ctk.CTkButton(self.button_frame, text="Cancel", command=self.on_cancel)
        self.cancel_button.pack(side="left", padx=5, pady=5)
        
        self.select_button = ctk.CTkButton(self.button_frame, text="Select Motion", command=self.on_select)
        self.select_button.pack(side="right", padx=5, pady=5)
        
        # Motion info frame
        self.info_frame = ctk.CTkFrame(self)
        self.info_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        self.motion_info_label = ctk.CTkLabel(self.info_frame, text="No motion selected", anchor="w")
        self.motion_info_label.pack(anchor="w", padx=5, pady=5)
        
    def load_motions(self):
        # Clear existing widgets
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
            
        # Get motions from database
        self.motions = self.db.get_motions_list()
        
        if not self.motions:
            label = ctk.CTkLabel(self.scrollable_frame, text="No motions found in database", anchor="w")
            label.pack(anchor="w", pady=2)
            return
            
        # Create radio buttons for each motion
        self.motion_var = ctk.StringVar(value="")
        
        for motion in self.motions:
            radio = ctk.CTkRadioButton(
                self.scrollable_frame,
                text=f"{motion['name']} ({motion['frame_count']} frames)",
                variable=self.motion_var,
                value=str(motion['id']),
                command=lambda m=motion: self.on_motion_selected(m)
            )
            radio.pack(anchor="w", pady=2)
            
    def on_motion_selected(self, motion):
        """Update info when a motion is selected"""
        self.motion_info_label.configure(
            text=f"Selected: {motion['name']}\nCategory: {motion['category']}\nFrames: {motion['frame_count']}"
        )
        self.selected_motion_id = motion['id']
        
    def on_select(self):
        """Confirm selection and close dialog"""
        if not self.selected_motion_id:
            return
            
        self.grab_release()
        self.destroy()
        
    def on_cancel(self):
        """Cancel selection"""
        self.selected_motion_id = None
        self.grab_release()
        self.destroy()