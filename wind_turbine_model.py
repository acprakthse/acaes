import pandas as pd
import numpy as np
from params import (pareto_wind_turbine) 

def read_wind_data(file_path):
 
    return pd.read_excel(file_path)

def calculate_power_output(df):


    df['Power_Output_1'] = (
        -0.7985 * (df['windspeed'] ** 4) +
        20.23 * (df['windspeed'] ** 3) -
        157.12 * (df['windspeed'] ** 2) +
        589.05 * df['windspeed'] -
        837.65
    )
    df['Power_Output_2'] = (
        -0.14452 * (df['windspeed'] ** 4) +
        2.9804 * (df['windspeed'] ** 3) -
        2.534 * (df['windspeed'] ** 2) -
        32.955 * df['windspeed'] +
        77.9625
    )
    df['Power_Output_3'] = (
        -0.0665 * (df['windspeed'] ** 4) +
        0.9589 * (df['windspeed'] ** 3) +
        6.2757 * (df['windspeed'] ** 2) -
        58.071 * df['windspeed'] +
        96.127
    )
    return df

def apply_conditions(df):

    # Turbine 1 conditions (2MW)
    mask1_cut_in = df['windspeed'] < 3.5
    mask1_shutdown = df['windspeed'] > 25
    mask1_rated = (df['windspeed'] >= 12.5) & (df['windspeed'] <= 25.1)
    df.loc[df['Power_Output_1'] < 0, 'Power_Output_1'] = 0
    df.loc[df['Power_Output_1'] > 2000, 'Power_Output_1'] = 2000
    df.loc[mask1_rated, 'Power_Output_1'] = 2000
    df.loc[mask1_shutdown, 'Power_Output_1'] = 0
    df.loc[mask1_cut_in, 'Power_Output_1'] = 0

    # Turbine 2 conditions (1.75MW)
    mask2_cut_in = df['windspeed'] < 3.5
    mask2_shutdown = df['windspeed'] > 25
    mask2_rated = (df['windspeed'] >= 15) & (df['windspeed'] <= 25.1)
    df.loc[df['Power_Output_2'] < 0, 'Power_Output_2'] = 0
    df.loc[df['Power_Output_2'] > 1750, 'Power_Output_2'] = 1750
    df.loc[mask2_rated, 'Power_Output_2'] = 1750
    df.loc[mask2_shutdown, 'Power_Output_2'] = 0
    df.loc[mask2_cut_in, 'Power_Output_2'] = 0

    # Turbine 3 conditions (0.66MW)
    mask3_cut_in = df['windspeed'] < 4
    mask3_shutdown = df['windspeed'] > 25
    mask3_rated = (df['windspeed'] >= 17) & (df['windspeed'] <= 25.1)
    df.loc[df['Power_Output_3'] < 0, 'Power_Output_3'] = 0
    df.loc[df['Power_Output_3'] > 660, 'Power_Output_3'] = 660
    df.loc[mask3_rated, 'Power_Output_3'] = 660
    df.loc[mask3_shutdown, 'Power_Output_3'] = 0
    df.loc[mask3_cut_in, 'Power_Output_3'] = 0

    # Calculate total power output using the given turbine counts:
    total_power = (df['Power_Output_1'] * 3 * pareto_wind_turbine +
                   df['Power_Output_2'] * 3 * pareto_wind_turbine +
                   df['Power_Output_3'] * 6 * pareto_wind_turbine)
    df['Total_Power_Output'] = (total_power) 
    # Count rows in DataFrame and print
    num_rows = len(df)
    print(f"Number of Hours Operation: {num_rows}")

    total_cap_wind_turbine = (3*2000+3*1750+6*660)*pareto_wind_turbine
    cumulative_total_power = df['Total_Power_Output'].sum()
    wind_turbine_cap_fac = cumulative_total_power / (total_cap_wind_turbine * num_rows) * 100

    print(f"Capacity Factor of Wind Farm: {wind_turbine_cap_fac:>15.2f} %")
    print(f"Capacity of Wind Farm: {total_cap_wind_turbine:>15,.0f} kW")
     

    return df
