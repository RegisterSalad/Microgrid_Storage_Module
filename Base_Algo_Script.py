import sys
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

TIMESTEPS = 86400 # Number of seconds in a day of operation

#Print all final values from the grid into an excel spreadsheet 
# Disaster grid profile must be implimented
# Genrator set class
class genset():
    ''' Contains all parameters of grid generator set.
        Gensets cost fuel to operate and cut into grid margins '''
    def __init__(self, df_genset):
        self.genset_min = df_genset['genset_min']
        self.genset_max = df_genset['genset_max']
        self.ramping_rate = df_genset['ramping_rate']
        
    
# Energy storage class
class storage():
    ''' Contains the parameters for the battery types
        Battery types are:
        - Lithium Ion Batteries
        - Vanadium Ion Flow Batteries
        - Flywheel Storage '''
    def __init_(self, df_storage):
        ''' Maximums for capacities and power '''
        # Lithium Ion
        self.li_cap = df_storage['li_size'] # In kWh
        self.li_max_power = df_storage['li_max_power'] # In kilowatts
        # Vanadium Ion Flow 
        self.vanadiumflow_cap = df_storage['vanadiumflow_cap'] # In kWh
        self.vanadiumflow_max_power = df_storage['vanadiumflow_max_power'] # In kilowatts
        # Flywheel
        self.flywheel_cap = df_storage['flywheel_cap'] # In kWh
        self.flywheel_max_power = df_storage['flywheeel_max_power'] # In kilowatts
    def get_lithium_performance(self, li_cap, li_max_power):
        ''' Uses the performance profile of bulk storage lithium Ion cells to return the power capabilities evey time step '''
	# li_pow = self.li_max_power - (self

                 
        
# Grid design class
class grid_design():   
    ''' This class contains all the elements of the designed grids
        The grid will be desinged with 1 scenario in mind each. Grids cannot be modified during the scenario.
        The score that each grid gets will be a part of how the network finds patterns and adjust new designs
        Score will be determined by traking the price of the grid and how it long it can remain opperational '''
    def __init__(self, df_requirements): #requiremtns is pandas dataframe
        ''' Parse requirements dictionary into single values to opperate on '''

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
        self.reliablity = df_requirements['reliability'] # Whether or not the grid is in a disaster scenario
	

    def get_mg_exports(self, df_pv, df_genset, df_flywheel, df_vanadiumflow): 
        ''' Function returns dataframe the total ammount of kWh that the grid can export every timestep '''
        df_total_self_gen = pd.DataFrame(df_pv[i] + df_genset[i] + df_flywheel[i] + df_vanadiumflow[i] for i in range (0, TIMESTEPS) )
        return df_total_self_gen

    def get_cost_per_kwh(self, local_power_cost):  
        ''' Retuns dataframe will power cost per kWh when connected to this micro-grid '''
        df_cost_with_offset = 0 #placeholder
        return df_cost_with_offset
    

    
    
