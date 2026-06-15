import tkinter as tk
from tkinter import filedialog, scrolledtext
import threading    
import sys  
import os   

from parser import parse_pdf
from normalizer import normalize_all
from sheets_writer import write_to_sheets

os.environ['TKINTER_NATIVE_FILE_DIALOG'] = '0'

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("AMS Work Order Extractor")
        self.root.resizable(False, False)

        # ── Layout ────────────────────────────────────────────────────────
        frame = tk.Frame(root, padx=20, pady=20)
        frame.pack()

        # Title label
        tk.Label(
            frame,
            text="AMS Work Order Extractor",
            font=("Helvetica", 16, "bold")
        ).grid(row=0, column=0, columnspan=2, pady=(0, 15))

        # File selection button
        self.select_btn = tk.Button(
            frame,
            text="Select PDF Files",
            width=20,
            command=self.select_file,
        )
        self.select_btn.grid(row=1, column=0, pady=(0, 10))

        # Selected file label
        self.file_label = tk.Label(
            frame,
            text="No files selected",
            fg="gray",
            width=35,
            anchor="w"
        )
        self.file_label.grid(row=2, column=1,)

        # Run button
        self.run_btn = tk.Button(
            frame,
            text="Run Extraction",
            width=20,
            state="disabled",     # only enabled after files are selected
            command=self.run_extraction,
        )
        self.run_btn.grid(row=3, column=0, columnspan=2, pady=(15, 10))

        # Log window
        self.log = scrolledtext.ScrolledText(frame,
            width=60,
            height=20,
            state="disabled",    # read only
            font=("Courier", 10)
        )
        self.log.grid(row=4, column=0, columnspan=2)

        # Store selected file path
        self.pdf_path = None

    def select_file(self):
        """Open a file picker dialog filtered to PDF files"""
        path = filedialog.askopenfilenames(
            title="Select Work Order PDF",
            filetypes=[("PDF Files", "*.pdf")]
        )
        # Handle both string and tuple returns
        if isinstance(path, tuple):
            path = path[0] if path else None

        if path:
            self.pdf_path = path
            self.file_label.config(
                text=os.path.basename(path),
                fg="black"
            )
            self.run_btn.config(state="normal")
            self.log_message(f"Selected: {os.path.basename(path)}\n")

    def log_message(self, message):
        """Write a message to the log window"""
        self.log.config(state="normal")
        self.log.insert(tk.END, message)
        self.log.see(tk.END)  # auto-scroll to bottom
        self.log.config(state="disabled")

    def run_extraction(self):
        """
        Run the full pipeline in a background thread so the ui 
        doesn't freeze while processing large PDF's
        """
        # Disable buttons while running
        self.run_btn.config(state="disabled")
        self.select_btn.config(state="disabled")     
        self.log_message("\n── Starting Extraction ──\n")

        # Run in background thread
        thread = threading.Thread(target=self.pipeline)
        thread.daemon = True
        thread.start()

    def pipeline(self):
        """The full extraction pipeline - runs in background thread."""
        try:
            # Step 1 - Parse
            self.log_message(f"Opening {os.path.basename(self.pdf_path[0])}...\n")
            parsed, errors = parse_pdf(self.pdf_path)

            self.log_message(f"Found {len(parsed)} WO header page(s).\n")

            for err in errors:
                self.log_message(f"  ⚠ Page {err['page_number']}: {err['error']}\n")

            # Step 2 - Normalize
            master_rows, flagged_rows = normalize_all(parsed)

            # Step 3 - Write to Sheets
            self.log_message("Connecting to Google Sheets...\n")    

            # Redirect print output to log window
            original_print = sys.stdout
            sys.stdout = PrintRedirector(self.log_message)

            write_to_sheets(master_rows, flagged_rows)

            sys.stdout = original_print

        except Exception as e:
            self.log_message(f"\n✗ Error: {e}\n")

        finally:
             # Re-enable buttons when done
             self.root.after(0, self.reset_buttons)
        
    def reset_buttons(self):
            """Re-enable buttons after pipeline finishes."""
            self.run_btn.config(state="normal")
            self.select_btn.config(state="normal")
            self.log_message("\n── Ready ──\n")

class PrintRedirector:
            """
            Redrects print() output from sheets_writer.py into the
            log window of the terminal.
            """
            def __init__(self, log_func):
                self.log_func = log_func

            def write(self, message):
                if message.strip():
                     self.log_func(message + "\n")
            
            def flush(self):
                pass

if __name__ == "__main__": 
    root = tk.Tk()
    app = App(root)
    root.mainloop()
          