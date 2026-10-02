"""
Marks & Analytics Engine

This module processes raw marks files (e.g., CSV or Excel) into a consolidated 
summary DataFrame and derived analytics. It calculates totals, assigns grades, 
and identifies toppers and at-risk students for final reporting.
"""

import pandas as pd
import numpy as np
import os

def _assign_grade(percent: float, pass_percentage: float) -> str:
    """
    Helper function to map an overall percentage to a letter grade.
    The viva grading scale is: A+ (>=90), A (>=75), B (>=60), 
    C (>=50), D (>= pass_percentage), F (below pass_percentage).
    """
    if pd.isna(percent):
        return "F"
    if percent >= 90:
        return "A+"
    elif percent >= 75:
        return "A"
    elif percent >= 60:
        return "B"
    elif percent >= 50:
        return "C"
    elif percent >= pass_percentage:
        return "D"
    else:
        return "F"

def process_marks(file_path: str, pass_percentage: float = 40.0) -> tuple:
    """
    Process a raw marks file into three summary DataFrames.

    Pipeline:
    1. Validation: Checks if the file exists and has a supported extension.
    2. Column Verification: Ensures the DataFrame has all required columns 
       before processing to prevent KeyError down the line.
    3. Numeric Coercion: Safely converts Marks/MaxMarks to numeric types.
       Any bad data (like text or blanks) is coerced to NaN and filled with 0
       so the pipeline doesn't crash on dirty data.
    4. Calculations: Computes row-level Subject_Percent, then aggregates to 
       find Total_Marks and Overall_Percent. Assigns Grades, ranks, and a 
       Pass/Fail status based on both overall score and individual subjects.
    5. Final Output: Derives toppers (Top 3) and at-risk students (Grade F)
       from the calculated summary DataFrame.

    Args:
        file_path: path to the marks .csv or .xlsx file to process
        pass_percentage: minimum overall percentage required to pass
                          (used in a later calculation step)

    Returns:
        tuple: (summary_df, toppers_df, at_risk_df)
    """
    # 1. Check if the file exists on disk
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Marks file not found: {file_path}")
        
    # 2. Determine the file extension to decide how to read it
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()
    
    try:
        if ext == '.csv':
            # Read CSV files
            df = pd.read_csv(file_path)
        elif ext in ['.xlsx', '.xls']:
            # Read Excel files
            df = pd.read_excel(file_path)
        else:
            raise ValueError(f"Unsupported file type '{ext}'. Only .csv and .xlsx/.xls files are supported.")
    except Exception as e:
        raise RuntimeError(f"Error reading the marks file '{file_path}': {str(e)}")
        
    # 3. Verify required columns exist before operating on them
    required_cols = ['StudentID', 'Name', 'Subject', 'Marks', 'MaxMarks']
    missing_cols = list(set(required_cols) - set(df.columns))
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")

    # 4. Convert Marks and MaxMarks to numeric types
    df["Marks"] = pd.to_numeric(df["Marks"], errors="coerce").fillna(0)
    df["MaxMarks"] = pd.to_numeric(df["MaxMarks"], errors="coerce").fillna(0)

    # ---------------------------------------------------------
    # CALCULATIONS
    # ---------------------------------------------------------

    # 5. Row-level calculations (Subject_Percent)
    # Guard against division by zero using np.where: if MaxMarks > 0, compute normally, else 0
    df["Subject_Percent"] = np.where(df["MaxMarks"] > 0, (df["Marks"] / df["MaxMarks"]) * 100, 0)
    df["Subject_Percent"] = df["Subject_Percent"].round(2)
    
    # Helper column to identify if they failed this specific subject
    df["Failed_Subject"] = df["Subject_Percent"] < pass_percentage

    # If the dataframe is empty after reading, skip calculations to avoid crashing on groupby
    if df.empty:
        summary_df = pd.DataFrame(columns=[
            'StudentID', 'Name', 'Total_Marks', 'Total_MaxMarks', 
            'Overall_Percent', 'Grade', 'Final_Status', 'Class_Rank'
        ])
    else:
        # 6. Group by Student to compute totals
        summary_df = df.groupby(['StudentID', 'Name']).agg(
            Total_Marks=('Marks', 'sum'),
            Total_MaxMarks=('MaxMarks', 'sum'),
            Any_Subject_Failed=('Failed_Subject', 'any') # True if any row had Failed_Subject == True
        ).reset_index()

        # 7. Overall Percent
        summary_df["Overall_Percent"] = np.where(
            summary_df["Total_MaxMarks"] > 0, 
            (summary_df["Total_Marks"] / summary_df["Total_MaxMarks"]) * 100, 
            0
        )
        summary_df["Overall_Percent"] = summary_df["Overall_Percent"].round(2)

        # 8. Grade Assignment via .apply()
        summary_df["Grade"] = summary_df["Overall_Percent"].apply(
            lambda p: _assign_grade(p, pass_percentage)
        )

        # 9. Final_Status (Pass/Fail)
        summary_df["Final_Status"] = np.where(
            (summary_df["Any_Subject_Failed"] == True) | (summary_df["Overall_Percent"] < pass_percentage),
            "Fail",
            "Pass"
        )
        summary_df = summary_df.drop(columns=["Any_Subject_Failed"]) # Clean up helper column

        # 10. Class Rank
        summary_df["Class_Rank"] = summary_df["Overall_Percent"].rank(ascending=False, method="min").astype(int)

    # ---------------------------------------------------------
    # FINAL RETURN LOGIC
    # ---------------------------------------------------------
    
    # We derive toppers and at-risk students directly from the calculated summary_df.
    # This is much more efficient than recalculating overall scores from scratch,
    # ensuring data consistency across the reporting pipeline.

    # 1. Build toppers_df (Top 3 ranks)
    toppers_df = summary_df[summary_df["Class_Rank"] <= 3].sort_values(by="Class_Rank", ascending=True).reset_index(drop=True)

    # 2. Build at_risk_df (Students with an 'F' Grade)
    at_risk_df = summary_df[summary_df["Grade"] == "F"].reset_index(drop=True)

    # 3. Final Output Tuple
    return summary_df, toppers_df, at_risk_df


if __name__ == "__main__":
    # __main__ block for comprehensive testing of final output
    import tempfile
    
    # Dummy data with clear distinctions for testing Toppers and At-Risk logic
    dummy_data = {
        'StudentID': [101, 101, 102, 102, 103, 103, 104, 104, 105, 105],
        'Name': ['Alice', 'Alice', 'Bob', 'Bob', 'Charlie', 'Charlie', 'Diana', 'Diana', 'Eve', 'Eve'],
        'Subject': ['Math', 'Science', 'Math', 'Science', 'Math', 'Science', 'Math', 'Science', 'Math', 'Science'],
        'Marks': [95, 98,    # Alice: 193/200 (96.5% Rank 1)
                  45, 90,    # Bob: 135/200 (67.5% Fail Math -> Fail overall)
                  80, 85,    # Charlie: 165/200 (82.5% Rank 3)
                  30, 20,    # Diana: 50/200 (25% Grade F)
                  90, 88],   # Eve: 178/200 (89.0% Rank 2)
        'MaxMarks': [100, 100, 100, 100, 100, 100, 100, 100, 100, 100]
    }
    dummy_df = pd.DataFrame(dummy_data)
    
    temp_csv = os.path.join(tempfile.gettempdir(), 'test_marks_final.csv')
    dummy_df.to_csv(temp_csv, index=False)
    
    try:
        print("Testing final process_marks logic...")
        
        # We test with pass_percentage=50.0
        summary_df, toppers_df, at_risk_df = process_marks(temp_csv, pass_percentage=50.0)
        
        print("\n--- Summary DataFrame ---")
        print(summary_df.to_string(index=False))
        
        print("\n--- Toppers DataFrame (Rank <= 3) ---")
        print(toppers_df.to_string(index=False))
        
        print("\n--- At-Risk DataFrame (Grade F) ---")
        print(at_risk_df.to_string(index=False))
        print("---------------------------------")
        
    except Exception as e:
        print(f"Test failed with error: {e}")
    finally:
        if os.path.exists(temp_csv):
            os.remove(temp_csv)
