import math
import pandas as pd
import numpy as np
#from Cavern_model import E_max_s9, E_max_s12, E_max_s14, E_max_s16

# includes the economical calculations and data
#compressor charge = 22.5 kg/s
# CAPEX
#cost per V47 -660 turbine
#Capex_V47 = 10741247.26 #SEK
Capex_V47 = 10741247.26/11.4 #EU


# using the above price we could assume the price per mw to be 16274617 sek per mw
Capex_wind_tot= Capex_V47/660*1000*15.21
#capex 1.75 and 2 MW


#Capex storage system
#CAPEX power range between 1200-2000 eu/kW
P_max_s9 = 2.3377027949851086 #MW
P_max_s12 = 2.23125695518165576 #MW
P_max_s14= 2.141176953504475 #MW
P_max_s16 = 2.137651629530287 #MW

CAPEX_storage_mean = (1200 + 2000)/ 2 * 1000 # eu / mw
#s9
CAPEX_s9 = P_max_s9 *CAPEX_storage_mean #eu
print(CAPEX_s9)
CAPEX_total_s9 = Capex_wind_tot + CAPEX_s9
print(CAPEX_total_s9)
#s12
CAPEX_s12 = P_max_s12 *CAPEX_storage_mean #eu
CAPEX_total_s12 = Capex_wind_tot + CAPEX_s12
print(CAPEX_total_s12)
#s14
CAPEX_s14 = P_max_s14 *CAPEX_storage_mean #eu
CAPEX_total_s14 = Capex_wind_tot + CAPEX_s14
print(CAPEX_total_s14)
#s16
CAPEX_s16 = P_max_s16 *CAPEX_storage_mean #eu
CAPEX_total_s16 = Capex_wind_tot + CAPEX_s16
print(CAPEX_total_s16)



#OPEX assume at 4% of capex
OPEX_wind_tot = Capex_wind_tot * 0.04
#range of opex lies between 400k-600k SEK per MW for windturbine
#OPEX_wind_low = 400000 #sek
#OPEX_wind_high = 600000 #sek

OPEX_system_s9 = 0.04 * CAPEX_s9
OPEX_system_s12 = 0.04 * CAPEX_s12
OPEX_system_s14 = 0.04 * CAPEX_s14
OPEX_system_s16 = 0.04 * CAPEX_s16

OPEX_total_s9 =OPEX_wind_tot + OPEX_system_s9
OPEX_total_s12 =OPEX_wind_tot + OPEX_system_s12
OPEX_total_s14=OPEX_wind_tot + OPEX_system_s14
OPEX_total_s16 =OPEX_wind_tot + OPEX_system_s16

discount_rate = 0.05 # assumption
lifetime = 20 # assuming atleast 30 years, but 20 years as the turbines themsleves last shorter

# assume annual enery output
Energy_Output = 49304.72 #MWh

CRF = (discount_rate*(1+discount_rate)**lifetime)/((1+discount_rate)**lifetime - 1)
print(CRF)

LCOE_s9 = (CAPEX_total_s9*CRF + OPEX_total_s9) / Energy_Output
print(LCOE_s9)
LCOE_s12 = (CAPEX_total_s12*CRF + OPEX_total_s12) / Energy_Output
print(LCOE_s12)
LCOE_s14 = (CAPEX_total_s14*CRF + OPEX_total_s14) / Energy_Output
print(LCOE_s14)
LCOE_s16 = (CAPEX_total_s16*CRF + OPEX_total_s16) / Energy_Output
print(LCOE_s16)


