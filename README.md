# Student Performance & Attendance Automation Suite

A desktop Python application built for processing student data. It imports raw attendance and marks data, processes them, and automatically generates a formatted, multi-sheet Excel report with native charts.

## Team Member Assignments (Task Distribution)

This project is designed to be built collaboratively by a 3-person team. Here is the suggested distribution of work to ensure equal contribution:

### 👤 Member 1: Data Engineer (Attendance Focus)
**Primary Responsibility:** Handling the attendance logic and project scaffolding.
- **`src/attendance.py`**: Develop the logic to parse attendance files, clean the data, calculate per-student attendance percentages, and flag students falling below thresholds (e.g., <75%).
- **`main.py`**: Set up the initial entry point of the application.
- **Data Scaffolding**: Create the initial `data/sample_attendance.csv` and `data/sample_marks.csv` files to establish the data schema for the team.

### 👤 Member 2: Data Engineer (Performance Focus)
**Primary Responsibility:** Handling the marks processing and analytics logic.
- **`src/marks.py`**: Develop the logic to parse marks files, compute subject-wise totals, calculate overall averages, assign grades (A+, A, B, etc.), and determine pass/fail status.
- **Analytics**: Identify class rank, toppers, and at-risk students within the `marks.py` module.
- **Dependencies**: Manage the `requirements.txt` file as new libraries (like pandas) are added.

### 👤 Member 3: UI & Reporting Specialist
**Primary Responsibility:** User interface and Excel report generation.
- **`src/report_generator.py`**: Use `openpyxl` to take the DataFrames produced by Members 1 & 2 and write them into a multi-sheet Excel file. Add conditional formatting (red for fails/low attendance) and generate native Excel charts.
- **`src/gui.py`**: Build the graphical interface using `CustomTkinter`. Connect the UI buttons to the backend pipeline, ensuring file dialogs work and the GUI remains responsive using threading.

## Setup Instructions

1. Clone or download the repository.
2. Ensure Python 3.8+ is installed.
3. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the application:
   ```bash
   python main.py
   ```
