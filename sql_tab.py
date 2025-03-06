import customtkinter as ctk
from tkinter import messagebox
import mysql.connector
import logging
from langchain_community.llms import Ollama
import subprocess
import threading

class SQLTab:
    def __init__(self, parent):
        self.parent = parent
        self.conn = None
        self.llm = None
        self.schema_info = None
        
        # Configure logging
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        
        # Configure tab's grid
        self.parent.grid_rowconfigure(2, weight=1)
        self.parent.grid_columnconfigure(0, weight=1)
        
        # Create connection frame
        self.connection_frame = ctk.CTkFrame(self.parent)
        self.connection_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        
        # Configure connection frame grid
        for i in range(2):
            self.connection_frame.grid_columnconfigure(i, weight=1)
        
        # Connection inputs with labels
        self.create_labeled_entry("Host:", 0, 0, "host_entry", "localhost")
        self.create_labeled_entry("Username:", 0, 1, "user_entry", "Enter username")
        self.create_labeled_entry("Password:", 1, 0, "pass_entry", "Enter password", show="*")
        self.create_labeled_entry("Database:", 1, 1, "db_entry", "Enter database name")
        
        # Connection status frame
        self.status_frame = ctk.CTkFrame(self.parent)
        self.status_frame.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="ew")
        self.status_frame.grid_columnconfigure(0, weight=1)
        
        # Connect button with status indicator
        self.connect_button = ctk.CTkButton(
            self.status_frame,
            text="Connect",
            fg_color="green",
            command=self.toggle_connection
        )
        self.connect_button.grid(row=0, column=1, padx=5, pady=5)
        
        # Status label
        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="Not connected",
            text_color="red"
        )
        self.status_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        
        # Chat display area
        self.chat_display = ctk.CTkTextbox(
            self.parent,
            state="disabled",
            height=300
        )
        self.chat_display.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")
        
        # Configure tags for different message types with colors on the underlying Text widget
        self.chat_display._textbox.tag_configure("system", foreground="#ff4444")  # Red for system messages
        self.chat_display._textbox.tag_configure("user", foreground="#ffd700")    # Yellow for user messages
        self.chat_display._textbox.tag_configure("assistant", foreground="#98fb98")  # Light green for assistant messages
        self.chat_display._textbox.tag_configure("table", foreground="#ffffff")   # White for tables
        
        # Question input frame
        self.input_frame = ctk.CTkFrame(self.parent)
        self.input_frame.grid(row=3, column=0, padx=10, pady=10, sticky="ew")
        self.input_frame.grid_columnconfigure(0, weight=1)
        
        # Question entry and buttons
        self.question_entry = ctk.CTkEntry(
            self.input_frame,
            placeholder_text="Enter your SQL query or natural language question"
        )
        self.question_entry.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        
        # Add both Direct Query and Ask AI buttons
        self.direct_query_button = ctk.CTkButton(
            self.input_frame,
            text="Direct Query",
            command=self.execute_direct_query
        )
        self.direct_query_button.grid(row=0, column=1, padx=5, pady=5)
        
        self.ask_ai_button = ctk.CTkButton(
            self.input_frame,
            text="Ask AI",
            command=self.ask_ai_question
        )
        self.ask_ai_button.grid(row=0, column=2, padx=5, pady=5)
        
        # Connection state
        self.is_connected = False
        
        # Initialize LLM in a separate thread
        threading.Thread(target=self.initialize_llm, daemon=True).start()

    def format_table(self, results, headers):
        """Display query results in a raw format (no table formatting)"""
        if not results or not headers:
            return "No data to display"
        
        # Convert headers and rows into a simple string representation
        formatted_data = []
        
        # Add headers
        formatted_data.append(" | ".join(headers))
        
        # Add rows
        for row in results:
            formatted_data.append(" | ".join(str(cell) for cell in row))
        
        return "\n".join(formatted_data)

    def initialize_llm(self):
        """Initialize the LLM model in background"""
        try:
            if self.check_ollama_models():
                self.llm = Ollama(model="llama3.2-vision")
                self.add_message("System", "AI assistant initialized successfully")
            else:
                self.add_message("System", "Warning: Required model 'llama3.2-vision' is not installed")
        except Exception as e:
            self.add_message("System", f"Error initializing AI assistant: {str(e)}")

    def check_ollama_models(self):
        """Check if required Ollama models are available"""
        try:
            output = subprocess.run(["ollama", "list"], capture_output=True, text=True)
            return "llama3.2-vision" in output.stdout.lower()
        except Exception as e:
            logging.error(f"Error checking Ollama models: {str(e)}")
            return False

    def create_labeled_entry(self, label_text, row, col, entry_name, placeholder, show=None):
        """Helper method to create a labeled entry field"""
        frame = ctk.CTkFrame(self.connection_frame)
        frame.grid(row=row, column=col, padx=5, pady=5, sticky="ew")
        frame.grid_columnconfigure(1, weight=1)
        
        label = ctk.CTkLabel(frame, text=label_text)
        label.grid(row=0, column=0, padx=5, pady=2, sticky="w")
        
        entry = ctk.CTkEntry(frame, placeholder_text=placeholder, show=show)
        entry.grid(row=0, column=1, padx=5, pady=2, sticky="ew")
        
        setattr(self, entry_name, entry)

    def connect_to_db(self):
        """Establish connection to MySQL database"""
        try:
            self.conn = mysql.connector.connect(
                host=self.host_entry.get(),
                user=self.user_entry.get(),
                password=self.pass_entry.get(),
                database=self.db_entry.get()
            )
            return True
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", f"Failed to connect to database:\n{str(err)}")
            logging.error(f"Database connection error: {err}")
            return False
        except Exception as e:
            messagebox.showerror("Error", f"Unexpected error:\n{str(e)}")
            logging.error(f"Unexpected error during database connection: {e}")
            return False

    def get_table_schema(self):
        """Get the schema of all tables in the database"""
        if not self.conn:
            return ""
        
        cursor = self.conn.cursor()
        schema_info = []
        
        try:
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            
            for table in tables:
                table_name = table[0]
                cursor.execute(f"DESCRIBE {table_name}")
                columns = cursor.fetchall()
                
                schema_info.append(f"Table: {table_name}")
                column_info = [f"- {col[0]} ({col[1]})" for col in columns]
                schema_info.extend(column_info)
                schema_info.append("")  # Empty line between tables
            
            return "\n".join(schema_info)
        except Exception as e:
            logging.error(f"Error fetching schema: {e}")
            return ""
        finally:
            cursor.close()

    def toggle_connection(self):
        """Toggle database connection state"""
        if not self.is_connected:
            if self.validate_connection() and self.connect_to_db():
                self.is_connected = True
                self.connect_button.configure(text="Disconnect", fg_color="red")
                self.status_label.configure(text="Connected", text_color="green")
                self.add_message("System", f"Connected to database: {self.db_entry.get()}")
                
                # Get schema information
                self.schema_info = self.get_table_schema()
                if self.schema_info:
                    self.add_message("System", "Database schema loaded successfully")
                
                # Disable input fields when connected
                self.toggle_input_fields("disabled")
        else:
            if self.conn:
                self.conn.close()
            self.is_connected = False
            self.conn = None
            self.schema_info = None
            self.connect_button.configure(text="Connect", fg_color="green")
            self.status_label.configure(text="Not connected", text_color="red")
            self.add_message("System", "Disconnected from database")
            
            # Enable input fields when disconnected
            self.toggle_input_fields("normal")

    def validate_connection(self):
        """Validate connection parameters"""
        fields = {
            "Host": self.host_entry.get(),
            "Username": self.user_entry.get(),
            "Password": self.pass_entry.get(),
            "Database": self.db_entry.get()
        }
        
        missing = [field for field, value in fields.items() if not value]
        
        if missing:
            messagebox.showerror(
                "Error",
                f"Please fill in all required fields:\n{', '.join(missing)}"
            )
            return False
        return True

    def toggle_input_fields(self, state):
        """Toggle the state of connection input fields"""
        self.host_entry.configure(state=state)
        self.user_entry.configure(state=state)
        self.pass_entry.configure(state=state)
        self.db_entry.configure(state=state)

    def execute_direct_query(self):
        """Execute direct SQL query"""
        if not self.is_connected:
            messagebox.showwarning("Warning", "Please connect to a database first!")
            return
            
        query = self.question_entry.get()
        if not query:
            return
            
        self.add_message("User", f"Direct Query: {query}")
        self.execute_query(query)
        self.question_entry.delete(0, 'end')

    def ask_ai_question(self):
        """Handle natural language question using AI"""
        if not self.is_connected:
            messagebox.showwarning("Warning", "Please connect to a database first!")
            return
            
        if not self.llm:
            messagebox.showwarning("Warning", "AI assistant is not initialized!")
            return
            
        question = self.question_entry.get()
        if not question:
            return
            
        self.add_message("User", f"Question: {question}")
        
        try:
            # Get SQL query from LLM
            sql_query = self.get_llm_query(question)
            if sql_query:
                self.add_message("Assistant", f"Generated SQL query:\n{sql_query}")
                self.execute_query(sql_query)
            else:
                self.add_message("Assistant", "Failed to generate SQL query")
        except Exception as e:
            self.add_message("Assistant", f"Error processing question: {str(e)}")
            
        self.question_entry.delete(0, 'end')

    def get_llm_query(self, prompt):
        """Get SQL query from LLM based on natural language prompt"""
        if not self.llm or not self.schema_info:
            return None
            
        try:
            system_prompt = f"""You are a SQL query generator. Given the following database schema:

{self.schema_info}

Convert the following natural language prompt to a SQL query that matches the schema structure.
Only return the SQL query itself, without any explanation or markdown formatting."""
            
            full_prompt = f"{system_prompt}\n\nUser prompt: {prompt}\n\nSQL query:"
            sql_query = self.llm.invoke(full_prompt).strip()
            
            # Remove any markdown formatting if present
            sql_query = sql_query.replace('```sql', '').replace('```', '').strip()
            return sql_query
        except Exception as e:
            logging.error(f"Error getting response from LLM: {e}")
            return None

    def execute_query(self, query):
        """Execute SQL query and display results with improved formatting"""
        if not self.conn:
            return
            
        cursor = self.conn.cursor()
        try:
            # Execute multiple statements
            for result in cursor.execute(query, multi=True):
                if result.with_rows:
                    # Handle SELECT queries
                    results = result.fetchall()
                    if results:
                        headers = [desc[0] for desc in result.description]
                        # Use format_table instead of tabulate
                        formatted_table = self.format_table(results, headers)
                        self.add_message("System", "Query Results:", formatted_table)
                    else:
                        self.add_message("System", "No records found.")
                else:
                    # Handle INSERT, UPDATE, DELETE queries
                    self.add_message("System", f"Query executed successfully. Rows affected: {result.rowcount}")
            
            self.conn.commit()
                
        except mysql.connector.Error as err:
            self.add_message("System", f"MySQL error: {err}")
            self.conn.rollback()
        except Exception as e:
            self.add_message("System", f"Error executing query: {e}")
            self.conn.rollback()
        finally:
            cursor.close()

    def add_message(self, sender, message, table_content=None):
        """Add a message to the chat display with appropriate styling"""
        self.chat_display.configure(state="normal")
        
        # Insert the sender with appropriate tag
        tag = sender.lower()  # "system", "user", or "assistant"
        self.chat_display._textbox.insert("end", f"{sender}: ", tag)
        
        # Insert the main message with the same tag
        self.chat_display._textbox.insert("end", f"{message}\n", tag)
        
        # If there's a table, insert it with the table tag and proper spacing
        if table_content:
            self.chat_display._textbox.insert("end", "\n", tag)  # Add spacing before table
            self.chat_display._textbox.insert("end", table_content, "table")
            self.chat_display._textbox.insert("end", "\n", tag)  # Add spacing after table
        
        # Add extra newline for spacing between messages
        self.chat_display._textbox.insert("end", "\n")
        
        self.chat_display.configure(state="disabled")
        self.chat_display.see("end")