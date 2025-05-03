import math
import pandas as pd
import numpy as np


# Inputs for the different Cavern options
R_specific = 287.058 #, J kg−1 K−1
V̇_turbine = 22.5 # Max air flowrate (Kg/s)
V_turbine = 7.79 #Mwh


#Cavern S9
P_max_s9 = 2.87*1000000 #Reservoir pressure (Pa)
T_s9 = 15.3+273.15 # Reservoir Temperature (K)
V_pore_s9 = 365877 # Pore Volume (m3)
V̇_s9 = 34.6 # Max air flowrate (Kg/s)
max_CAES_cap_s9 = P_max_s9 * V_pore_s9 / (T_s9 * R_specific) #Kg
E_max_s9 = 366 #MWh
Pw_max_s9 = E_max_s9 / (max_CAES_cap_s9/V̇_turbine/3600)
print(max_CAES_cap_s9/10**7)
print (Pw_max_s9) #MW

#Cavern S12
P_max_s12 = 3.01*1000000 #Reservoir pressure (Pa)
T_s12 = 15.7+273.15 # Reservoir Temperature (K)
V_pore_s12 = 515013 # Pore Volume (m3)
V̇_s12 = 124.1 # Max air flowrate (Kg/s)
max_CAES_cap_s12 = P_max_s12 * V_pore_s12 / (T_s12 * R_specific) #Kg
E_max_s12 = 515 #MWh
Pw_max_s12 = E_max_s12 / (max_CAES_cap_s12/V̇_turbine/3600)
print (max_CAES_cap_s12/10**7)
print (Pw_max_s12)

#Cavern S14
P_max_s14 = 3.14*1000000 #Reservoir pressure (Pa)
T_s14 = 16.1+273.15 # Reservoir Temperature (K)
V_pore_s14 = 265089 # Pore Volume (m3)
V̇_s14 = 68.6 # Max air flowrate (Kg/s)
max_CAES_cap_s14 = P_max_s14 * V_pore_s14 / (T_s14 * R_specific) #Kg
E_max_s14 = 265 #MWh
Pw_max_s14 = E_max_s14 / (max_CAES_cap_s14/V̇_turbine/3600)
print(max_CAES_cap_s14/10**7)
print (Pw_max_s14)

#Cavern S16
P_max_s16 = 3.16*1000000 #Reservoir pressure (Pa)
T_s16 = 16.2+273.15 # Reservoir Temperature (K)
V_pore_s16 = 83663 # Pore Volume (m3)
V̇_s16 = 102.1 # Max air flowrate (Kg/s)
max_CAES_cap_s16 = P_max_s16 * V_pore_s16 / (T_s16 * R_specific) #Kg
E_max_s16 = 84 #MWh
Pw_max_s16 = E_max_s16 / (max_CAES_cap_s16/V̇_turbine/3600)
print (max_CAES_cap_s16/10**7)
print (Pw_max_s16)
# Model of the cavern

#Possible formula for describing the amount of energy sotred int the cavern

P_atm =  101.325 # atmospheric pressure(kPa)
P_cavern = P_max_s9
V_cavern = V_pore_s9
E_store_CAES = P_cavern * V_cavern * math.log(P_cavern/P_atm) #


    

