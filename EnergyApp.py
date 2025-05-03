import os
import re
import io
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, PhotoImage
import tkinter.simpledialog as simpledialog

import pandas as pd
import numpy as np
import itertools
from datetime import datetime
import importlib

# plotting for Pareto
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import params
import wind_turbine_model
import Compressor_Model
import energy_management
import revenue

# Paths
DIR_PATH = os.path.dirname(__file__)
PARAMS_FILE = os.path.join(DIR_PATH, 'params.py')
BG_IMAGE = os.path.join(DIR_PATH, 'params_bg.png')

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
        tk.Button(control_frame, text="Run Analysis", command=self.run_analysis,
                  bg="#4CAF50", fg="white").pack(side=tk.LEFT)
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
        self.log.delete(1.0, tk.END)
        self.log.insert(tk.END, "Starting analysis...\n")

        buf = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = buf
        try:
            df = wind_turbine_model.read_wind_data(self.file_path)
            self.log.insert(tk.END, f"Data loaded: {len(df)} rows\n")

            df = wind_turbine_model.calculate_power_output(df)
            self.log.insert(tk.END, "Calculated wind power output.\n")

            df = wind_turbine_model.apply_conditions(df)
            self.log.insert(tk.END, "Applied turbine operating conditions.\n")

            df = Compressor_Model.compressor_energy_model(df)
            self.log.insert(tk.END, "Computed compressor energy model.\n")

            df = energy_management.allocate_energy_storage(df)
            self.log.insert(tk.END, "Allocated energy storage.\n")

            df = revenue.calculate_revenue(df)
            self.log.insert(tk.END, "Calculated revenue.\n")

            sys.stdout = old_stdout
            output = buf.getvalue()
            self.log.insert(tk.END, output)
            self.data = df

        except Exception as e:
            sys.stdout = old_stdout
            messagebox.showerror("Analysis Error", str(e))
            self.log.insert(tk.END, f"Error during analysis: {e}\n")

    def save_results(self):
        if self.data is None:
            messagebox.showwarning("No Data", "No analysis results to save. Run analysis first.")
            return
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

        win = tk.Toplevel(self)
        win.title("Edit Parameters")

        if os.path.exists(BG_IMAGE):
            bg = PhotoImage(file=BG_IMAGE)
            canvas = tk.Canvas(win, width=bg.width(), height=bg.height())
            canvas.create_image(0, 0, image=bg, anchor='nw')
            canvas.bg = bg
        else:
            canvas = tk.Canvas(win, width=900, height=700, bg='lightgray')
        canvas.pack()

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

        btn = tk.Button(win, text="Save Parameters",
                        command=lambda: self._save_params(lines, win))
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
            try:
                importlib.reload(params)
            except:
                if 'params' in sys.modules:
                    del sys.modules['params']
                importlib.import_module('params')
            importlib.reload(wind_turbine_model)
            importlib.reload(Compressor_Model)
            importlib.reload(energy_management)
            importlib.reload(revenue)
            messagebox.showinfo("Parameters Updated",
                                "params.py has been updated and modules reloaded.")
        else:
            messagebox.showinfo("No Changes",
                                "No parameter values were changed.")
        window.destroy()


# === PARETO EXTENSION: min,max,step ENTRY ===

def _add_pareto_menu(self):
    menubar = self.nametowidget(self['menu'])
    pareto_menu = tk.Menu(menubar, tearoff=0)
    pareto_menu.add_command(label="Run Pareto Analysis", command=self.run_pareto)
    menubar.add_cascade(label="Pareto", menu=pareto_menu)

def _parse_range(s, cast=float):
    parts = [p.strip() for p in s.split(',')]
    if len(parts) != 3:
        raise ValueError("Expected format: min,max,step")
    mn, mx, st = cast(parts[0]), cast(parts[1]), cast(parts[2])
    if st <= 0 or mx < mn:
        raise ValueError("Require step>0 and max>=min")
    return list(np.arange(mn, mx + 1e-9, st))

def run_pareto(self):
    if not self.file_path:
        messagebox.showwarning("No File",
            "Please select a wind data file first.")
        return

    t_caps = simpledialog.askstring(
        "Turbine capacity range",
        "Enter turbine capacity as min,max,step (kW):",
        parent=self
    )
    if t_caps is None: return
    s_caps = simpledialog.askstring(
        "TES capacity range",
        "Enter TES capacity as min,max,step (kWh):",
        parent=self
    )
    if s_caps is None: return
    p_thresh = simpledialog.askstring(
        "Price threshold range",
        "Enter price threshold as min,max,step (€/kWh):",
        parent=self
    )
    if p_thresh is None: return

    try:
        TURBINE_CAPS     = _parse_range(t_caps, float)
        STORAGE_CAPS     = _parse_range(s_caps, float)
        PRICE_THRESHOLDS = _parse_range(p_thresh, float)
    except Exception as e:
        messagebox.showerror("Parse error", f"Failed to parse range:\n{e}")
        return

    self.log.insert(tk.END, "\n=== Starting Pareto sweep ===\n")
    records = []
    for tc, sc, pt in itertools.product(TURBINE_CAPS, STORAGE_CAPS, PRICE_THRESHOLDS):
        self.log.insert(tk.END, f"Testing TC={tc}, SC={sc}, PT={pt}\n")
        self.log.see(tk.END); self.update()

        energy_management.turbine_capacity = tc
        energy_management.TES_cap         = sc

        df = wind_turbine_model.read_wind_data(self.file_path)
        df = wind_turbine_model.calculate_power_output(df)
        df = wind_turbine_model.apply_conditions(df)
        df = Compressor_Model.compressor_energy_model(df)
        df = energy_management.allocate_energy_storage(
            df, charge_threshold=pt, discharge_threshold=pt
        )
        df = revenue.calculate_revenue(df)

        total_rev = df["Total_Revenue"].sum()
        records.append({
            "turbine_capacity_kW":     tc,
            "TES_capacity_kWh":        sc,
            "price_threshold_€/kWh":   pt,
            "total_revenue_€":         total_rev
        })

    results = pd.DataFrame(records)
    pts = results[["price_threshold_€/kWh", "total_revenue_€"]].values
    is_pareto = np.ones(len(pts), dtype=bool)
    for i, p in enumerate(pts):
        mask = (pts[:,0] <= p[0]) & (pts[:,1] >= p[1])
        mask[i] = False
        if np.any(mask):
            is_pareto[i] = False
    pareto_df = results[is_pareto]

    self.log.insert(tk.END, "Pareto analysis complete.\n"); self.log.see(tk.END)

    # 4) plot in a new Tk window, coloring by TES capacity
    win = tk.Toplevel(self)
    win.title("Pareto Front by TES Capacity")
    fig, ax = plt.subplots(figsize=(6,4))
    
    # pick one distinct color per TES capacity
    unique_sc = sorted(results["TES_capacity_kWh"].unique())
    cmap = plt.cm.get_cmap('tab10', len(unique_sc))
    
    for idx, sc in enumerate(unique_sc):
        df_sc = results[results["TES_capacity_kWh"] == sc]
        ax.scatter(
            df_sc["total_revenue_€"],
            df_sc["price_threshold_€/kWh"],
            color=cmap(idx),
            label=f"{sc} kWh",
            alpha=0.7
        )
    
    # overlay Pareto front with black circles (no fill)
    ax.scatter(
        pareto_df["total_revenue_€"],
        pareto_df["price_threshold_€/kWh"],
        facecolors='none',
        edgecolors='k',
        s=100,
        linewidths=1.5,
        label="Pareto Front"
    )
    
    ax.set_xlabel("Total Revenue (€)")
    ax.set_ylabel("Price Threshold (€/kWh)")
    ax.set_title("Pareto Front by TES Capacity")
    ax.legend(title="TES Capacity")
    canvas = FigureCanvasTkAgg(fig, master=win)
    canvas.draw()
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)


# Attach extension into the class
EnergyApp._add_pareto_menu = _add_pareto_menu
EnergyApp.run_pareto      = run_pareto

# Monkey-patch __init__ to install Pareto menu
_orig_init = EnergyApp.__init__
def _patched_init(self, *args, **kwargs):
    _orig_init(self, *args, **kwargs)
    self._add_pareto_menu()
EnergyApp.__init__ = _patched_init

if __name__ == "__main__":
    app = EnergyApp()
    app.mainloop()
