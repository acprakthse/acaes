import os
import itertools

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import wind_turbine_model
import Compressor_Model
import energy_management
import revenue as revenue_module

# -----------------------------------------------------------------------------
# 1) LOCATE YOUR WIND DATA IN DOWNLOADS
# -----------------------------------------------------------------------------

WIND_DATA_FILE   = os.path.join("D:/", "wind and temp.xlsx")

# -----------------------------------------------------------------------------
# 2) DEFINE YOUR EXPLORATION GRID
# -----------------------------------------------------------------------------
# turbine capacities to test (in kW)
TURBINE_CAPS    = [10_000, 15_000, 20_000, 25_000]

# TES (thermal energy storage) capacities to test (in kWh)
STORAGE_CAPS    = [100_000, 200_000, 300_000, 400_000]

# sell/buy price thresholds to test (in €/kWh)
PRICE_THRESHOLDS = [0.05, 0.06, 0.07, 0.08, 0.09]

# -----------------------------------------------------------------------------
# 3) RUN ALL COMBINATIONS
# -----------------------------------------------------------------------------
records = []

for tc, sc, pt in itertools.product(TURBINE_CAPS, STORAGE_CAPS, PRICE_THRESHOLDS):

    # --- patch your modules with the current parameters ---
    # (assumes energy_management.py reads these globals)
    energy_management.turbine_capacity = tc
    energy_management.TES_cap         = sc

    # --- a) wind turbine model: load & compute power output ---
    df = wind_turbine_model.read_wind_data(WIND_DATA_FILE)
    df = wind_turbine_model.calculate_power_output(df)
    df = wind_turbine_model.apply_conditions(df)

    # --- b) compressor model ---
    df = Compressor_Model.compressor_energy_model(df)

    # --- c) storage dispatch (charge/discharge threshold = pt) ---
    df = energy_management.allocate_energy_storage(
        df,
        charge_threshold=pt,
        discharge_threshold=pt
    )

    # --- d) revenue calculation ---
    df = revenue_module.calculate_revenue(df)

    # total revenue over the full period
    total_rev = df["Total_Revenue"].sum()

    records.append({
        "turbine_capacity_kW": tc,
        "TES_capacity_kWh":   sc,
        "price_threshold_€/kWh": pt,
        "total_revenue_€":    total_rev
    })

# assemble into DataFrame
results = pd.DataFrame(records)

# -----------------------------------------------------------------------------
# 4) FIND PARETO‐EFFICIENT POINTS
#    (minimize price_threshold, maximize revenue)
# -----------------------------------------------------------------------------
pts = results[["price_threshold_€/kWh", "total_revenue_€"]].values
is_pareto = np.ones(len(pts), dtype=bool)

for i, p in enumerate(pts):
    # any other point that is no worse in both criteria and strictly better in one?
    mask = (pts[:,0] <= p[0]) & (pts[:,1] >= p[1])
    mask[i] = False
    if np.any(mask):
        is_pareto[i] = False

pareto_df = results[is_pareto]

# -----------------------------------------------------------------------------
# 5) SAVE CSVs
# -----------------------------------------------------------------------------
results.to_csv("pareto_scan_all.csv", index=False)
pareto_df.to_csv("pareto_front.csv", index=False)

# -----------------------------------------------------------------------------
# 6) PLOT Revenue vs. Price Threshold (pareto front in red)
# -----------------------------------------------------------------------------
plt.figure(figsize=(8,6))
plt.scatter(
    results["total_revenue_€"],
    results["price_threshold_€/kWh"],
    c="lightgray",
    label="All runs"
)
plt.scatter(
    pareto_df["total_revenue_€"],
    pareto_df["price_threshold_€/kWh"],
    c="red",
    label="Pareto front"
)
plt.xlabel("Total Revenue (€)")
plt.ylabel("Price Threshold (€/kWh)")
plt.title("Pareto Front: minimize threshold, maximize revenue")
plt.legend()
plt.tight_layout()
plt.savefig("pareto_front.png", dpi=300)
plt.show()
