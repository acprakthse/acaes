import os
import re
import io
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, PhotoImage
import pandas as pd
from datetime import datetime

# Import user modules
import wind_turbine_model
import Compressor_Model
import energy_management
import revenue

# Paths
DIR_PATH = os.path.dirname(__file__)
PARAMS_FILE = os.path.join(DIR_PATH, 'params.py')
BG_IMAGE = os.path.join(DIR_PATH, 'params_bg.png')  # Background for parameter editor

class EnergyApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Wind-CAES Energy Management GUI")
        self.geometry("900x700")

        # State
        self.file_path = None
        self.data = None
        self.params = {}
        self.entries = {}

        # Menu bar
        menubar = tk.Menu(self)
        self.config(menu=menubar)
        params_menu = tk.Menu(menubar, tearoff=0)
        params_menu.add_command(label="Edit Parameters", command=self.edit_params)
        menubar.add_cascade(label="Parameters", menu=params_menu)

        # File selection
        file_frame = tk.Frame(self)
        file_frame.pack(fill=tk.X, padx=10, pady=5)
        tk.Label(file_frame, text="Wind Data File:").pack(side=tk.LEFT)
        self.file_label = tk.Label(file_frame, text="No file selected")
        self.file_label.pack(side=tk.LEFT, padx=5)
        tk.Button(file_frame, text="Browse...", command=self.browse_file).pack(side=tk.RIGHT)

        # Control buttons
        control_frame = tk.Frame(self)
        control_frame.pack(fill=tk.X, padx=10, pady=5)
        tk.Button(control_frame, text="Run Analysis", command=self.run_analysis, bg="#4CAF50", fg="white").pack(side=tk.LEFT)
        tk.Button(control_frame, text="Save Results", command=self.save_results).pack(side=tk.RIGHT)

        # Output log
        log_frame = tk.Frame(self)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        tk.Label(log_frame, text="Output:").pack(anchor=tk.W)
        self.log = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, font=("Courier", 10))
        self.log.pack(fill=tk.BOTH, expand=True)

    def browse_file(self):
        filetypes = [("Excel files", "*.xlsx;*.xls"), ("All files", "*.*")]
        path = filedialog.askopenfilename(title="Select wind data file", filetypes=filetypes)
        if path:
            self.file_path = path
            self.file_label.config(text=path)
            self.log.delete(1.0, tk.END)
            self.log.insert(tk.END, f"Selected file: {path}\n")
            self.data = None

    def run_analysis(self):
        if not self.file_path:
            messagebox.showwarning("No File", "Please select a wind data file first.")
            return
        # Clear previous log
        self.log.delete(1.0, tk.END)
        self.log.insert(tk.END, "Starting analysis...\n")
        # Capture print output
        buf = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = buf
        try:
            # 1. Read wind data
            df = wind_turbine_model.read_wind_data(self.file_path)
            self.log.insert(tk.END, f"Data loaded: {len(df)} rows\n")
            
            # 2. Wind power calculations
            df = wind_turbine_model.calculate_power_output(df)
            self.log.insert(tk.END, "Calculated wind power output.\n")

            # 3. Apply operational conditions
            df = wind_turbine_model.apply_conditions(df)
            self.log.insert(tk.END, "Applied turbine operating conditions.\n")

            # 4. Compressor model
            df = Compressor_Model.compressor_energy_model(df)
            self.log.insert(tk.END, "Computed compressor energy model.\n")

            # 5. Energy management (storage allocation)
            df = energy_management.allocate_energy_storage(df)
            self.log.insert(tk.END, "Allocated energy storage.\n")

            # 6. Revenue calculation
            df = revenue.calculate_revenue(df)
            self.log.insert(tk.END, "Calculated revenue.\n")

            # Restore stdout and write captured prints to log
            sys.stdout = old_stdout
            output = buf.getvalue()
            self.log.insert(tk.END, output)
            # Save processed DataFrame
            self.data = df
        except Exception as e:
            sys.stdout = old_stdout
            messagebox.showerror("Analysis Error", str(e))
            self.log.insert(tk.END, f"Error during analysis: {e}\n")

    def save_results(self):
        if self.data is None:
            messagebox.showwarning("No Data", "No analysis results to save. Run analysis first.")
            return
        # Create timestamp for filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        default_name = f"results_{timestamp}.xlsx"
        filetypes = [("Excel files", "*.xlsx"), ("CSV files", "*.csv"), ("All files", "*.*")]
        save_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=filetypes,
            initialfile=default_name,
            title="Save results as"
        )
        if save_path:
            try:
                if save_path.lower().endswith('.csv'):
                    self.data.to_csv(save_path, index=False)
                else:
                    self.data.to_excel(save_path, index=False)
                messagebox.showinfo("Saved", f"Results saved to {save_path}")
                self.log.insert(tk.END, f"Results saved to {save_path}\n")
            except Exception as e:
                messagebox.showerror("Save Error", str(e))
                self.log.insert(tk.END, f"Error saving results: {e}\n")

    def edit_params(self):
        # Load and parse params
        lines = open(PARAMS_FILE, 'r').read().splitlines(keepends=True)
        pattern = re.compile(
            r"^(?P<indent>\s*)(?P<name>[A-Za-z_][A-Za-z0-9_]*)\s*=\s*(?P<value>[^#\n]+?)(?P<comment>\s*(#.*))?$"
        )
        self.params.clear()
        for idx, line in enumerate(lines):
            m = pattern.match(line)
            if m:
                name = m.group('name')
                self.params[name] = {'value': m.group('value').strip(), 'line_no': idx}

        # Editor window
        win = tk.Toplevel(self)
        win.title("Edit Parameters")

        # Background
        if os.path.exists(BG_IMAGE):
            bg = PhotoImage(file=BG_IMAGE)
            canvas = tk.Canvas(win, width=bg.width(), height=bg.height())
            canvas.create_image(0, 0, image=bg, anchor='nw')
            canvas.bg = bg
        else:
            canvas = tk.Canvas(win, width=900, height=700, bg='lightgray')
        canvas.pack()

        # Parameter positions and units
        positions = {
            'P1': (350,350), 'P2': (350,380), 'gamma': (350,410), 'cp': (350,440),
            'eta_comp': (350,470), 'eta_trans': (350,500), 'eta_TES': (350,530),
            'charge_threshold': (700,50), 'discharge_threshold': (700,80),
            'TES_cap': (650,400),
            'eta_t': (1050,370), 'P_amb': (1050,400), 'turbine_capacity': (1050,430),
            'CAES_loss': (770,450), 'TES_loss': (770,480),
            'P_max_s': (1050,620), 'T_s': (1050,650), 'V_pore_s': (1050,680)
        }
        units = {
            'P1': 'Pa', 'P2': 'Pa', 'gamma': '-', 'cp': 'kJ/kg·K',
            'eta_comp': '%', 'eta_trans': '%', 'eta_TES': '%',
            'charge_threshold': '€', 'discharge_threshold': '€',
            'TES_cap': 'kWh',
            'eta_t': '%', 'T_tes': 'K', 'P_amb': 'Pa', 'turbine_capacity': 'kW',
            'CAES_loss': '%', 'TES_loss': '%',
            'P_max_s': 'Pa', 'T_s': 'K', 'V_pore_s': 'm3'
        }
        for name, (x, y) in positions.items():
            val = self.params.get(name, {}).get('value', '')
            unit = units.get(name, '')
            lbl_text = f"{name} ({unit}) =" if unit else f"{name} ="
            lbl = tk.Label(canvas, text=lbl_text, bg='#000', fg='#0f0', anchor='e')
            canvas.create_window(x, y, window=lbl, anchor='ne')
            ent = tk.Entry(canvas, width=12, justify='left')
            ent.insert(0, val)
            canvas.create_window(x + 5, y, window=ent, anchor='nw')
            self.entries[name] = ent

        # Save button
        btn = tk.Button(win, text="Save Parameters", command=lambda: self._save_params(lines, win))
        canvas.create_window(250, 650, window=btn, anchor='center')

    def _save_params(self, lines, window):
        updated = False
        for name, ent in self.entries.items():
            new_val = ent.get().strip()
            if name in self.params:
                idx = self.params[name]['line_no']
                orig = lines[idx]
                comment = orig[orig.find('#'):] if '#' in orig else ''
                lines[idx] = f"{name} = {new_val} {comment}\n"
                updated = True
            else:
                lines.append(f"{name} = {new_val}\n")
                updated = True
        if updated:
            with open(PARAMS_FILE, 'w') as f:
                f.writelines(lines)
            messagebox.showinfo("Parameters Updated", "params.py has been updated.")
        else:
            messagebox.showinfo("No Changes", "No parameter values were changed.")
        window.destroy()

if __name__ == "__main__":
    app = EnergyApp()
    app.mainloop()
