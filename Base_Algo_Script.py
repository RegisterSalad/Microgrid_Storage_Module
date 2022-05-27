import sys
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

TIMESTEPS = 8760

#Print all final values from the grid into an excel spreadsheet 
class grid_design():
    ''' This class contains all the elements of the designed grids
        The grid will be desinged with 1 scenario in mind each. Grids cannot be modified during the scenario.
        The score that each grid gets will be a part of how the network finds patterns and adjust new designs
        Score will be determined by traking the price of the grid and how it long it can remain opperational  '''
    def __init__(self, df_requirements): #requiremtns is pandas dataframe
        # Parse requirements dictionary into single values to opperate on

        # Load minimum in kWh
        self.load_min =  df_requirements['load_min']
        
        # Photovolteic Contraints in kWh
        self.pv_min = df_requirements['pv_min']
        self.pv_max = df_requirements['pv_max']

        # Highest ammount that the all grid components can cost (installation not included) in $ (component cost is varible)
        self.component_cost_max = df_requirements['component_cost_max']

        # Local Power cost in $
        self.local_power_cost = df_requirements['local_power_cost']
        # Uptime of the microgrid if main grid goes down
        self.reliablity_min = df_requirements['requirements']

    def get_mg_export(self, df_pv, df_genset, df_flywheel, df_vanadiumflow): 
        # Function returns dataframe the total ammount of kWh that the grid can export every timestep
        df_total_self_gen = pd.DataFrame(df_pv[i] + df_genset[i] + df_flywheel + df_vanadiumflow for i in range (0, TIMESTEPS) )
        return df_total_self_gen

    def get_cost_per_kwh(self, local_power_cost):  
        # Retuns dataframe will power cost per kWh when connected to this micro-grid
        df_cost_with_offset = 0 #placeholder
        return df_cost_with_offset
    
    
