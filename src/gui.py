import os
import datetime
import sys
import customtkinter as ctk
import tkinter.filedialog as filedialog

# Add current dir to sys path so imports work seamlessly 
# whether run from main.py or directly from src/
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Member 1's module (Attendance processing)
# Expected to take a file path and return a cleaned pandas DataFrame.
from attendance import process_attendance

# Member 2's module (Marks processing)
# Expected to take a file path and return a cleaned pandas DataFrame.
from marks import process_marks

# My module (Member 3 - Excel Generation)
from report_generator import generate_report

# ---------------------------------------------------------
# GLOBAL CONFIGURATION
# ---------------------------------------------------------
# Set the overall look and feel of the application
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class AutomationApp(ctk.CTk):
    """
    Main application class for the Student Performance & Attendance Automation Suite.
    Handles the UI layout and user interactions.
    Data Flow: Browse -> path stored -> Generate clicked -> validate ->
    process_attendance -> process_marks -> generate_report -> log result.
    """
    
    def __init__(self):
        super().__init__()

        # Basic window setup
        self.title("Student Performance & Attendance Automation Suite")
        self.geometry("800x600")

        # Variables to store the selected file/folder paths
        self.attendance_path = ""
        self.marks_path = ""
        self.output_folder = ""

        # Construct the layout
        self._build_layout()

    def _build_layout(self):
        """
        Builds the complete UI layout, separated logically into:
        1. Input Rows (Attendance CSV, Marks CSV, Output Folder)
        2. Action Button (Generate Report)
        3. Log/Status Box
        """
        # Outer frame for padding and clean layout
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # ---------------------------------------------------------
        # ROW 1: Attendance CSV
        # ---------------------------------------------------------
        row1 = ctk.CTkFrame(main_frame, fg_color="transparent")
        row1.pack(fill="x", pady=(0, 10))

        lbl_att = ctk.CTkLabel(row1, text="Attendance CSV:", width=120, anchor="w")
        lbl_att.pack(side="left", padx=(0, 10))

        self.entry_att = ctk.CTkEntry(row1, placeholder_text="Select Attendance File...", state="disabled")
        self.entry_att.pack(side="left", fill="x", expand=True, padx=(0, 10))

        btn_att = ctk.CTkButton(row1, text="Browse", width=100, command=self._browse_attendance)
        btn_att.pack(side="right")

        # ---------------------------------------------------------
        # ROW 2: Marks CSV
        # ---------------------------------------------------------
        row2 = ctk.CTkFrame(main_frame, fg_color="transparent")
        row2.pack(fill="x", pady=(0, 10))

        lbl_marks = ctk.CTkLabel(row2, text="Marks CSV:", width=120, anchor="w")
        lbl_marks.pack(side="left", padx=(0, 10))

        self.entry_marks = ctk.CTkEntry(row2, placeholder_text="Select Marks File...", state="disabled")
        self.entry_marks.pack(side="left", fill="x", expand=True, padx=(0, 10))

        btn_marks = ctk.CTkButton(row2, text="Browse", width=100, command=self._browse_marks)
        btn_marks.pack(side="right")

        # ---------------------------------------------------------
        # ROW 3: Output Folder
        # ---------------------------------------------------------
        row3 = ctk.CTkFrame(main_frame, fg_color="transparent")
        row3.pack(fill="x", pady=(0, 20))

        lbl_out = ctk.CTkLabel(row3, text="Output Folder:", width=120, anchor="w")
        lbl_out.pack(side="left", padx=(0, 10))

        self.entry_out = ctk.CTkEntry(row3, placeholder_text="Select Output Directory...", state="disabled")
        self.entry_out.pack(side="left", fill="x", expand=True, padx=(0, 10))

        btn_out = ctk.CTkButton(row3, text="Browse", width=100, command=self._browse_output)
        btn_out.pack(side="right")

        # ---------------------------------------------------------
        # ACTION BUTTON
        # ---------------------------------------------------------
        self.btn_generate = ctk.CTkButton(
            main_frame, 
            text="Generate Report", 
            font=ctk.CTkFont(size=16, weight="bold"), 
            height=40,
            command=self.on_generate_report # wired up to logic
        )
        self.btn_generate.pack(fill="x", pady=(0, 20))

        # ---------------------------------------------------------
        # LOG / STATUS TEXTBOX
        # ---------------------------------------------------------
        lbl_log = ctk.CTkLabel(main_frame, text="Execution Logs:", anchor="w")
        lbl_log.pack(fill="x", pady=(0, 5))

        self.log_box = ctk.CTkTextbox(main_frame, state="disabled")
        self.log_box.pack(fill="both", expand=True)

    # ---------------------------------------------------------
    # UI EVENT HANDLERS
    # ---------------------------------------------------------
    
    def _update_entry(self, entry: ctk.CTkEntry, text: str):
        """Helper to update a readonly entry with the selected path."""
        entry.configure(state="normal")
        entry.delete(0, "end")
        entry.insert(0, text)
        entry.configure(state="disabled")

    def _browse_attendance(self):
        """Opens a file dialog for the Attendance CSV/XLSX and stores the path."""
        file_path = filedialog.askopenfilename(
            title="Select Attendance File",
            filetypes=[("Data Files", "*.csv *.xlsx"), ("All Files", "*.*")]
        )
        if file_path:
            self.attendance_path = file_path
            self._update_entry(self.entry_att, file_path)

    def _browse_marks(self):
        """Opens a file dialog for the Marks CSV/XLSX and stores the path."""
        file_path = filedialog.askopenfilename(
            title="Select Marks File",
            filetypes=[("Data Files", "*.csv *.xlsx"), ("All Files", "*.*")]
        )
        if file_path:
            self.marks_path = file_path
            self._update_entry(self.entry_marks, file_path)

    def _browse_output(self):
        """Opens a directory dialog for the Output Folder and stores the path."""
        dir_path = filedialog.askdirectory(title="Select Output Folder")
        if dir_path:
            self.output_folder = dir_path
            self._update_entry(self.entry_out, dir_path)

    def _log(self, message: str):
        """
        Helper method to log messages to the UI textbox safely.
        - Enables the textbox
        - Inserts timestamped message
        - Disables the textbox
        - Auto-scrolls to the end
        """
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}\n"
        
        self.log_box.configure(state="normal")
        self.log_box.insert("end", formatted_message)
        self.log_box.configure(state="disabled")
        self.log_box.see("end")

    def on_generate_report(self):
        """
        Main logic execution (Step 2).
        Validates inputs, processes data sequentially (Attendance -> Marks),
        and generates the final report. The UI may freeze briefly during processing.
        """
        # 1. Validate inputs
        if not self.attendance_path or not self.marks_path or not self.output_folder:
            self._log("Error: Please select all three inputs before generating.")
            return

        # 2. Process Attendance Data (Member 1)
        self._log("Processing attendance data...")
        try:
            attendance_df = process_attendance(self.attendance_path)
        except Exception as e:
            self._log(f"Error processing attendance: {str(e)}")
            return
            
        # 3. Process Marks Data (Member 2)
        self._log("Processing marks data...")
        try:
            # Unpack the tuple of 3 DataFrames returned by process_marks
            marks_summary_df, marks_toppers_df, marks_at_risk_df = process_marks(self.marks_path)
            
            # Note: marks_toppers_df and marks_at_risk_df are unused for now,
            # but available if report_generator.py is extended to include them later.
        except Exception as e:
            self._log(f"Error processing marks: {str(e)}")
            return
            
        # 4. Generate Excel Report (Member 3)
        self._log("Generating Excel report...")
        output_path = os.path.join(self.output_folder, "Class_Report.xlsx")
        try:
            generate_report(attendance_df, marks_summary_df, output_path)
        except Exception as e:
            self._log(f"Error generating report: {str(e)}")
            return
            
        # 5. Success Confirmation
        self._log(f"\u2713 Report generated: {output_path}")


def run_app():
    """Entry point function called by main.py"""
    app = AutomationApp()
    app.mainloop()

if __name__ == "__main__":
    run_app()
