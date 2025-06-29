import pandas as pd
import os
import re
from sqlalchemy import create_engine
from urllib.parse import quote_plus # Added for URL-encoding password

def load_and_combine_data(folder_path):
    """
    Loads data from both multi-sheet Excel files (Forest and Grassland),
    extracts data from all sheets, and combines them into a single DataFrame.
    """
    all_data = []
    
    excel_files = {
        'FOREST': 'Bird_Monitoring_Data_FOREST.XLSX',
        'GRASSLAND': 'Bird_Monitoring_Data_GRASSLAND.XLSX'
    }

    for location_type, filename_excel in excel_files.items():
        file_path = os.path.join(folder_path, filename_excel)
        
        if not os.path.exists(file_path):
            print(f"Error: Excel file '{filename_excel}' not found at '{file_path}'. Please ensure it's in the project folder.")
            continue

        print(f"Reading all sheets from '{filename_excel}' for {location_type} data...")
        try:
            # Read all sheets from the Excel file
            # sheet_name=None reads all sheets into a dictionary of DataFrames
            excel_sheets_dict = pd.read_excel(file_path, sheet_name=None, engine='openpyxl')
            
            for sheet_name, df_sheet in excel_sheets_dict.items():
                # Add Location_Type from the Excel file's context
                df_sheet['Location_Type'] = location_type.capitalize() # 'Forest' or 'Grassland'
                
                # The sheet name itself is the Admin_Unit_Code
                df_sheet['Admin_Unit_Code'] = sheet_name 
                
                all_data.append(df_sheet)
                print(f"  - Loaded sheet: '{sheet_name}' ({df_sheet.shape[0]} rows)")

        except Exception as e:
            print(f"Error reading Excel file {filename_excel}: {e}")
    
    if not all_data:
        print("No data was loaded from Excel files. Please check file names and paths.")
        return pd.DataFrame() # Return empty DataFrame if no data

    combined_df = pd.concat(all_data, ignore_index=True)
    return combined_df

def initial_data_cleaning(df):
    """
    Performs initial data cleaning steps.
    """
    print("Initial shape:", df.shape)
    
    # Drop duplicate rows to ensure unique observations
    df.drop_duplicates(inplace=True)
    print("Shape after dropping duplicates:", df.shape)

    # Convert 'Date' column to proper datetime objects, explicitly specifying format
    # Based on previous warning, assuming DD-MM-YYYY format (e.g., 25-01-2023)
    df['Date'] = pd.to_datetime(df['Date'], format='%d-%m-%Y', errors='coerce') 
    
    # Handle boolean-like strings to actual booleans (True/False)
    for col in ['Flyover_Observed', 'PIF_Watchlist_Status', 'Regional_Stewardship_Status']:
        if col in df.columns:
            df[col] = df[col].astype(str).str.upper().map({'TRUE': True, 'FALSE': False}).fillna(False)

    # Convert numerical columns, handling missing/invalid data
    numeric_cols = ['Temperature', 'Humidity', 'Initial_Three_Min_Cnt', 'AcceptedTSN', 'AOU_Code', 'Visit']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce') # Convert to number, put NaN for errors
            
            if col in ['Initial_Three_Min_Cnt', 'Visit']:
                df[col] = df[col].fillna(0).astype(int) # For counts/visits, fill missing with 0 and convert to integer
            elif col in ['AcceptedTSN', 'AOU_Code']:
                df[col] = df[col].fillna(-1).astype(int) # For codes, fill missing with -1 and convert to integer
            else:
                # For Temperature/Humidity, fill missing with the mean of the column
                if not df[col].isnull().all():
                    df[col] = df[col].fillna(df[col].mean())
                else:
                    df[col] = df[col].fillna(0) # Or another sensible default if all are NaN

    # Fill missing categorical values with 'Unknown' for consistency
    categorical_cols = [
        'Sex', 'ID_Method', 'Distance', 'Sky', 'Wind', 'Disturbance',
        'Common_Name', 'Scientific_Name', 'Sub_Unit_Code', 'Site_Name',
        'Plot_Name', 'Observer', 'Interval_Length', 'NPSTaxonCode',
        'TaxonCode', 'Previously_Obs'
    ]
    for col in categorical_cols:
        if col in df.columns:
            df[col] = df[col].fillna('Unknown')
    
    # Ensure 'Year' column is correctly inferred or derived from 'Date' if missing
    # Assuming 'Year' is primarily from original data, but can cross-check with 'Date'
    if 'Year' not in df.columns and 'Date' in df.columns:
        df['Year'] = df['Date'].dt.year.fillna(0).astype(int)
    
    print("Shape after initial cleaning:", df.shape)
    return df

def upload_to_sql(df):
    """
    Uploads the DataFrame to a PostgreSQL database.
    """
    # --- PostgreSQL Connection Details ---
    # These values are based on your confirmed setup:
    PG_USERNAME = 'postgres'          # Your confirmed username
    PG_PASSWORD = 'Roshan@2025'       # Your confirmed password
    PG_HOST = 'localhost'             # Your confirmed host
    PG_PORT = '5432'                  # Your confirmed port
    PG_DB_NAME = 'bird_analysis_db'    # Your confirmed database name

    # URL-encode the password to handle special characters like '@'
    encoded_password = quote_plus(PG_PASSWORD)

    # Construct the connection string using the encoded password
    db_connection_str = f'postgresql://{PG_USERNAME}:{encoded_password}@{PG_HOST}:{PG_PORT}/{PG_DB_NAME}'
    engine = create_engine(db_connection_str)
    
    print(f"Uploading data to PostgreSQL database: {PG_DB_NAME}...")
    try:
        # 'replace' will delete the table if it exists and create a new one.
        df.to_sql('bird_observations', engine, if_exists='replace', index=False, chunksize=1000)
        print("Data uploaded successfully to PostgreSQL.")
    except Exception as e:
        print(f"Error uploading data to PostgreSQL: {e}")
        print("Please ensure your PostgreSQL server is running and connection details in this script are correct.")
        print(f"Attempted connection string (without password shown): postgresql://{PG_USERNAME}:*****@{PG_HOST}:{PG_PORT}/{PG_DB_NAME}")

if __name__ == "__main__":
    current_directory = os.getcwd()
    
    print("Starting data ingestion and cleaning process...")
    combined_df = load_and_combine_data(current_directory)

    if not combined_df.empty:
        print("Performing initial data cleaning...")
        cleaned_df = initial_data_cleaning(combined_df.copy())
        
        print("\n--- Data Cleaning Summary ---")
        print(cleaned_df.info())
        print("\nMissing values after cleaning (should be few or none for key columns):")
        print(cleaned_df.isnull().sum()[cleaned_df.isnull().sum() > 0])
        
        # Save the cleaned data to CSV as a backup (this CSV will NOT be re-processed in future runs)
        cleaned_df.to_csv('cleaned_bird_observations.csv', index=False)
        print("\nCleaned data saved to 'cleaned_bird_observations.csv'")

        upload_to_sql(cleaned_df)
    else:
        print("No data was loaded. Please check if Excel files are in the correct directory and named correctly.")