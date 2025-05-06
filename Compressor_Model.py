import pandas as pd
import numpy as np
from params import  P1, P2, gamma, cp, eta_comp, eta_trans, eta_TES

def compressor_energy_model(
    df,

):
    """
    Adjusted compressor model using thermodynamic relations.

    Steps:
      1. Compute the ideal isentropic outlet temperature:
            T2s = T1 * (P2/P1)^((gamma - 1)/gamma)
      2. Determine the actual outlet temperature:
            T2 = T1 + (T2s - T1) / eta_comp
      3. Calculate enthalpy change per kg of air:
            Δh = cp * (T2 - T1)  [kJ/kg]
      4. Convert available electrical energy from the wind turbine (in kW for 1-hour → kWh)
         to kJ: E_elec_kJ = E_elec_kWh * 3600
      5. Compute the mass of air compressed:
            m_air = (E_elec_kJ * (eta_comp * eta_trans)) / Δh
      6. Energy stored in CAES:
            E_CAES_kWh = (m_air * Δh) / 3600
      7. Thermal energy stored (TES):
            E_TES_kWh = eta_TES * E_elec_kWh

    Assumptions:
      - df['Power_Output'] holds the wind turbine's electrical power in kW.
      - A 1-hour timestep is used (so kW equals kWh per hour).
      - Negative power outputs are set to zero.
    
    Returns:
      DataFrame with additional columns:
        'T2s_K': Ideal outlet temperature (K)
        'T2_K': Actual outlet temperature (K)
        'Delta_h_kJ_per_kg': Enthalpy change [kJ/kg]
        'E_elec_kWh': Available electrical energy [kWh]
        'E_elec_kJ': Electrical energy converted to [kJ]
        'm_air_kg': Mass of air compressed [kg]
        'E_CAES_kJ': Energy stored in compressed air [kJ]
        'E_CAES_kWh': Energy stored in compressed air [kWh]
        'E_TES_kWh': Thermal energy stored [kWh]
        'Compressor_Power_kW': Compressor power used (average over 1-hour)
    """

    # 1. Ideal isentropic outlet temperature:
    T2s = (df['temp']+273.15) * (P2 / P1) ** ((gamma - 1) / gamma)

    # 2. Actual outlet temperature considering compressor efficiency:
    T2 = (df['temp']+273.15)  + (T2s - (df['temp']+273.15) ) / eta_comp

    # 3. Enthalpy change per kg of air [kJ/kg]:
    delta_h = cp * (T2 - (df['temp']+273.15) )

    # Overall efficiency (compressor and transmission):
    eta_total = eta_comp * eta_trans

    # 4. Electrical energy available (Power_Output in kW for 1 hour equals kWh)
    #    Convert to kJ: 1 kWh = 3600 kJ.
    df['E_elec_kWh'] = df['Total_Power_Output'].clip(lower=0)
    df['E_elec_kJ'] = df['E_elec_kWh'] * 3600.0

    # 5. Compute mass of air compressed [kg]:
    df['m_air_kg'] = (df['E_elec_kJ'] * eta_total) / delta_h

    # 6. Energy stored in compressed air (CAES) in kJ and kWh:
    df['E_CAES_kJ'] = df['m_air_kg'] * delta_h
    # df['E_CAES_kWh'] = df['E_CAES_kJ'] / 3600.0

    # 7. Thermal Energy Storage (TES): a fraction of the electrical energy (if captured)
    df['E_TES_kWh'] = eta_total * eta_TES * df['E_elec_kWh']

    # Compressor power is simply the electrical power used over the hour.
    df['Compressor_Power_kW'] = df['E_elec_kWh']  # (since 1 kWh over 1h equals 1 kW)

    # Optional: Store intermediate temperatures and enthalpy change for reference.
    df['T2s_K'] = T2s
    df['T2_K'] = T2
    df['Delta_h_kJ_per_kg'] = delta_h

     # Print peak mass flow
    max_flow = df['m_air_kg'].max()/3600
    print(f"Peak air‐mass flow: {max_flow:.2f} kg/s")

    return df
