#!/usr/bin/env python3
"""
hourlies.py - Hourly Work Logger Application
A Windows application to log work done each hour throughout the day.
"""

import platformdirs
import pygetwindow as gw


import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import os
import sys
import json
import threading
import time
from datetime import datetime, timedelta
import subprocess
from pathlib import Path

class Config:
    """Handle application configuration"""
    def __init__(self):
        self.appname = "hourlies"
        self.orgname = "mbeware"
        self.default_config_dir = str(platformdirs.user_config_path(self.appname,self.orgname) )
        self.config_file = f"{self.default_config_dir}\\hourlies_config.json"
        self.default_config = {
            "worklog_folder": os.path.join(str(platformdirs.user_data_path(self.appname,self.orgname)), "hourlies"),
            "popup_at_minute": 0,
            "window_width": 600,
            "window_height": 400
        }
        self.config = self.load_config()


    def get_default_config_directory(self):
        if os.name == "nt":  # Windows
            appdata = os.getenv("LOCALAPPDATA")
            if appdata:
                return appdata
            appdata = os.getenv("APPDATA")
            if appdata:
                return appdata
            return None
        else:  # Unix-like systems (Linux, macOS)
            xdg_config_home = os.getenv("XDG_CONFIG_HOME")
            if xdg_config_home:
                return xdg_config_home
            return os.path.join(os.path.expanduser("~"), ".config")   
        
    def load_config(self):
        """Load configuration from file or create default"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    # Merge with defaults for any missing keys
                    for key, value in self.default_config.items():
                        if key not in config:
                            config[key] = value
                    return config
            except:
                return self.default_config.copy()
        else:
            self.save_config(self.default_config)
            return self.default_config.copy()
    
    def save_config(self, config=None):
        """Save configuration to file"""
        if config is None:
            config = self.config
        os.makedirs(self.default_config_dir, exist_ok=True)
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=4)
    
    def get(self, key, default=None):
        """Get configuration value"""
        return self.config.get(key, default)
    
    def edit_config(self):
        """Open config file in default editor"""
        if sys.platform == "win32":
            os.startfile(self.config_file)
        else:
            subprocess.call(["xdg-open", self.config_file])

class HourlyWorklogWindow:
    """Window for entering hourly work log"""
    def __init__(self, parent, day_folder, callback=None):
        self.parent = parent
        self.day_folder = day_folder
        self.callback = callback
        self.window = None
        self.text_widget = None
        
    def show(self):
        """Show the hourly worklog window"""

        # Get a list of all windows
        windows = gw.getAllWindows()
        # Minimize each window
        for window in windows:
            window.minimize()

        if self.window is not None and self.window.winfo_exists():
            self.window.lift()
            self.window.focus_force()
            return
            
        self.window = tk.Toplevel(self.parent)
        self.window.title("Hourly Worklog Entry")
        self.window.geometry("600x400")
        
        # Make window stay on top
        self.window.attributes('-topmost', True)
        self.window.focus_force()
        
        # Main frame
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.window.columnconfigure(0, weight=1)
        self.window.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Label
        label = ttk.Label(main_frame, text="Hourly Work (What did you do in the last hour?):")
        label.grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        
        # Text entry field
        self.text_widget = scrolledtext.ScrolledText(main_frame, wrap=tk.WORD, width=70, height=15)
        self.text_widget.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        self.text_widget.focus_set()
        
        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, sticky=(tk.W, tk.E))
        
        # Same as last hour button
        same_button = ttk.Button(button_frame, text="Same as last hour", 
                                command=self.same_as_last_hour)
        same_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # Save button
        save_button = ttk.Button(button_frame, text="Save", command=self.save_entry)
        save_button.pack(side=tk.LEFT)
        
        # Bind Enter key to save
        self.window.bind('<Control-Return>', lambda e: self.save_entry())
        
        # Handle window close
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)
    
    def get_last_entry(self):
        """Get the content of the last hourly entry"""
        if not os.path.exists(self.day_folder):
            return None
            
        files = [f for f in os.listdir(self.day_folder) if f.endswith('.hourlies')]
        if not files:
            return None
            
        files.sort()
        last_file = os.path.join(self.day_folder, files[-1])
        
        try:
            with open(last_file, 'r', encoding='utf-8') as f:
                return f.read()
        except:
            return None
    
    def same_as_last_hour(self):
        """Fill the text field with the same content as last hour"""
        last_entry = self.get_last_entry()
        if last_entry:
            self.text_widget.delete('1.0', tk.END)
            self.text_widget.insert('1.0', last_entry)
        else:
            messagebox.showinfo("No Previous Entry", "No previous entry found for today.")
    
    def save_entry(self):
        """Save the hourly work entry"""
        content = self.text_widget.get('1.0', tk.END).strip()
        
        if not content:
            result = messagebox.askyesno("Empty Entry", "Use same as last hour?")
            if result:
                last_entry = self.get_last_entry()
                if last_entry:
                    content = last_entry
                else:
                    messagebox.showwarning("No Previous Entry", 
                                         "No previous entry found. Please enter your work.")
                    self.text_widget.focus_set()
                    return
            else:
                self.text_widget.focus_set()
                return
        
        # Create day folder if it doesn't exist
        os.makedirs(self.day_folder, exist_ok=True)
        
        # Generate filename
        now = datetime.now()
        base_filename = now.strftime("%Y%m%d%H%M")
        filename = f"{base_filename}.hourlies"
        filepath = os.path.join(self.day_folder, filename)
        
        # Handle duplicate filenames
        minute_offset = 0
        while os.path.exists(filepath):
            minute_offset += 1
            adjusted_time = now + timedelta(minutes=minute_offset)
            filename = adjusted_time.strftime("%Y%m%d%H%M") + ".hourlies"
            filepath = os.path.join(self.day_folder, filename)
        
        # Save the file
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.window.destroy()
            self.window = None
            
            if self.callback:
                self.callback()
                
        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save entry: {str(e)}")
    
    def on_close(self):
        """Handle window close event"""
        self.window.destroy()
        self.window = None

class HourliesApp:
    """Main application class"""
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Hourlies - Hourly Work Logger")
        self.root.geometry("300x100")
        
        self.config = Config()
        self.day_folder = None
        self.timer_thread = None
        self.timer_active = False
        self.worklog_window = None
        
        self.setup_ui()
        
        # Start minimized
        self.root.withdraw()
        self.root.iconify()
        
        # Auto-start a new day
        self.start_new_day()
    
    def setup_ui(self):
        """Setup the main UI"""
        # Create menu bar
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Start a new day", command=self.start_new_day)
        file_menu.add_command(label="End of day", command=self.end_of_day)
        file_menu.add_separator()
        file_menu.add_command(label="Edit Config", command=self.config.edit_config)
        file_menu.add_separator()
        file_menu.add_command(label="Restart", command=self.restart_app)
        file_menu.add_command(label="Close", command=self.close_app)
        
        # Main frame with status
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        self.status_label = ttk.Label(main_frame, text="Ready to start logging...")
        self.status_label.pack()
        
        # Handle window close button
        self.root.protocol("WM_DELETE_WINDOW", self.minimize_to_tray)
    
    def minimize_to_tray(self):
        """Minimize to system tray (actually just minimize)"""
        self.root.withdraw()
        self.root.iconify()
    
    def start_new_day(self):
        """Start a new day of logging"""
        # Create worklog folder if it doesn't exist
        worklog_folder = self.config.get("worklog_folder")
        os.makedirs(worklog_folder, exist_ok=True)
        
        # Create day folder
        today = datetime.now().strftime("%Y%m%d")
        day_folder_base = os.path.join(worklog_folder, today)
        
        # Find the next available folder number
        folder_num = 1
        self.day_folder = f"{day_folder_base}.{folder_num:03d}"
        while os.path.exists(self.day_folder):
            folder_num += 1
            self.day_folder = f"{day_folder_base}.{folder_num:03d}"
        
        # Use existing folder if it's for today, otherwise create new
        existing_folders = [f for f in os.listdir(worklog_folder) 
                          if f.startswith(today) and os.path.isdir(os.path.join(worklog_folder, f))]
        
        if existing_folders:
            existing_folders.sort()
            self.day_folder = os.path.join(worklog_folder, existing_folders[-1])
        else:
            os.makedirs(self.day_folder, exist_ok=True)
        
        # Update status
        self.status_label.config(text=f"Logging to: {os.path.basename(self.day_folder)}")
        
        # Start the hourly timer
        self.start_timer()
        
        # Create worklog window instance
        self.worklog_window = HourlyWorklogWindow(self.root, self.day_folder)
    
    def start_timer(self):
        """Start the hourly timer"""
        if self.timer_active:
            return
            
        self.timer_active = True
        self.timer_thread = threading.Thread(target=self.timer_loop, daemon=True)
        self.timer_thread.start()
    
    def timer_loop(self):
        """Timer loop that triggers hourly popups"""
        while self.timer_active:
            now = datetime.now()
            next_hour = now.replace(minute=self.config.get("popup_at_minute", 0), 
                                   second=0, microsecond=0)
            
            if now >= next_hour:
                next_hour += timedelta(hours=1)
            
            wait_seconds = (next_hour - now).total_seconds()
            
            # Wait until next hour
            time.sleep(wait_seconds)
            
            if self.timer_active:
                # Show the worklog window
                self.root.after(0, self.show_worklog_window)
    
    def show_worklog_window(self):
        """Show the hourly worklog window"""
        if self.worklog_window:
            self.worklog_window.show()
    
    def end_of_day(self):
        """End the day - show final worklog and close"""
        if not self.day_folder:
            messagebox.showwarning("No Active Day", "Please start a new day first.")
            return
            
        # Stop the timer
        self.timer_active = False
        
        # Show worklog window with callback to close app
        if self.worklog_window:
            self.worklog_window.callback = self.close_app
            self.worklog_window.show()
        else:
            self.close_app()
    
    def restart_app(self):
        """Restart the application"""
        python = sys.executable
        os.execl(python, python, *sys.argv)
    
    def close_app(self):
        """Close the application"""
        self.timer_active = False
        self.root.quit()
    
    def run(self):
        """Run the application"""
        self.root.mainloop()

if __name__ == "__main__":
    app = HourliesApp()
    app.run()