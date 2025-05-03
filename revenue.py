import pandas as pd

def calculate_revenue(
                      df, 
                      grid_price_col='price', 
                      tes_discharge_col='TES_discharged_kWh',
                      export_col='Grid_transfer_kWh', 
                      power_output_wind_turbine='Total_Power_Output'
                      ):
    """
    Calculates total revenue from:
    1. Selling thermal energy discharged from TES (converted to electricity)
    2. Selling electricity sent directly to the grid from wind

    Parameters:
        df (DataFrame): Must include 'price', 'TES_discharged_kWh', and 'Grid_transfer_kWh' columns
        grid_price_col (str): Name of the column representing market price
        tes_discharge_col (str): Name of the column for TES discharge (in kWh)
        export_col (str): Name of the column for energy sent directly to grid from wind (in kWh)

    Returns:
        DataFrame with new columns:
            - 'Revenue_from_storage' (price * TES_discharged_kWh)
            - 'Revenue_from_grid' (price * Grid_transfer_kWh)
            - 'Total_Revenue'
    """
    
    df['Revenue_without_storage'] = df[grid_price_col] * df[power_output_wind_turbine]
    df['Revenue_from_storage'] = df[grid_price_col] * df[tes_discharge_col]
    df['Revenue_from_grid'] = df[grid_price_col] * df[export_col]
    df['Total_Revenue'] = df['Revenue_from_storage'] + df['Revenue_from_grid']
    
    total_without_storage = df['Revenue_without_storage'].sum()
    total_from_storage   = df['Revenue_from_storage'].sum()
    total_from_grid      = df['Revenue_from_grid'].sum()
    total_revenue        = df['Total_Revenue'].sum()
    annual_saving        = total_revenue-total_without_storage
    
    print(f"Total revenue without storage: €{total_without_storage:>15,.2f}")
    print(f"Total revenue from storage:    €{total_from_storage:>15,.2f}")
    print(f"Total revenue from grid:       €{total_from_grid:>15,.2f}")
    print(f"Grand total revenue:           €{total_revenue:>15,.2f}")
    print(f"Annual saving from storage:    €{annual_saving:>15,.2f}")

    return df