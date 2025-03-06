import customtkinter as ctk
from tkinter import messagebox
import os
from csv_data_retrieval import search_csv_directory
import pandas as pd

class CSVTab:
    def __init__(self, parent):
        self.parent = parent
        
        # Configure tab's grid
        self.parent.grid_rowconfigure(1, weight=1)  # Chat display area
        self.parent.grid_columnconfigure(0, weight=1)
        
        # Create directory selection frame
        self.dir_frame = ctk.CTkFrame(self.parent)
        self.dir_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        self.dir_frame.grid_columnconfigure(0, weight=1)
        
        # Directory entry and connect button
        self.dir_entry = ctk.CTkEntry(self.dir_frame, placeholder_text="Enter directory path")
        self.dir_entry.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        
        self.connect_button = ctk.CTkButton(
            self.dir_frame, 
            text="Connect", 
            fg_color="green", 
            command=self.toggle_connection
        )
        self.connect_button.grid(row=0, column=1, padx=5, pady=5)
        
        # Chat display area - using CTkTextbox for colored text
        self.chat_display = ctk.CTkTextbox(self.parent)
        self.chat_display.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        
        # Configure text tags for different colors
        self.chat_display.tag_config("system", foreground="red")
        self.chat_display.tag_config("user", foreground="yellow")
        self.chat_display.tag_config("result", foreground="white")
        
        # Question input frame
        self.input_frame = ctk.CTkFrame(self.parent)
        self.input_frame.grid(row=2, column=0, padx=10, pady=10, sticky="ew")
        self.input_frame.grid_columnconfigure(0, weight=1)
        
        # Question entry and ask button
        self.question_entry = ctk.CTkEntry(self.input_frame, placeholder_text="Enter search term")
        self.question_entry.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        
        self.ask_button = ctk.CTkButton(
            self.input_frame, 
            text="Search", 
            command=self.search_csv_files
        )
        self.ask_button.grid(row=0, column=1, padx=5, pady=5)
        
        # Connection state
        self.is_connected = False
        self.directory_path = None

    def toggle_connection(self):
        directory = self.dir_entry.get()
        
        if not self.is_connected:
            # Check if directory exists
            if os.path.isdir(directory):
                self.is_connected = True
                self.directory_path = directory
                self.connect_button.configure(text="Disconnect", fg_color="red")
                
                # Get CSV files count
                csv_files = [f for f in os.listdir(directory) if f.endswith('.csv')]
                self.add_message("System", f"Connected to directory: {directory}", "system")
                self.add_message("System", f"Found {len(csv_files)} CSV files", "system")
            else:
                messagebox.showerror("Error", "Invalid directory path!")
        else:
            self.is_connected = False
            self.directory_path = None
            self.connect_button.configure(text="Connect", fg_color="green")
            self.add_message("System", "Disconnected from directory", "system")

    def search_csv_files(self):
        if not self.is_connected:
            messagebox.showwarning("Warning", "Please connect to a directory first!")
            return
            
        search_term = self.question_entry.get()
        if not search_term:
            messagebox.showwarning("Warning", "Please enter a search term!")
            return
            
        self.add_message("User", f"Searching for: {search_term}", "user")
        
        # Call the search function from csv_data_retrieval.py
        results_dict = search_csv_directory(self.directory_path, search_term)
        
        if results_dict is not None:
            total_matches = 0
            
            for file_name, result_info in results_dict.items():
                matches = result_info['data']
                source_path = result_info['source_path']
                
                self.add_message("System", f"File: {file_name}", "system")
                self.add_message("System", f"Path: {source_path}", "system")
                self.add_message("System", f"Matches: {len(matches)}", "system")
                
                # Display the matches in a formatted way
                self.display_dataframe(matches)
                
                total_matches += len(matches)
            
            self.add_message("System", f"Total matches across all files: {total_matches}", "system")
        else:
            self.add_message("System", f"No matches found for '{search_term}' in any CSV file", "system")
            
        self.question_entry.delete(0, 'end')
        
    def display_dataframe(self, df):
        """Display a pandas DataFrame in the chat display area with white color"""
        if not isinstance(df, pd.DataFrame) or df.empty:
            return
            
        # Format DataFrame as string with fixed width columns
        df_string = df.to_string()
        
        # Add the formatted DataFrame to the chat display
        self.chat_display.insert("end", "-" * 50 + "\n", "result")
        self.chat_display.insert("end", df_string + "\n", "result")
        self.chat_display.insert("end", "-" * 50 + "\n\n", "result")
        self.chat_display.see("end")
        
    def add_message(self, sender, message, message_type):
        """
        Add a message to the chat display with appropriate color
        
        Parameters:
        sender (str): Who sent the message
        message (str): The message content
        message_type (str): Type of message - "system", "user", or "result"
        """
        self.chat_display.insert("end", f"{sender}: {message}\n", message_type)
        self.chat_display.see("end")