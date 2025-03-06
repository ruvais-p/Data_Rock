import customtkinter as ctk
from tkinter import messagebox
import os
from documents_pdf_ppt import initialize_models, load_or_create_faiss, create_qa_chain, get_response

class DocumentsTab:
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
        
        # Chat display area
        self.chat_display = ctk.CTkTextbox(self.parent, state="disabled")
        self.chat_display.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        
        # Configure text tags for colors
        self.chat_display.tag_config("system", foreground="red")
        self.chat_display.tag_config("user", foreground="yellow")
        self.chat_display.tag_config("assistant", foreground="white")
        
        # Question input frame
        self.input_frame = ctk.CTkFrame(self.parent)
        self.input_frame.grid(row=2, column=0, padx=10, pady=10, sticky="ew")
        self.input_frame.grid_columnconfigure(0, weight=1)
        
        # Question entry and ask button
        self.question_entry = ctk.CTkEntry(self.input_frame, placeholder_text="Enter your question")
        self.question_entry.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        
        self.ask_button = ctk.CTkButton(
            self.input_frame, 
            text="Ask", 
            command=self.ask_question
        )
        self.ask_button.grid(row=0, column=1, padx=5, pady=5)
        
        # Connection state
        self.is_connected = False
        self.llm_model, self.embedding_model = initialize_models()
        self.db = None
        self.qa_chain = None

    def toggle_connection(self):
        directory = self.dir_entry.get()
        
        if not self.is_connected:
            # Check if directory exists
            if os.path.isdir(directory):
                self.is_connected = True
                self.connect_button.configure(text="Stop", fg_color="red")
                self.add_message("System", "Connected to directory: " + directory, "system")
                self.add_message("System", "Loading and processing documents...", "system")
                
                # Load or create FAISS index
                faiss_index_path = os.path.join(directory, "faiss_index")
                self.db = load_or_create_faiss(directory, faiss_index_path, self.embedding_model)
                if self.db:
                    self.qa_chain = create_qa_chain(self.db, self.llm_model)
                    self.add_message("System", "Documents loaded successfully. You can now ask questions.", "system")
                else:
                    self.add_message("System", "Failed to load documents.", "system")
                    self.is_connected = False
                    self.connect_button.configure(text="Connect", fg_color="green")
            else:
                messagebox.showerror("Error", "Invalid directory path!")
        else:
            self.is_connected = False
            self.connect_button.configure(text="Connect", fg_color="green")
            self.add_message("System", "Disconnected from directory", "system")
            self.db = None
            self.qa_chain = None

    def ask_question(self):
        if not self.is_connected:
            messagebox.showwarning("Warning", "Please connect to a directory first!")
            return
            
        question = self.question_entry.get()
        if question:
            self.add_message("User", question, "user")
            if self.qa_chain:
                response, sources = get_response(self.qa_chain, question, self.db)
                output_final = "Response: \n"+("-" * 50)+"\n"+ response + "\n"+("-" * 50)+"\n"
                # Display response
                self.add_message("Assistant", output_final, "assistant")
                
                # Display sources if available
                if sources:
                    output_final_source = "Sources:\n"
                    for source in sources:
                        output_final_source += (source + "\n")
                    self.add_message("Assistant", output_final_source, "assistant")
            else:
                self.add_message("Assistant", "Failed to process the question. Please try again.", "assistant")
            self.question_entry.delete(0, 'end')
        
    def add_message(self, sender, message, tag):
        """Add a message to the chat display with the specified color tag."""
        self.chat_display.configure(state="normal")
        self.chat_display.insert("end", f"{sender}: {message}\n\n", tag)
        self.chat_display.configure(state="disabled")
        self.chat_display.see("end")