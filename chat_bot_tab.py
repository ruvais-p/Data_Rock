import customtkinter as ctk
from tkinter import messagebox, filedialog
import requests
import json
import os

class ChatbotUI:
    def __init__(self, parent):
        self.parent = parent
        
        # Configure main grid
        self.parent.grid_rowconfigure(0, weight=1)  # Make chat display expandable
        self.parent.grid_columnconfigure(0, weight=1)
        
        # Chat display area
        self.chat_display = ctk.CTkTextbox(
            self.parent,
            height=400
        )
        self.chat_display.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        # Configure text tags for different colors
        self.chat_display.tag_config("system", foreground="red")
        self.chat_display.tag_config("user", foreground="yellow")
        self.chat_display.tag_config("bot", foreground="white")
        
        # Input frame at bottom
        self.input_frame = ctk.CTkFrame(self.parent)
        self.input_frame.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
        self.input_frame.grid_columnconfigure(0, weight=1)  # Make input field expandable
        
        # Message entry and send button
        self.message_entry = ctk.CTkEntry(
            self.input_frame,
            placeholder_text="Type your message here..."
        )
        self.message_entry.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        
        self.send_button = ctk.CTkButton(
            self.input_frame,
            text="Send",
            command=self.send_message
        )
        self.send_button.grid(row=0, column=1, padx=5, pady=5)
        
        # Bind Enter key to send message
        self.message_entry.bind("<Return>", lambda event: self.send_message())
        
        # Conversation history for context
        self.conversation = []
        
        # Add initial system message
        self.add_message("System", "Llama 3.2 chatbot initialized. You can send text messages.", "system")
        
    def send_message(self):
        """Handle sending messages"""
        message = self.message_entry.get().strip()
        if not message:
            messagebox.showwarning("Warning", "Please enter a message!")
            return
            
        # Add user message to chat
        self.add_message("You", message, "user")
        
        # Get response from Llama
        response = self.get_llama_response(message)
        
        # Add response to chat
        if response:
            self.add_message("Bot", response, "bot")
        else:
            self.add_message("System", "Failed to get response from Llama model", "system")
            
        # Clear input field
        self.message_entry.delete(0, 'end')
    
    def get_llama_response(self, prompt):
        """Get response from Llama 3.2 model for text-only input"""
        try:
            url = "http://localhost:11434/api/chat"
            payload = {
                "model": "llama3.2-vision",  # Changed from llama3.2-vision to llama3.2
                "messages": self.conversation + [{"role": "user", "content": prompt}],
                "stream": False
            }
            
            response = requests.post(url, json=payload)
            
            if response.status_code == 200:
                result = response.json()
                message = result.get("message", {}).get("content", "No response")
                
                # Update conversation history
                self.conversation.append({"role": "user", "content": prompt})
                self.conversation.append({"role": "assistant", "content": message})
                
                # Keep conversation history manageable
                if len(self.conversation) > 10:
                    self.conversation = self.conversation[-10:]
                    
                return message
            else:
                return f"Error: {response.status_code} - {response.text}"
                
        except Exception as e:
            return f"Error connecting to Llama model: {str(e)}"
    
    def add_message(self, sender, message, message_type):
        """Add a message to the chat display with appropriate color"""
        self.chat_display.insert("end", f"{sender}: ", message_type)
        self.chat_display.insert("end", f"{message}\n\n", message_type)
        self.chat_display.see("end")