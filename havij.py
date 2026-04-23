import tkinter as tk
from tkinter import scrolledtext, messagebox
import subprocess
import threading
import sys
import os
import re

class AdvancedScannerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Havij Pro - Database Extraction Tool")
        self.root.geometry("950x750")
        self.root.configure(bg="#f0f0f0")
        
        # --- Top Frame (URL Input & Analyze Button) ---
        top_frame = tk.LabelFrame(root, text=" Target Information ", font=("Arial", 10, "bold"), pady=10, padx=10)
        top_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(top_frame, text="URL:").grid(row=0, column=0, sticky="w")
        
        self.url_entry = tk.Entry(top_frame, font=("Arial", 11), width=70)
        self.url_entry.grid(row=0, column=1, padx=10, sticky="we")
        
        # Default Boxy/3D "Analyze" Button
        analyze_btn = tk.Button(top_frame, text="Analyze", width=12, command=self.get_dbs, font=("Arial", 10, "bold"))
        analyze_btn.grid(row=0, column=2, padx=5)

        # --- Middle Frame (Data Extraction) ---
        mid_frame = tk.LabelFrame(root, text=" Data Extraction (Select & Dump) ", font=("Arial", 10, "bold"), pady=10, padx=10)
        mid_frame.pack(fill=tk.X, padx=10, pady=5)

        # Row 0: Database & Table
        tk.Label(mid_frame, text="Database (-D):").grid(row=0, column=0, sticky="w")
        self.db_entry = tk.Entry(mid_frame, width=30)
        self.db_entry.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(mid_frame, text="Table (-T):").grid(row=0, column=2, sticky="w")
        self.table_entry = tk.Entry(mid_frame, width=30)
        self.table_entry.grid(row=0, column=3, padx=5, pady=5)

        # Row 1: Columns
        tk.Label(mid_frame, text="Columns (-C):").grid(row=1, column=0, sticky="w")
        self.col_entry = tk.Entry(mid_frame, width=30)
        self.col_entry.grid(row=1, column=1, padx=5, pady=5)
        tk.Label(mid_frame, text="(Use comma for multiple: id,user,pass)", font=("Arial", 8), fg="gray").grid(row=1, column=2, columnspan=2, sticky="w")

        # Row 2: Options
        self.batch_var = tk.BooleanVar(value=True)
        tk.Checkbutton(mid_frame, text="Auto Mode [Auto Yes to all prompts]", variable=self.batch_var).grid(row=2, column=0, columnspan=4, sticky="w", pady=5)

        # Row 3: Action Buttons (No Colors, Default 3D Look)
        btn_frame = tk.Frame(mid_frame)
        btn_frame.grid(row=3, column=0, columnspan=4, pady=15)

        actions = [
            ("Get Tables", self.get_tables),
            ("Get Columns", self.get_columns),
            ("Get Data", self.get_data),
            ("Clear All", self.clear_all)
        ]

        for text, cmd in actions:
            btn = tk.Button(btn_frame, text=text, width=12, command=cmd, font=("Arial", 10, "bold"))
            btn.pack(side=tk.LEFT, padx=8)

        # --- Output Log ---
        bottom_frame = tk.LabelFrame(root, text=" Process Output Log ", font=("Arial", 10, "bold"), pady=5, padx=5)
        bottom_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.output_area = scrolledtext.ScrolledText(bottom_frame, wrap=tk.WORD, font=("Consolas", 10), bg="black")
        self.output_area.pack(fill=tk.BOTH, expand=True)

        # Terminal Colors
        self.output_area.tag_config('blue', foreground='#5DADE2') 
        self.output_area.tag_config('green', foreground='#00FF00') 
        self.output_area.tag_config('red', foreground='#FF4136') 

    def get_engine_path(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(current_dir, "sqlmap.py")

    def run_command(self, extra_args):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("URL Missing", "Please enter target URL first.")
            return

        engine_path = self.get_engine_path()
        if not os.path.exists(engine_path):
            messagebox.showerror("Error", "Core engine file not found in the same folder!")
            return

        command = [sys.executable, engine_path, "-u", url]
        if self.batch_var.get():
            command.append("--batch")
        
        command.extend(extra_args)

        self.output_area.insert(tk.END, f"\n[>] Initializing Engine Process...\n", 'blue')
        self.output_area.see(tk.END)
        
        thread = threading.Thread(target=self.execute_engine, args=(command,))
        thread.daemon = True
        thread.start()

    def execute_engine(self, command):
        try:
            flags = 0
            if sys.platform == "win32":
                flags = subprocess.CREATE_NO_WINDOW

            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, creationflags=flags)
            
            for line in process.stdout:
                self.root.after(0, self.update_output, line)
            process.wait()
            self.root.after(0, self.update_output, "\n--- Task Finished ---\n", 'blue')
        except Exception as e:
            self.root.after(0, self.update_output, f"\nError: {str(e)}\n", 'red')

    def update_output(self, text, force_tag=None):
        # 1. Filter out SQLMap ASCII Banner
        banner_keywords = [
            "__H__", 
            "___ ___[.]_____", 
            "|_ -| . [(]", 
            "|___|_  [)]", 
            "|_|V...",
            "___ ___[(]_____",       
            "|___|_  [.]_|_|_|__,|", 
            "{1.10.3#pip}"           
        ]
        
        if text.strip() == "___":
            return
            
        if any(keyword in text for keyword in banner_keywords):
            return

        # 2. Magic Trick: Replace 'sqlmap' with 'Engine' safely
        clean_text = re.sub(r'(?i)sqlmap', 'Engine', text)

        # 3. Add Colors
        if force_tag:
            tag = force_tag
        else:
            upper_text = clean_text.upper()
            if '[!]' in clean_text or '[X]' in upper_text or 'ERROR' in upper_text or 'WARNING' in upper_text or 'CRITICAL' in upper_text:
                tag = 'red'
            elif '[*]' in clean_text or '[INFO]' in upper_text or '[+]' in clean_text or 'DEBUG' in upper_text:
                tag = 'blue'
            elif clean_text.strip() == '':
                tag = 'blue'
            else:
                tag = 'green'

        self.output_area.insert(tk.END, clean_text, tag)
        self.output_area.see(tk.END)

    # --- Button Logic ---
    def get_dbs(self):
        self.run_command(["--dbs"])

    def get_tables(self):
        db = self.db_entry.get().strip()
        if not db:
            messagebox.showinfo("Input Needed", "Please enter Database name.")
            return
        self.run_command(["-D", db, "--tables"])

    def get_columns(self):
        db = self.db_entry.get().strip()
        table = self.table_entry.get().strip()
        if not db or not table:
            messagebox.showinfo("Input Needed", "Enter Database and Table name.")
            return
        self.run_command(["-D", db, "-T", table, "--columns"])

    def get_data(self):
        db = self.db_entry.get().strip()
        table = self.table_entry.get().strip()
        cols = self.col_entry.get().strip()

        if not db or not table:
            messagebox.showinfo("Input Needed", "Enter Database and Table name to dump data.")
            return
        
        args = ["-D", db, "-T", table]
        if cols:
            args.extend(["-C", cols])
        args.append("--dump")
        
        self.run_command(args)

    def clear_all(self):
        self.url_entry.delete(0, tk.END)
        self.db_entry.delete(0, tk.END)
        self.table_entry.delete(0, tk.END)
        self.col_entry.delete(0, tk.END)
        self.output_area.delete('1.0', tk.END)

if __name__ == "__main__":
    root = tk.Tk()
    app = AdvancedScannerGUI(root)
    root.mainloop()