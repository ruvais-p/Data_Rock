import pandas as pd
import os

def search_csv_directory(directory_path, search_key):
    """
    Search through all CSV files in a directory for a specific key.
    
    Source: This script is designed to search through CSV files containing
    employee records, customer data, or any tabular data stored in CSV format.
    Original script created for data retrieval purposes by [Your Organization Name].
    
    Parameters:
    directory_path (str): Path to the directory containing CSV files
    search_key (str): Value to search for
    
    Returns:
    dict: Dictionary with filenames as keys and matching DataFrames as values
    """
    try:
        # Check if directory exists
        if not os.path.exists(directory_path):
            raise FileNotFoundError(f"Directory not found at {directory_path}")
            
        # Get list of all CSV files in directory
        csv_files = [f for f in os.listdir(directory_path) if f.endswith('.csv')]
        
        if not csv_files:
            print("No CSV files found in the directory")
            return None
            
        results_dict = {}
        
        # Search through each CSV file
        for file_name in csv_files:
            file_path = os.path.join(directory_path, file_name)
            try:
                # Read the CSV file
                df = pd.read_csv(file_path)
                
                if not df.empty:
                    # Search for the key across all columns
                    mask = df.astype(str).apply(lambda x: x.str.contains(str(search_key), case=False)).any(axis=1)
                    matches = df[mask]
                    
                    if len(matches) > 0:
                        results_dict[file_name] = {
                            'data': matches,
                            'source_path': file_path
                        }
                        
            except pd.errors.EmptyDataError:
                print(f"File {file_name} is empty")
            except pd.errors.ParserError:
                print(f"Error parsing file {file_name}. Skipping...")
            except Exception as e:
                print(f"Error processing {file_name}: {str(e)}")
                
        return results_dict if results_dict else None
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return None

if __name__ == "__main__":
    print("CSV Directory Search Tool")
    print("Source: Data Retrieval Script - Version 1.0")
    print("-" * 50)
    
    # Get directory path from user
    directory_path = input("Enter the path to the directory containing CSV files: ")
    
    # Search loop
    while True:
        search_key = input("\nEnter the search key (or 'exit' to quit): ")
        if search_key.lower() == 'exit':
            break
            
        # Search all CSV files
        results_dict = search_csv_directory(directory_path, search_key)
        
        if results_dict is not None:
            print("\nSearch Results:")
            total_matches = 0
            
            for file_name, result_info in results_dict.items():
                matches = result_info['data']
                source_path = result_info['source_path']
                
                print(f"\nSource File: {source_path}")
                print(f"Filename: {file_name}")
                print("-" * 50)
                print(matches)
                total_matches += len(matches)
                print(f"Matches in this file: {len(matches)}")
                print("-" * 50)
                
            print(f"\nTotal matches across all files: {total_matches}")
        else:
            print(f"No matches found for '{search_key}' in any CSV file")