import sys
import os
import re
import io
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, PhotoImage
import tkinter.simpledialog as simpledialog

import pandas as pd
import numpy as np
import itertools
from datetime import datetime
import importlib

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# ─── Handle frozen bundle vs. script ──────────────────────────────────────────
if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(__file__)

PARAMS_FILE = os.path.join(BASE_DIR, 'params.py')
BG_IMAGE    = os.path.join(BASE_DIR, 'params_bg.png')

# ─── Import user modules ─────────────────────────────────────────────────────
import params
import wind_turbine_model
import Compressor_Model
import energy_management
import revenue


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

        # Parameters menu
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
            self.log.insert(tk.END, buf.getvalue())
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
        save_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files","*.xlsx"),("CSV files","*.csv"),("All files","*.*")],
            initialfile=default_name,
            title="Save results as"
        )
        if not save_path:
            return

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
                self.params[m.group('name')] = {'value': m.group('value').strip(), 'line_no': idx}

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
            lbl = tk.Label(canvas, text=f"{name} ({unit}) =", bg='#000', fg='#0f0', anchor='e')
            canvas.create_window(x, y, window=lbl, anchor='ne')
            ent = tk.Entry(canvas, width=12, justify='left')
            ent.insert(0, val)
            canvas.create_window(x+5, y, window=ent, anchor='nw')
            self.entries[name] = ent

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
            messagebox.showinfo("Parameters Updated", "params.py has been updated and modules reloaded.")
        else:
            messagebox.showinfo("No Changes", "No parameter values were changed.")
        window.destroy()


# ─── PARETO EXTENSION w/ FIXED STORAGE_CAPS & LABELS ─────────────────────────

def _add_pareto_menu(self):
    menubar = self.nametowidget(self['menu'])
    pmenu = tk.Menu(menubar, tearoff=0)
    pmenu.add_command(label="Run Pareto Analysis", command=self.run_pareto)
    menubar.add_cascade(label="Pareto", menu=pmenu)

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
        messagebox.showwarning("No File", "Please select a wind data file first.")
        return

    # ask for ranges (no TES)
    w_turb   = simpledialog.askstring("Wind Turbine ×n",    "min,max,step:", parent=self)
    t_caps   = simpledialog.askstring("Turbine Capacity",    "min,max,step (kW):", parent=self)
    p_thresh = simpledialog.askstring("Price Threshold",      "min,max,step (€/kWh):", parent=self)
    if None in (w_turb, t_caps, p_thresh):
        return

    try:
        PARETO_WT        = _parse_range(w_turb,   float)
        TURBINE_CAPS     = _parse_range(t_caps,   float)
        PRICE_THRESHOLDS = _parse_range(p_thresh, float)
    except Exception as e:
        messagebox.showerror("Parse error", str(e))
        return

    # fixed TES capacities & labels
    STORAGE_CAPS   = [366000, 515000, 265000, 84000]
    STORAGE_LABELS = ['S9', 'S12', 'S14', 'S16']

    self.log.insert(tk.END, "\n=== Starting Pareto sweep ===\n")
    records = []
    for tc, sc, pt, w in itertools.product(TURBINE_CAPS, STORAGE_CAPS, PRICE_THRESHOLDS, PARETO_WT):
        self.log.insert(tk.END, f"TC={tc}, SC={sc}, PT={pt}, WT×{w}\n")
        self.log.see(tk.END); self.update()

        energy_management.turbine_capacity     = tc
        energy_management.TES_cap             = sc
        wind_turbine_model.pareto_wind_turbine = w

        df = wind_turbine_model.read_wind_data(self.file_path)
        df = wind_turbine_model.calculate_power_output(df)
        df = wind_turbine_model.apply_conditions(df)
        df = Compressor_Model.compressor_energy_model(df)
        df = energy_management.allocate_energy_storage(df, charge_threshold=pt, discharge_threshold=pt)
        df = revenue.calculate_revenue(df)

        tot_rev = df["Total_Revenue"].sum()
        rev_no  = df.get("Revenue_without_storage", pd.Series(0, index=df.index)).sum()
        save_yr = tot_rev - rev_no

        records.append({
            "WT_multiplier":               w,
            "turbine_capacity_kW":         tc,
            "TES_capacity_kWh":            sc,
            "TES_label":                   STORAGE_LABELS[STORAGE_CAPS.index(sc)],
            "price_threshold_€/kWh":       pt,
            "total_revenue_€":             tot_rev,
            "annual_saving_from_storage_€": save_yr
        })

    results = pd.DataFrame(records)
    pts     = results[["price_threshold_€/kWh","total_revenue_€"]].values
    mask    = np.ones(len(pts), dtype=bool)
    for i,p in enumerate(pts):
        d = (pts[:,0] <= p[0]) & (pts[:,1] >= p[1])
        d[i] = False
        if d.any(): mask[i] = False
    pareto_df = results[mask]

    self.log.insert(tk.END, "Pareto complete.\n"); self.log.see(tk.END)

    # export Excel
    if messagebox.askyesno("Save Pareto?", "Save AllRuns & ParetoFront to Excel?"):
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        default = f"pareto4d_{ts}.xlsx"
        path = filedialog.asksaveasfilename(defaultextension=".xlsx",
            filetypes=[("Excel","*.xlsx")], initialfile=default,
            title="Save Pareto Results")
        if path:
            with pd.ExcelWriter(path, engine="openpyxl") as w:
                results.to_excel(w,   sheet_name="AllRuns",    index=False)
                pareto_df.to_excel(w, sheet_name="ParetoFront", index=False)
            messagebox.showinfo("Saved", f"Saved to {path}")

    # plot by TES only
    win = tk.Toplevel(self)
    win.title("Pareto Front by TES Capacity")
    fig, ax = plt.subplots(figsize=(6,4))

    for sc,label in zip(STORAGE_CAPS, STORAGE_LABELS):
        sub = results[results["TES_capacity_kWh"] == sc]
        ax.scatter(sub["total_revenue_€"],
                   sub["price_threshold_€/kWh"],
                   label=label, s=30, alpha=0.7)

    ax.scatter(pareto_df["total_revenue_€"],
               pareto_df["price_threshold_€/kWh"],
               facecolors='none', edgecolors='k',
               s=100, linewidths=1.5, label="Pareto Front")

    ax.set_xlabel("Total Revenue (€)")
    ax.set_ylabel("Price Threshold (€/kWh)")
    ax.set_title("Pareto Front by TES Capacity (S9,S12,S14,S16)")
    ax.legend(bbox_to_anchor=(1.05,1), loc='upper left')
    plt.tight_layout()

    canvas = FigureCanvasTkAgg(fig, master=win)
    canvas.draw()
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)


# attach & patch
EnergyApp._add_pareto_menu = _add_pareto_menu
EnergyApp.run_pareto      = run_pareto
_orig_init = EnergyApp.__init__
def _patched_init(self,*a,**k):
    _orig_init(self,*a,**k)
    self._add_pareto_menu()
EnergyApp.__init__ = _patched_init


if __name__=="__main__":
    app = EnergyApp()
    app.mainloop()
