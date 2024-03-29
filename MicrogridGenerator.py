"""
Copyright 2020 Total S.A., Tanguy Levent all rights reserved,
Authors:Gonzague Henri <gonzague.henri@total.com>, Tanguy Levent <>
Permission to use, modify, and distribute this software is given under the
terms of the pymgrid License.
NO WARRANTY IS EXPRESSED OR IMPLIED.  USE AT YOUR OWN RISK.
$Date: 2020/06/04 14:54 $
Gonzague Henri
"""

"""
<pymgrid is a Python library to simulate microgrids>
Copyright (C) <2020> <Total S.A.>

This program is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.

"""

from msilib.schema import Error
import numpy as np
import pandas as pd
from requests import NullHandler
from . import Microgrid
from os import listdir
from os.path import isfile, join
import os
import sys
import pickle
from IPython.display import display
from pathlib import Path
import random
# from Storage import StorageSuite
# HOUR = 3600/900 # Number of seconds in hour
# DAY = 86400/900 # Number of seconds in day
# MONTH = 2631600/900 # Number of seconds in month
# YEAR =31579200/900 # Number of seconds in year (non-leap)
# ZERO = 10**-5

HOUR = 4 # 15 Min intervals in an hour
DAY = 96 # Number of 15 Min intervals in day
MONTH = 2_924 # Number of 15 Min intervals in month
YEAR =35_088 # Number of 15 Min intervals in year (non-leap)
ZERO = 10**-5

# MICROGRID_DEFAULT_CONFIG : {
#     'load_type':'Folder', #or 'File'
#     'load_path': 'default', # or a specific path
#     'pv_type':'Folder', #or 'File'
#     'pv_path': 'default', # or a specific path
#     'co2_type':'Folder', #or 'File'
#     'co2_path': 'default', # or a specific path


#     'parameters':{

#     }, #Dictionary
#     'df_actions':df_actions, #Dataframe
#     'architecture':architecture, #Dictionary
#     'df_status':df_status, #Dictionary
#     'df_actual_generation':df_actual_production,#Dataframe
#     'grid_spec':grid_spec, #value = 0
#     'df_cost':df_cost, #Dataframe of 1 value = 0.0
#     'df_co2': df_co2,
#     'pv':pv, #Dataframe
#     'load': load, #Dataframe
#     'grid_ts':grid_ts, #Dataframe
#     'control_dict': column_actions, #dictionnary
#     'grid_price_import' : grid_price_import_ts,
#     'grid_price_export' : grid_price_export_ts,
#     'grid_co2': grid_co2_ts,
# }

class MicrogridGenerator:
    """
        The class MicrogridGenerator generates a number of microgrids with differerent and randomized paramters based on
        the load and renewable data files in the data folder.

        Parameters
        ----------
            nb_microgrid: int, optional
                Number representing the number of microgrid to be generated.
            random_seed: int, optional
                Seed to be used to generate the needed random numbers to size microgrids.
            timestep: int, optional
                Timestep to be used in the time series.
            path: string
                The path to the pymgrid folder, used to get the data files needed.

        Attributes
        ----------
        self.microgrids= [] # generate a list of microgrid object
        #self.annual_load
        self.nb_microgrids=nb_microgrid
        self.timestep=1
        self.path=path

            microgrids: list
                List that contains all the generated microgrids
            nb_microgrid: int, optional
                Number representing the number of microgrid to be generated.
                this microgrid has one of them
            timestep: int, optional
                Timestep to be used in the time series.
            path: string
                The path to the pymgrid folder, used to get the data files needed.

        Notes
        -----
        Due to the random nature of the implemented process, all the generated microgrids might not make the most sense
        economically or in term of generator sizing. The main idea is to generate realistic-ich microgrids to develop,
        test and compare control algorithms and advance AI research applied to microgrids.

        Examples
        --------
        To create microgrids through MicrogridGenerator:
        >>> m_gen=mg.MicrogridGenerator(nb_microgrid=10)
        >>> m_gen.generate_microgrid()

        To plot informations about the generated microgrids:
        >>> m_gen.print_mg_parameters()
        """


    def __init__(self,
                 random_seed=88,
                 timestep=1,
                 path=str(Path(__file__).parent),
                 storage_suite_list: list = None):
        if str(type(storage_suite_list[0])) != "<class 'Storage.StorageSuite'>":
            raise TypeError(f"Please provide Storage class instances, 1 per mircogrid requested. Provided a {str(type(storage_suite_list[0]))}")
        np.random.seed(random_seed)
        #todo manage simulation duration and different timesteps
        #todo create an architecture argument to fix an architetcture (pymgrid10)
        self.microgrids= [] # generate a list of microgrid object
        #self.annual_load
        self.nb_microgrids=len(storage_suite_list)
        self.timestep=1
        self.path=path
        self.interpolate = '15_m'
        self.ss_list = storage_suite_list


    ###########################################
    #utility functions
    ###########################################
    def _get_random_file(self, path):
        """ Based on a path, and a folder containing data files, return a file chosen randomly."""

        onlyfiles = [f for f in listdir(path) if isfile(join(path, f))]
        #todo check for files name in a cleanedr way
        onlyfiles.remove('__init__.py')
        if '.DS_Store'  in onlyfiles:
            onlyfiles.remove('.DS_Store')

        file = pd.read_csv(path + onlyfiles[np.random.randint(low=0, high=len(onlyfiles))])

        # get number of files in our database
        # generate a random integer to select the files
        # Resample the file if needed
        return file
            
    def _scale_ts(self, df_ts, size, scaling_method='sum'):
        """ Scales a time series based on either the sum or the maximum of the time series."""

        actual_ratio=1
        if scaling_method =='sum':
            actual_ratio = size/df_ts.sum()#.values[0]

        if scaling_method == 'max':
            actual_ratio=size / df_ts.max()
        df_ts = df_ts * actual_ratio

        return df_ts

    def _resize_timeseries(self, timeserie, current_time_step, new_time_step):
        """ Change the frequency of a time series. """

        index = pd.date_range('1/1/2022 00:00:00', freq=str(int(current_time_step * 4)) + 'S',
                              periods=(len(timeserie)))  # , freq='0.9S')

        unsampled = pd.Series(timeserie, index=index)
        resampled = unsampled.resample(rule=str(int(new_time_step * 60)) + 'S').mean().interpolate(method='linear')

        return resampled.values

    ###########################################
    # methods to generate timeseries
    ###########################################

    def _get_pv_ts(self):
        """ Function to get a random PV file."""
        #open pv folder
        # get list of file
        # select randomly rank if file to select in the list
        path = self.path+'/data/pv/'
        return pd.DataFrame(self._resize_timeseries(timeserie=self._get_random_file(path).values.flatten(),current_time_step=60,new_time_step=1))


    def _get_load_ts(self):
        """ Function to get a random load file. """
        #open load folder
        # get list of file
        # select randomly rank if file to select in the list
        path = self.path+'/data/load/'
        return pd.DataFrame(self._resize_timeseries(timeserie=self._get_random_file(path).values.flatten(),current_time_step=60,new_time_step=1))
        

    def _get_wind_ts(self):
        """ Function to get a random wind file. """
        #open load folder
        # get list of file
        # select randomly rank if file to select in the list
        path = self.path+'/data/wind/'
        return pd.DataFrame(self._resize_timeseries(timeserie=self._get_random_file(path).values.flatten(),current_time_step=60,new_time_step=1))

    def _get_co2_ts(self):
        """ Function to get a random wind file. """
        # open load folder
        # get list of file
        # select randomly rank if file to select in the list
        path = self.path + '/data/co2/'
        return pd.DataFrame(self._resize_timeseries(timeserie=self._get_random_file(path).values.flatten(),current_time_step=60,new_time_step=1))

    def _get_genset(self, rated_power=1000, pmax=0.9, pmin=0.05):
        """ Function generates a dictionnary with the genset information. """

        polynom=[np.random.rand()*10, np.random.rand(), np.random.rand()/10] #fuel consumption

        genset={
            'polynom':polynom,
            'rated_power':rated_power,
            'pmax':pmax,
            'pmin':pmin,
            'fuel_cost':0.4,
            'co2':2,
        }

        return genset

    def _get_electricity_tariff(self):
        price_import = []
        price_export = []
        for i in range(YEAR):
            price_import.append(0.11/4_000)
            price_export.append(0.05/4_000)
        return price_import, price_export


    def _get_grid(self, rated_power=1000, weak_grid=0, pmin=0.2, price_export = 0, price_import =0.3):
        """ Function generates a dictionnary with the grid information. """
        if weak_grid == 1:
            grid_ts = self._generate_weak_grid_profile(YEAR)
        else:
            grid_ts = pd.DataFrame(np.ones(int(np.floor(YEAR))),columns=['grid_variables'])
        # Make sure grid_ts is of length YEAR
        grid_ts = grid_ts.iloc[:YEAR]
        price_import, price_export = self._get_electricity_tariff()
        grid={
                'grid_power_import':rated_power,
                'grid_power_export':rated_power,
                'grid_ts':grid_ts,
                'grid_price_export':pd.DataFrame(price_export),
                'grid_price_import': pd.DataFrame(price_import),
        }
        return grid


    def _generate_weak_grid_profile(self,nb_time_step_per_year):
        """ Function generates an outage time series to be used in the microgrids with a weak grid. """
        #profile of ones and zeros
        duration_of_outage = np.random.randint(int(HOUR/6),HOUR*3)
        outage_per_day = (np.random.randn()*3/4 +0.25)*5
        weak_grid_timeseries = np.random.random(int(nb_time_step_per_year+1) ) #for a number of time steps, value between 0 and 1
        weak_grid_timeseries = [0 if weak_grid_timeseries[i] < outage_per_day/DAY else 1 for i in range(len(weak_grid_timeseries))]
        for i in range(len(weak_grid_timeseries)):
            if weak_grid_timeseries[i] == 0:
                duration_of_outage = np.random.randint(int(HOUR/6),HOUR*3)
                for j in range(1, int(duration_of_outage)):
                    if i-j > 0:
                        weak_grid_timeseries[i-j] = 0
        #print weak_grid_timeseries

        return pd.DataFrame(weak_grid_timeseries, columns=['grid_variables']) #[0 if weak_grid_timeseries[i] < h_outage_per_day/24 else 1 for i in range(len(weak_grid_timeseries))]
   

    ###########################################
    # sizing functions
    ###########################################
    def _size_mg(self, load, size_load):
        '''
         Function that returns a dictionnary with the size of each component of a microgrid. We chose to define PV
         penetration as defined by NREL (https://www.nrel.gov/docs/fy12osti/55094.pdf)
         PV penetration = peak PV power / peak load power
         '''
        # generate a list of size based on the number of architecture  generated
        # 2 size the other generators based on the load

        #PV penetration definition by NREL: https: // www.nrel.gov/docs/fy12osti/55094.pdf
        # penetragion = peak pv / peak load
        pv=load.max().values[0]*(np.random.randint(low=30, high=151)/100)
        
        self.li_battery, self.flow_battery, self.flywheel = self.ss.unpack() # These are objects of the Storage class
        
        size={
            'pv': pv,
            'load': size_load,
            'li_battery': self.li_battery.cap,
            'flow_battery': self.flow_battery.cap,
            'flywheel': self.flywheel.cap,
            'genset': self._size_genset(load),
            'grid': int(max(load.values)*2),
        }
        return size

    def _size_genset(self, load, max_operating_loading = 0.9):
        """ Function that returns the maximum power a genset. """
        #random number > 3 < 20
        # polynomial for fuel consumption
        # Is able to match 90% of max load
        _size_genset = int(np.ceil(np.max(load.values)/max_operating_loading))
        return _size_genset

    # ##########################################
    # generate the microgrid
    # ##########################################

    def generate_microgrid(self, verbose=True, interpolate = False) -> object:
        """ Function used to generate the nb_microgrids to append them to the microgrids list. It also returns the storage suite object """
        self.interpolate = interpolate
        for i in range(self.nb_microgrids):
            self.microgrids.append(self._create_microgrid(idx = i))
        
        if verbose == True:
            self.print_mg_parameters()
        
        return self.ss 

    def _create_microgrid(self, idx):
        """
        Function used to create one microgrid. First selecting a load file, and a load size  and a randome architecture
        and then size the other components of the microgrid depending on the load size. This function also initializes
        the tracking dataframes to be used in microgrid.
        """

        # get the sizing data
        # create microgrid object and append
        # return the list
        self.ss = self.ss_list[idx]
        architecture = {'PV':1, 'battery':1, 'genset':1, 'grid':1}
        size_load = self.ss.load
        load = self._scale_ts(self._get_load_ts(), size_load, scaling_method='max') #obtain dataframe of loads
        size = self._size_mg(load, size_load) #obtain a dictionary of mg sizing components
        column_actions=[]
        column_actual_production=[]
        column_cost = []
        grid_ts=[]
        grid_price_export_ts = []
        grid_price_import_ts = []
        grid_co2_ts = []
        df_parameters = pd.DataFrame()
        df_status = {}
        df_co2 = {'co2':[]}

        df_parameters['load'] = [size_load]
        df_parameters['load_size'] = size_load
        df_parameters['cost_loss_load'] = 10
        df_parameters['cost_overgeneration'] = 1
        df_parameters['cost_co2'] = 0.1
        df_status['load'] = [np.around(load.iloc[0,0],1)]
        df_status['hour'] = [0]
        column_actual_production.append('loss_load')
        column_actual_production.append('overgeneration')
        column_actions.append('load')
        column_cost.append('loss_load')
        column_cost.append('overgeneration')
        column_cost.append('co2')
        if architecture['PV'] == 1:

            df_parameters['PV_rated_power'] = np.around(size['pv'],2)
            column_actual_production.append('pv_consummed')
            column_actual_production.append('pv_curtailed')
            column_actions.append('pv_consummed')
            column_actions.append('pv_curtailed')
            column_actions.append('pv')
            pv = pd.DataFrame(self._scale_ts(self._get_pv_ts(), size['pv'], scaling_method='max'))
            df_status['pv'] = [np.around( pv.iloc[0].values[0],1)]

##############
# Logic for new storage types
##############

        self.li_battery.capa_to_charge
        self.li_battery.capa_to_discharge

        self.flow_battery.capa_to_charge
        self.flow_battery.capa_to_discharge

        self.flywheel.capa_to_charge
        self.flywheel.capa_to_discharge

        ################ Lithium Ion Battery ###################
        column_actual_production.append('li_ion_charge')
        column_actual_production.append('li_ion_discharge')
        column_actions.append('li_ion_charge')
        column_actions.append('li_ion_discharge')
        df_status['li_ion_soc'] = [self.li_battery.soc]
        df_status['li_ion_capa_to_charge'] = [self.li_battery.capa_to_charge]
        df_status['li_ion_capa_to_discharge'] = [self.li_battery.capa_to_discharge]
        ########################################################################################

        ################ Ion Flow Battery ###################
        column_actual_production.append('flow_charge')
        column_actual_production.append('flow_discharge')
        column_actions.append('flow_charge')
        column_actions.append('flow_discharge')
        df_status['flow_soc'] = [self.flow_battery.soc]
        df_status['flow_capa_to_charge'] = [self.flow_battery.capa_to_charge]
        df_status['flow_capa_to_discharge'] = [self.flow_battery.capa_to_discharge]
        ########################################################################################

        ################ Flywheel Energy Storage ###################
        column_actual_production.append('flywheel_charge')
        column_actual_production.append('flywheel_discharge')
        column_actions.append('flywheel_charge')
        column_actions.append('flywheel_discharge')
        df_status['flywheel_soc'] = [self.flywheel.soc]
        df_status['flywheel_capa_to_charge'] = [self.flywheel.capa_to_charge]
        df_status['flywheel_capa_to_discharge'] = [self.flywheel.capa_to_discharge]
        ########################################################################################


        grid_spec=0

        if architecture['grid']==1:
            rand_weak_grid = np.random.randint(low=1, high=2)
            architecture['genset'] = 1
            grid = self._get_grid(rated_power=size['grid'], weak_grid=rand_weak_grid)
            df_parameters['grid_weak'] = rand_weak_grid
            df_parameters['grid_power_import'] = grid['grid_power_import']
            df_parameters['grid_power_export'] = grid['grid_power_export']
            grid_ts = grid['grid_ts']
            column_actual_production.append('grid_import')
            column_actual_production.append('grid_export')
            column_actions.append('grid_import')
            column_actions.append('grid_export')
            column_cost.append('grid_import')
            column_cost.append('grid_export')
            df_status['grid_variables'] = [grid_ts.iloc[0,0]]
            grid_co2_ts = self._get_co2_ts() 
            df_status['grid_co2'] = [grid_co2_ts.iloc[0, 0]]

            grid_price_import_ts = grid['grid_price_import']
            grid_price_export_ts = grid['grid_price_export']
            df_status['grid_price_import'] = [grid_price_import_ts.iloc[0, 0]]
            df_status['grid_price_export'] = [grid_price_export_ts.iloc[0, 0]]

        if architecture['genset']==1:
            genset = self._get_genset(rated_power=size['genset'])
            df_parameters['genset_polynom_order'] = len(genset['polynom'])

            for i in range(len(genset['polynom'])):
                df_parameters['genset_polynom_'+str(i)]=genset['polynom'][i]

            df_parameters['genset_rated_power'] = genset['rated_power']
            df_parameters['genset_pmin'] = genset['pmin']
            df_parameters['genset_pmax'] = genset['pmax']
            df_parameters['fuel_cost'] = genset['fuel_cost']
            df_parameters['genset_co2'] = genset['co2']
            column_actual_production.append('genset')
            column_actions.append('genset')
            column_cost.append('genset')
        column_cost.append('total_cost')
        df_actions= {key:[] for key in column_actions}
        df_actual_production = {key:[] for key in column_actual_production}
        df_cost = {key: [] for key in column_cost}

        microgrid_spec={
            'parameters':df_parameters, #Dataframe
            'df_actions':df_actions, #Dict
            'architecture':architecture, #Dictionary
            'df_status':df_status, #Dict
            'df_actual_generation':df_actual_production,#Dict
            'grid_spec':grid_spec, #value = 0
            'df_cost':df_cost, #Dict of 1 value = 0.0
            'df_co2': df_co2,
            'pv':pv, #Dataframe
            'load': load, #Dataframe
            'grid_ts':grid_ts, #Dataframe
            'control_dict': column_actions, #dictionnary
            'grid_price_import' : grid_price_import_ts,
            'grid_price_export' : grid_price_export_ts,
            'grid_co2': grid_co2_ts,
            'storage_suite': self.ss
            # 'li_cap': f'{self.li_battery.cap} Wh',
            # 'flow_cap': f'{self.flow_battery.cap} Wh',
            # 'flywheel_cap': f'{self.flywheel.cap} Wh'
        }
        # print(f'New Grid\nli_cap: {self.li_battery.cap} Wh\nflow_cap: {self.flow_battery.cap} Wh\nflywheel_cap: {self.flywheel.cap} Wh')
        microgrid = Microgrid.Microgrid(microgrid_spec = microgrid_spec)

        return microgrid
    ########################################################
    # PRINT / PLOT FUNCTIONS
    ########################################################

    # function to plot the parameters of all the microgrid generated
    def print_mg_parameters(self, id='all'):
        """ This function is used to print the parameters of all the generated microgrids."""

        if id == 'all':

            if self.microgrids != []:
                parameters = pd.DataFrame()
                for i in range(self.nb_microgrids):
                    parameters = parameters.append(self.microgrids[i].parameters, ignore_index=True)

                pd.options.display.max_columns = None
                display(parameters)

        elif isinstance(id, int) and id < self.nb_microgrids:
            display(self.microgrids[id].parameters)

    def print_all_costs(self):

        #one column ID, one run cost, one rule based, one mpc
        #if train test split, for each train and test
        df_cost = pd.DataFrame()
        for i in range(self.nb_microgrids):

            if self.microgrids[i]._has_train_test_split == False:

                cost_run = self.microgrids[i]._df_record_cost.sum().values
                cost_mpc = np.nan
                cost_rule_based = np.nan

                if self.microgrids[i]._has_run_mpc_baseline == True:
                    cost_mpc = np.around(self.microgrids[i]._baseline_linprog_cost.sum().values[0], 1)

                if self.microgrids[i]._has_run_rule_based_baseline == True:
                    cost_rule_based = np.around(self.microgrids[i]._baseline_priority_list_cost.sum().values[0],1)


            else:
                cost_run = self.microgrids[i]._df_record_cost.sum().values
                cost_mpc = np.nan
                cost_rule_based = np.nan

                if self.microgrids[i]._has_run_mpc_baseline == True:
                    cost_mpc = np.around(self.microgrids[i]._baseline_linprog_cost.iloc[self.microgrids[i]._limit_index:].sum().values[0],1)

                if self.microgrids[i]._has_run_rule_based_baseline == True:
                    cost_rule_based = np.around(self.microgrids[i]._baseline_priority_list_cost.iloc[self.microgrids[i]._limit_index:].sum().values[0],1)

            df_cost =df_cost.append({'ID':i, 'Cost': cost_run, 'Cost (MPC)': cost_mpc, 'Cost (rule-based)':cost_rule_based}, ignore_index=True)

        display(df_cost)