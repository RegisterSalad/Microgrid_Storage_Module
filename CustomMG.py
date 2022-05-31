import sys
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

TIMESTEPS = 86400 # Number of seconds in a day of operation

def create_base_grid(grid_type = 'perfect'):
    df_grid = pd.DataFrame() # Create Empy grid dataframe
    if grid_type == 'disaster':
        #disater grid logic
        return df_grid

    elif grid_type == 'weak':
        #weak grid logic
        return df_grid

    elif grid_type == 'perfect':
        #perfect grid logic
        return df_grid

    elif grid_type == 'test': 
        #Enter Preset Values

        #Genset of Test Grid
        df_grid['genset']['genset_min'] = 1000 # Minimum required generator set size in kWh
        df_grid['genset']['genset_max'] = 1500 # Maximum allowed generator set size in kWh
        df_grid['genset']['ramping_rate'] = 12 # Power per second in kW/s
        df_grid['genset']['capacity cost'] = 335 # Cost of installation for average internal combustion generator sets in USD $ 

        # Storage of Test Grid
        df_grid['storage']['li_capacity'] = 1 # Capacity In kWh
        df_grid['storage']['li_max_discharge'] = 1 # Max power output kilowatts
        df_grid['storage']['li_max_charge'] = 1 # Max power input kilowatts
        df_grid['storage']['li_cost_per_kWh'] = 135 # in USD $
        #  Ion Flow 
        df_grid['storage']['flow_cap'] = 40 # Capacity In kWh
        df_grid['storage']['flow_max_discharge'] = 20 # Max power output in kilowatts
        df_grid['storage']['flow_max_charge'] = 20 # Max power input in kilowatts
        df_grid['storage']['flow_cost_per_kWh'] = 54 # in USD $
        # Flywheel
        df_grid['storage']['flywheel_cap'] = 64 # Capacity In kWh
        df_grid['storage']['flywheeel_max_discharge'] = 8 #Max power output in kilowatts
        df_grid['storage']['flywheeel_max_charge'] = 8 #Max power input in kilowatts
        df_grid['storage']['flywheel_cost_per_kWh'] = 330 # in USD $

        #Grid Restrictions
        #Load minimum in kW
        df_grid['requirements']['load_min'] = 2000
        # Photovolteic Contraints in kW
        df_grid['requirements']['pv_min'] = 2000
        df_grid['requirements']['pv_max'] = 2400
        # Highest ammount that the all grid components can cost (installation not included) in $ (component cost is varible)
        df_grid['requirements']['component_cost_max'] = 500000
        # Local Power cost in $
        df_grid['requirements']['local_power_cost'] = 0.11 # $USD per kWh
        # Uptime of the microgrid if main grid goes down
        df_grid['requirements']['reliability'] = grid_type # Whether or not the grid is in a disaster scenario
	#Outages
	
        
        return df_grid
    else:
        return 0

    
#Print all final values from the grid into an excel spreadsheet 
# Disaster grid profile must be implimented
# Genrator set class
class Genset:
    ''' Contains all parameters of grid generator set.
        Gensets cost fuel to operate and cut into grid margins '''
    def __init__(self, df_grid):
        self.genset_min = df_grid['genset']['genset_min'] # Minimum required generator set size in kWh
        self.genset_max = df_grid['genset']['genset_max'] # Maximum allowed generator set size in kWh
        self.ramping_rate = df_grid['genset']['ramping_rate'] # Power per second in kW/s
        self.cost_per_capacity = df_grid['genset']['capacity cost'] # Cost of installation for average internal combustion generator sets in USD $ 
        
    
# Energy storage class
class Storage:
    ''' Contains the parameters for the battery types
        Battery types are:
        - Lithium Ion Batteries
        -  Ion Flow Batteries
        - Flywheel Storage '''
    def __init_(self, df_grid):
        ''' Maximums for capacities and power '''
        # Lithium Ion
        self.li_cap = df_grid['storage']['li_capacity'] # In kWh
        self.li_max_discharge = df_grid['storage']['li_max_discharge'] # # Max power output in kilowatts
	self.li_max_charge = df_grid['storage']['li_max_charge'] # Max power input in kilowatts
        self.li_cost_per_kWh = df_grid['storage']['li_cost_per_kWh'] # in USD $
        #  Ion Flow 
        self.flow_cap = df_grid['storage']['flow_cap'] # In kWh
        self.flow_max_discharge = df_grid['storage']['flow_max_discharge'] # Max power output in kilowatts
	self.flow_max_charge = df_grid['storage']['flow_max_charge'] # Max power input in kilowatts
        self.flow_cost_per_kWh = df_grid['storage']['flow_cost_per_kWh'] # in USD $
        # Flywheel
        self.flywheel_cap = df_grid['storage']['flywheel_cap'] # In kWh
        self.flywheel_max_discharge = df_grid['storage']['flywheeel_max_discharge'] # Max power output in kilowatts
	self.flywheel_max_charge = df_grid['storage']['flywheeel_max_charge'] # Max power input in kilowatts
        self.flywheel_cost_per_kWh = df_grid['storage']['flywheel_cost_per_kWh'] # in USD $

    def get_lithium_performance(self, li_cap, li_max_power):
        ''' Uses the performance profile of bulk storage lithium Ion cells to return the power capabilities evey time step '''
	    # li_pow = self.li_max_power - (self
    def total_cost(self):
        return self.li_cap * self.li_cost_per_kWh

                 
        
# Grid design class
class GridDesign:   
    ''' This class contains all the elements of the designed grids
        The grid will be desinged with 1 scenario in mind each. Grids cannot be modified during the scenario.
        The score that each grid gets will be a part of how the network finds patterns and adjust new designs
        Score will be determined by traking the price of the grid and how it long it can remain opperational '''
    def __init__(self, df_grid): #requiremtns is pandas dataframe
        ''' Parse requirements dictionary into single values to opperate on '''
        # Load minimum in kW
        self.load_min =  df_grid['requirements']['load_min']
        # Photovolteic Contraints in kW
        self.pv_min = df_grid['requirements']['pv_min']
        self.pv_max = df_grid['requirements']['pv_max']
        # Highest ammount that the all grid components can cost (installation not included) in USD $ (component cost is varible)
        self.component_cost_max = df_grid['requirements']['component_cost_max']
        # Local Power cost per kWh USD $
        self.local_power_cost = df_grid['requirements']['local_power_cost']
        # Grid Scenario Type
        self.reliablity = df_grid['requirements']['reliability'] # Whether or not the grid is in a disaster scenario

# TIMESTEP DEPENDENT, NOT STATIC
    def get_mg_exports(self, df_pv, df_genset, df_flywheel, df_flow): 
        ''' Function returns dataframe the total ammount of kWh that the grid can export every timestep '''
        df_total_self_gen = pd.DataFrame(df_pv[i] + df_genset[i] + df_flywheel[i] + df_flow[i] for i in range (0, TIMESTEPS) )
        return df_total_self_gen

    def get_uptime(self, df_grid):
        pass

    def get_cost_per_kwh(self, local_power_cost):  
        ''' Retuns dataframe will power cost per kWh when connected to this micro-grid '''
        df_cost_with_offset = 0 #placeholder
        return df_cost_with_offset
