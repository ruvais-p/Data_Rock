import customtkinter as ctk
from documents_tab import DocumentsTab
from csv_tab import CSVTab
from sql_tab import SQLTab
from chat_bot_tab import ChatbotUI

class TabbedApplication(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Configure window
        self.title("IParse")
        self.geometry("1200x1000")
        
        # Create and configure grid layout
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Create TabView with 500px width
        self.tabview = ctk.CTkTabview(self, width=500)
        self.tabview.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        
        # Create tabs
        self.tab1 = self.tabview.add("Documents")
        self.tab2 = self.tabview.add("CSV")
        self.tab3 = self.tabview.add("SQL")
        self.tab4 = self.tabview.add("Chat bot")
        
        # Initialize Documents tab UI
        self.documents_tab = DocumentsTab(self.tab1)
        self.csv_tab = CSVTab(self.tab2)
        self.sql_tab = SQLTab(self.tab3)
        self.chat_bot_tab = ChatbotUI(self.tab4)

if __name__ == "__main__":
    app = TabbedApplication()
    app.mainloop()
