import mysql.connector
from tabulate import tabulate
import subprocess
import logging
from langchain_community.llms import Ollama
import sys
import getpass

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def check_ollama_models():
    """Check if required Ollama models are available."""
    try:
        output = subprocess.run(["ollama", "list"], capture_output=True, text=True)
        installed_models = output.stdout.lower()
        required_model = "llama3.2-vision" in installed_models
        if not required_model:
            logging.error("Required llama3.2-vision model is not installed")
        return required_model
    except Exception as e:
        logging.error(f"Error checking Ollama models: {str(e)}")
        return False

def initialize_model():
    """Initialize the LLM model if it exists."""
    if not check_ollama_models():
        print("Required model is missing. Please install it manually using:")
        print("ollama pull llama3.2-vision")
        return None
    try:
        llm_model = Ollama(model="llama3.2-vision")
        return llm_model
    except Exception as e:
        logging.error(f"Error initializing model: {str(e)}")
        return None

def get_database_credentials():
    """Get database credentials from user."""
    print("\nPlease enter your database credentials:")
    host = input("Host (press Enter for 'localhost'): ").strip() or "localhost"
    user = input("Username: ").strip()
    password = getpass.getpass("Password: ").strip()
    database = input("Database name: ").strip()
    return host, user, password, database

def connect_to_db(host, user, password, database):
    """Establish connection to MySQL database."""
    try:
        conn = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database
        )
        logging.info(f"Successfully connected to MySQL database '{database}'")
        return conn
    except mysql.connector.Error as err:
        logging.error(f"Database connection error: {err}")
        return None
    except Exception as e:
        logging.error(f"Unexpected error during database connection: {e}")
        return None

def get_table_schema(conn):
    """Get the schema of all tables in the database."""
    if not conn:
        return ""
    
    cursor = conn.cursor()
    schema_info = []
    
    try:
        # Get list of tables
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

def get_llm_query(llm, prompt, schema_info):
    """Get SQL query from LLM based on natural language prompt."""
    try:
        system_prompt = f"""You are a SQL query generator. Given the following database schema:

{schema_info}

Convert the following natural language prompt to a SQL query that matches the schema structure.
Only return the SQL query itself, without any explanation or markdown formatting."""
        
        full_prompt = f"{system_prompt}\n\nUser prompt: {prompt}\n\nSQL query:"
        sql_query = llm.invoke(full_prompt).strip()
        
        # Remove any markdown formatting if present
        sql_query = sql_query.replace('```sql', '').replace('```', '').strip()
        logging.info("Successfully generated SQL query from prompt")
        return sql_query
    except Exception as e:
        logging.error(f"Error getting response from LLM: {e}")
        return None

def execute_query(conn, query):
    """Execute SQL query and return results. Supports multiple statements."""
    if not conn:
        logging.error("No database connection available")
        return
    
    mycursor = conn.cursor()
    try:
        # Execute multiple statements
        for result in mycursor.execute(query, multi=True):
            if result.with_rows:
                # Handle SELECT queries
                results = result.fetchall()
                if results:
                    headers = [desc[0] for desc in result.description]
                    print("\nQuery Results:")
                    print(tabulate(results, headers=headers, tablefmt="psql"))
                else:
                    print("No records found.")
            else:
                # Handle INSERT, UPDATE, DELETE queries
                print(f"Query executed successfully. Rows affected: {result.rowcount}")
        
        conn.commit()
            
    except mysql.connector.Error as err:
        logging.error(f"MySQL error during query execution: {err}")
        conn.rollback()  # Rollback changes if there's an error
    except Exception as e:
        logging.error(f"Unexpected error during query execution: {e}")
        conn.rollback()  # Rollback changes if there's an error
    finally:
        mycursor.close()

def main():
    # Initialize LLM
    llm = initialize_model()
    if not llm:
        logging.error("Failed to initialize LLM model")
        sys.exit(1)
    
    # Get database credentials from user
    host, user, password, database = get_database_credentials()
    
    # Connect to database
    conn = connect_to_db(host, user, password, database)
    if not conn:
        logging.error("Failed to connect to database")
        sys.exit(1)
    
    # Get database schema information
    schema_info = get_table_schema(conn)
    if not schema_info:
        logging.warning("Could not fetch database schema")
    
    try:
        while True:
            print("\nEnter your prompt (type 'exit' to quit):")
            user_prompt = input().strip()
            
            if user_prompt.lower() == "exit":
                break
            
            logging.info("Generating SQL query from prompt")
            sql_query = get_llm_query(llm, user_prompt, schema_info)
            
            if sql_query:
                print(sql_query)
                execute_query(conn, sql_query)
                
            else:
                print("Failed to generate SQL query.")
                
    except KeyboardInterrupt:
        logging.info("Program interrupted by user")
    except Exception as e:
        logging.error(f"Unexpected error in main loop: {e}")
    finally:
        if conn and conn.is_connected():
            conn.close()
            logging.info("Database connection closed")

if __name__ == "__main__":
    main()
#SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE, COLUMN_TYPE, IS_NULLABLE, COLUMN_KEY FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = 'Student'; 
