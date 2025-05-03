import pandas as pd
import numpy as np
from params import (
    R_specific,           
    P_max_s,    
    T_s,         
    V_pore_s,    
    cp,          
    gamma,       
    P_amb,       
    turbine_capacity,
    TES_cap,
    CAES_loss,
    TES_loss,
    eta_t,
    charge_threshold, 
    discharge_threshold
)

# Function to allocate and accumulate energy storage with 0.005% hourly loss, charging and discharging
def allocate_energy_storage(df, charge_threshold=charge_threshold, discharge_threshold=discharge_threshold):
  
    max_CAES_cap = P_max_s * V_pore_s / ((T_s)* R_specific)

    P_cav  = P_max_s  

    # Discharge rates per hour
    
    tes_discharge_rate = turbine_capacity      # kW (this is the total cap of expander)
    
    # Max TES Capacity
    max_TES_cap = TES_cap # kWh

    # Initialize all tracking columns
    for col in [
        'Grid_transfer_kWh',
        'CAES_charging_kg','TES_charging_kWh',
        'Cumulative_CAES_storage_kg','Cumulative_TES_storage_kWh',
        'CAES_loss_kg','TES_loss_kWh',   
        'CAES_discharged_kg','TES_discharged_kWh',
        'Cumulative_CAES_discharged_kg','Cumulative_TES_discharged_kWh',
        'Cumulative_Grid_transfer_kWh',
        'Operating_Mode'

    ]:
        df[col] = 0.0

    current_storage_kg = 0.0
    current_TES_storage_kWh = 0.0
    total_discharged_kg = 0.0
    total_discharged_kWh = 0.0
    total_to_Grid_kWh = 0.0

    for idx, row in df.iterrows():
        price = row.get('price', 0.0)
        elec_prod = row.get('Total_Power_Output', 0.0)

        # TES OUT
        tes_out = min(tes_discharge_rate, current_TES_storage_kWh)

        # Losses
        caes_loss = CAES_loss * current_storage_kg
        tes_loss = TES_loss * current_TES_storage_kWh
        current_storage_kg -= caes_loss
        current_TES_storage_kWh -= tes_loss
        df.at[idx, 'CAES_loss_kg'] = caes_loss
        df.at[idx, 'TES_loss_kWh'] = tes_loss

        # 1) recompute real‐time cavern pressure (Pa)
        p_cav = max(
            (current_storage_kg * T_s * R_specific) / V_pore_s,
            P_amb
        )
        
        # 2) ideal enthalpy drop Δh in kJ/kg
        T2 = row.get('T2_K', 0.0)
        delta_h_kJ = cp * T2 * (1 - (P_amb / p_cav)**((gamma - 1) / gamma))
        
        # 3) convert to kWh/kg and include turbine efficiency
        delta_h_kWh_per_kg = eta_t * delta_h_kJ / 3600.0
        
        # 4) discharge‐limited mass flow [kg] to supply tes_out [kWh]
        if delta_h_kWh_per_kg > 0:
            caes_discharge_rate = tes_out / delta_h_kWh_per_kg
        else:
            caes_discharge_rate = 0.0
                
        # if wind turbine generate electricty
        if elec_prod > 0:

            if price > discharge_threshold:

                if current_storage_kg > 0 or current_TES_storage_kWh > 0:

                    # OPERATING MODE 1 (STORAGE AND WIND -----> GRID)
                    df.at[idx, 'Operating_Mode'] = 1

                    # TES discharge
                    current_TES_storage_kWh -= tes_out
                    total_discharged_kWh += tes_out
                    total_to_Grid_kWh += row.get('E_elec_kWh', 0.0)
                    df.at[idx, 'TES_discharged_kWh'] = tes_out

                    # Wind transfer to grid
                    df.at[idx, 'Grid_transfer_kWh'] = row.get('E_elec_kWh', 0.0)

                    #CAES discharge
                    m_out = min(caes_discharge_rate, current_storage_kg)
                    current_storage_kg -= m_out             
                    total_discharged_kg += m_out
                    df.at[idx, 'CAES_discharged_kg'] = m_out
                    
                else:
                    # OPERATING MODE 2 (WIND -----> GRID)
                    df.at[idx, 'Operating_Mode'] = 2

                    df.at[idx, 'Grid_transfer_kWh'] = row.get('E_elec_kWh', 0.0)
                    total_to_Grid_kWh += row.get('E_elec_kWh', 0.0)
           
            elif price < charge_threshold:
                #available = max_CAES_cap - current_storage_kg
                available_TES = max_TES_cap - current_TES_storage_kWh

                #m_in = min(row.get('m_air_kg', 0.0), available) if current_storage_kg < max_CAES_cap else 0.0
                tes_in = min(row.get('E_TES_kWh', 0.0), available_TES) 

                if tes_in > 0:
                    # Operating Mode (OM 3)   
                    df.at[idx, 'Operating_Mode'] = 3

                    m_in = row['m_air_kg'] * (tes_in / row['E_TES_kWh'])
                    current_storage_kg += m_in
                    current_TES_storage_kWh += tes_in
                    df.at[idx, 'CAES_charging_kg'] = m_in
                    df.at[idx, 'TES_charging_kWh'] = tes_in

                    # Part of Electricity generated transfered to the grid directly
                    df.at[idx, 'Grid_transfer_kWh'] = row['E_elec_kWh'] * (1-(tes_in / row['E_TES_kWh']))
                    total_to_Grid_kWh += row['E_elec_kWh'] * (1-(tes_in / row['E_TES_kWh']))

                else:
                    # OPERATING MODE 2 (WIND -----> GRID)    
                    df.at[idx, 'Operating_Mode'] = 2
                    df.at[idx, 'Grid_transfer_kWh'] = row.get('E_elec_kWh', 0.0)
                    total_to_Grid_kWh += row.get('E_elec_kWh', 0.0)                   
           
            else:
                # OPERATING MODE 2 (WIND -----> GRID)    
                    df.at[idx, 'Operating_Mode'] = 2
                    df.at[idx, 'Grid_transfer_kWh'] = row.get('E_elec_kWh', 0.0)
                    total_to_Grid_kWh += row.get('E_elec_kWh', 0.0)
        else:
            if price > charge_threshold:
                if current_storage_kg > 0:
                    df.at[idx, 'Operating_Mode'] = 4
                    m_out = min(caes_discharge_rate, current_storage_kg)
                    current_storage_kg -= m_out             
                    current_TES_storage_kWh -= tes_out
                    total_discharged_kg += m_out
                    total_discharged_kWh += tes_out
                    total_to_Grid_kWh += 0.0    
                    df.at[idx, 'CAES_discharged_kg'] = m_out
                    df.at[idx, 'TES_discharged_kWh'] = tes_out
                    df.at[idx, 'Grid_transfer_kWh'] = 0.0
                    
                else:
                    df.at[idx, 'Operating_Mode'] = 5
            else:
                df.at[idx, 'Operating_Mode'] = 5

        # Update cumulative storage
        df.at[idx, 'Cumulative_CAES_storage_kg'] = current_storage_kg
        df.at[idx, 'Cumulative_TES_storage_kWh'] = current_TES_storage_kWh
        df.at[idx, 'Cumulative_CAES_discharged_kg'] = total_discharged_kg
        df.at[idx, 'Cumulative_TES_discharged_kWh'] = total_discharged_kWh*eta_t
        df.at[idx, 'Cumulative_Grid_transfer_kWh'] = total_to_Grid_kWh
    
    # Calculate percentage of operation modes over the entire period
    mode_counts = df['Operating_Mode'].value_counts(normalize=True) * 100
    for mode, pct in mode_counts.sort_index().items():
        df[f'Operating_Mode_{int(mode)}_Pct'] = pct

    # Print summary of percentages
    print("Operating mode percentages:")
    for mode, pct in mode_counts.sort_index().items():
        print(f"  Mode {int(mode)}: {pct:.2f}%")


    return df
