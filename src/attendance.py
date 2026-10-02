"""
Attendance Processing Module

This module is responsible for processing raw student attendance files 
(e.g., CSV or Excel) and transforming them into a clean, per-student 
summary DataFrame. It handles tasks such as calculating overall attendance 
percentages and flagging students who fall below required thresholds.
"""

import pandas as pd
import os

def process_attendance(file_path: str, threshold: float = 75.0) -> pd.DataFrame:
    """
    Process a raw attendance file into a per-student summary DataFrame.
    
    This function performs the following pipeline:
    1. Validates file existence and extension (.csv, .xlsx, .xls).
    2. Reads the file into a DataFrame, handling potential read errors.
    3. Validates that all required columns are present.
    4. Standardizes the 'Status' column (lowercase, stripped).
    5. Groups data by student to compute total classes and attended classes.
    6. Calculates the final attendance percentage and a low attendance flag.

    Args:
        file_path: path to the attendance .csv or .xlsx file to process
        threshold: attendance percentage below which a student is flagged
                   as low attendance (default 75.0)

    Returns:
        pd.DataFrame: A per-student attendance summary containing:
                      StudentID, Name, Total_Classes, Classes_Attended,
                      Attendance_Percent, Low_Attendance_Flag
    """
    # 1. Check if file exists
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Attendance file not found: {file_path}")
        
    # 2. Determine extension and read file
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()
    
    try:
        if ext == '.csv':
            df = pd.read_csv(file_path)
        elif ext in ['.xlsx', '.xls']:
            df = pd.read_excel(file_path)
        else:
            raise ValueError(f"Unsupported file type '{ext}'. Only .csv and .xlsx/.xls files are supported.")
    except Exception as e:
        raise RuntimeError(f"Error reading the attendance file '{file_path}': {str(e)}")
        
    # 3. Verify required columns exist
    required_cols = ['StudentID', 'Name', 'Date', 'Status']
    missing_cols = list(set(required_cols) - set(df.columns))
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
        
    # 4. Standardize the Status column
    df['Status'] = df['Status'].astype(str).str.strip().str.lower()
    
    # 5. Handle empty DataFrame edge case
    if df.empty:
        return pd.DataFrame(columns=[
            'StudentID', 'Name', 'Total_Classes', 
            'Classes_Attended', 'Attendance_Percent', 'Low_Attendance_Flag'
        ])

    # 6. Groupby and aggregations (Week 3)
    # We create a helper column to easily sum up present days based on the cleaned Status
    df['Is_Present'] = (df['Status'] == 'present').astype(int)
    
    # Group by student ID and Name
    summary_df = df.groupby(['StudentID', 'Name']).agg(
        Total_Classes=('Status', 'count'),
        Classes_Attended=('Is_Present', 'sum')
    ).reset_index()
    
    # Calculate Attendance_Percent and round to 2 decimal places
    summary_df['Attendance_Percent'] = (summary_df['Classes_Attended'] / summary_df['Total_Classes'] * 100).round(2)
    
    # Create Low_Attendance_Flag boolean column based on threshold
    summary_df['Low_Attendance_Flag'] = summary_df['Attendance_Percent'] < threshold
        
    # 7. Return the finalized summary DataFrame
    return summary_df

if __name__ == "__main__":
    # __main__ block for comprehensive testing of Week 3 logic
    import tempfile
    
    # Create a dummy CSV with multiple rows per student
    dummy_data = {
        'StudentID': [101, 101, 101, 101, 102, 102, 102, 102, 103, 103, 103, 103],
        'Name': ['Alice', 'Alice', 'Alice', 'Alice', 'Bob', 'Bob', 'Bob', 'Bob', 'Charlie', 'Charlie', 'Charlie', 'Charlie'],
        'Date': ['2023-01-01', '2023-01-02', '2023-01-03', '2023-01-04'] * 3,
        'Status': ['Present', ' present ', 'Absent', 'present',   # Alice: 3/4 = 75%
                   'absent', 'Absent ', 'absent', 'absent',      # Bob: 0/4 = 0% (Low Attendance)
                   ' PRESENT', 'present', 'present', 'present']  # Charlie: 4/4 = 100%
    }
    dummy_df = pd.DataFrame(dummy_data)
    
    # Save to a temporary file
    temp_csv = os.path.join(tempfile.gettempdir(), 'test_attendance_week3.csv')
    dummy_df.to_csv(temp_csv, index=False)
    
    try:
        print("Testing process_attendance with Week 3 calculation logic...")
        result_df = process_attendance(temp_csv, threshold=75.0)
        print("\n--- Final Summary DataFrame ---")
        print(result_df.to_string(index=False))
        print("-------------------------------")
    except Exception as e:
        print(f"Test failed with error: {e}")
    finally:
        # Clean up temporary file
        if os.path.exists(temp_csv):
            os.remove(temp_csv)
