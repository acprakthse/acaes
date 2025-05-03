# ALL PARAMETERS

# Price Threshold
charge_threshold = 0.07 
discharge_threshold = 0.07 

# compressor_params
    
P1 = 100000 # Ambient (inlet) pressure [kPa]
P2 = 3000000 # Storage pressure [kPa] (example value)
gamma = 1.4 # Specific heat ratio for air
cp = 1.005 # Specific heat at constant pressure [kJ/(kg·K)]
eta_comp = 0.90 # Compressor isentropic efficiency (decimal)
eta_trans = 1 # Transmission/electrical efficiency (decimal)
eta_TES = 1.0 # Fraction of compression heat recovered for TES (decimal)
# General params

R_specific = 287.058         # J/(kg·K)

# Cavern params 
P_max_s = 2.87e6 # Pa

T_s = 288.45 # C

V_pore_s = 365877 # m³

# Expander params
eta_t=0.90       # turbine isentropic efficiency
T_tes=597        # K
P_amb = 100000 # Pa

turbine_capacity = 15000 # kW (total expander or gas turbine capacity)

# TES Capacity
TES_cap = 300000 # kWh (maximum TES capacity in kWh)

# Losses
CAES_loss = 0 
TES_loss = 0 
