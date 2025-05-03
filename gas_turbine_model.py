import pandas as pd


def gas_turbine_discharge(
    df: pd.DataFrame,
    discharge_threshold: float = 0.05,
    turbine_capacity_kW: float = 5000.0,
    eta_turbine: float = 0.85,
) -> pd.DataFrame:
    """
    Models the discharge of stored compressed air (CAES) and thermal energy (TES)
    through a gas turbine to generate electricity.

    Parameters:
        df (pd.DataFrame): DataFrame with columns:
            - 'price': electricity price or dispatch signal.
            - 'Delta_h_kJ_per_kg': enthalpy change per kg of air from compressor.
            - 'Cumulative_CAES_storage_kg': current CAES storage mass [kg].
            - 'Cumulative_TES_storage_kWh': current TES storage energy [kWh].
        discharge_threshold (float): price threshold above which to discharge.
        turbine_capacity_kW (float): maximum turbine capacity [kW].
        eta_turbine (float): overall efficiency of the gas turbine (decimal).

    Returns:
        pd.DataFrame: DataFrame with added columns:
            - 'CAES_discharged_kg': mass of air discharged [kg].
            - 'TES_discharged_kWh': thermal energy used [kWh].
            - 'GT_elec_output_kWh': electricity generated [kWh].
            - 'Remaining_CAES_storage_kg': post-discharge CAES storage [kg].
            - 'Remaining_TES_storage_kWh': post-discharge TES storage [kWh].
    """
    # Initialize output columns
    df['CAES_discharged_kg'] = 0.0
    df['TES_discharged_kWh'] = 0.0
    df['GT_elec_output_kWh'] = 0.0
    df['Remaining_CAES_storage_kg'] = 0.0
    df['Remaining_TES_storage_kWh'] = 0.0

    # Start state from first row's cumulative storage
    if not df.empty:
        current_storage_kg = float(df.iloc[0]['Cumulative_CAES_storage_kg'])
        current_TES_kWh = float(df.iloc[0]['Cumulative_TES_storage_kWh'])
    else:
        return df

    # Loop through each timestep
    for idx, row in df.iterrows():
        price = float(row.get('price', 0.0))
        delta_h = float(row.get('Delta_h_kJ_per_kg', 0.0))  # kJ per kg from compressor
        # Energy from compressed air per kg in kWh
        E_caes_per_kg_kWh = delta_h / 3600.0

        # Dispatch decision
        if price >= discharge_threshold and current_storage_kg > 0:
            # TES energy per kg of stored air
            TES_per_kg = current_TES_kWh / current_storage_kg if current_storage_kg > 0 else 0.0

            # Total available energy per kg before turbine
            E_sum_per_kg = E_caes_per_kg_kWh + TES_per_kg
            # Mass required to hit capacity
            m_req = turbine_capacity_kW / E_sum_per_kg if E_sum_per_kg > 0 else 0.0
            # Actual mass discharged
            m_out = min(current_storage_kg, m_req)
            # Thermal energy drawn from TES
            TES_out = TES_per_kg * m_out

            # Electricity generated (accounting for turbine efficiency)
            E_out = (E_caes_per_kg_kWh * m_out + TES_out) * eta_turbine

            # Update storage states
            current_storage_kg -= m_out
            current_TES_kWh -= TES_out

            # Record discharge
            df.at[idx, 'CAES_discharged_kg'] = m_out
            df.at[idx, 'TES_discharged_kWh'] = TES_out
            df.at[idx, 'GT_elec_output_kWh'] = E_out

        # Record remaining storage after potential discharge or idle
        df.at[idx, 'Remaining_CAES_storage_kg'] = current_storage_kg
        df.at[idx, 'Remaining_TES_storage_kWh'] = current_TES_kWh

    return df
