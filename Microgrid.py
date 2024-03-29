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

from typing import List
import pandas as pd
import numpy as np
from copy import copy
import cvxpy as cp
import operator
import sys
# from plotly.offline import init_notebook_mode, iplot
import matplotlib.pyplot as plt
import cufflinks as cf
from IPython.display import display
from IPython import get_ipython
from pymgrid.algos.Control import Benchmarks

# def in_ipynb():
#     try:
#         cfg = get_ipython().config
#         if cfg['IPKernelApp']['parent_appname'] == 'ipython-notebook':
#             return True
#         else:
#             return False
#     except (NameError, AttributeError):
#         return False

# if in_ipynb():
#     init_notebook_mode(connected=False)

np.random.seed(123)

#cf.set_config_file(offline=True, theme='pearl') #commented for now, issues with parallel processes

DEFAULT_HORIZON = 31579200/900 #in seconds
DEFAULT_TIMESTEP = 1 #in seconds
ZERO = 10**-5

'''
The following classes are used to contain the information related to the different components
of the microgrid. Their main use is for easy access in a notebook.
'''

class Genset:
    """
    The class Genset is used to store the information related to the genset in a microgrid. One of the main use for
    this class is for an easy access to information in a notebook using the genset object contained in a microgrid.

    Parameters
    ----------
    param : dataframe
        All the data to initialize the genset.

    Attributes
    ----------
    rated_power: int
        Maximum rater power of the genset.
    p_min: float
        Value representing the minimum operating power of the genset (kW)
    p_max: float
        Value representing the maximum operating power of the genset (kW)
    fuel_cost: float
        Value representing the cost of using the genset in $/kWh.

    Notes
    -----
    Another way to use this information in a notebook is to use /tab/ after /microgrid.genset./ so you can see all the
    genset attributes.

    Examples
    --------
    >>> m_gen=mg.MicrogridGenerator(nb_microgrid=1,path='your_path')
    >>> m_gen.generate_microgrid()
    >>> m_gen.microgrids[0].genset
    You can then add a point and use tab to have suggestion of the different paramaterers
    You can access the maximum power max for example with:
    >>> m_gen.microgrids[0].genset.p_max
    """
    def __init__(self, param):
        self.rated_power = param['genset_rated_power'].values[0]
        self.p_min = param['genset_pmin'].values[0]
        self.p_max = param['genset_pmax'].values[0]
        self.fuel_cost = param['fuel_cost'].values[0]
        self.co2 = param['genset_co2'].values[0]





class Grid:
    """
    The class Grid is used to store the information related to the grid in a microgrid. One of the main use for
    this class is for an easy access to information in a notebook using the grid object contained in a microgrid.

    Parameters
    ----------
    param : dataframe
        All the data to initialize the grid.
    status: int
        Whether the grid is connected or not at the first time step.


    Attributes
    ----------
    power_export: float
        Value representing the maximum export power to the grid (kW)
    power_import: float
        Value representing the maximum import power from the grid (kW)
    price_export: float
        Value representing the cost of exporting to the grid in $/kJ.
    price_import: float
        Value representing the cost of importing to the grid in $/kJ.
    status: int, binary
        Binary value representing whether the grid is connected or not (for example 0 represent a black-out of the
        main grid).

    Notes
    -----
    Another way to use this information in a notebook is to use /tab/ after /microgrid.grid./ so you can see all the
    grid attributes.

    Examples
    --------
    >>> m_gen=mg.MicrogridGenerator(nb_microgrid=1,path='your_path')
    >>> m_gen.generate_microgrid()
    >>> m_gen.microgrids[0].grid
    You can then add a point and use tab to have suggestion of the different paramaterers
    You can access the status of the grid for example with:
    >>> m_gen.microgrids[0].grid.status
    """
    def __init__(self, param, status, price_import, price_export, co2):
        self.power_export = param['grid_power_export'].values[0]
        self.power_import = param['grid_power_import'].values[0]
        self.price_export = price_export #param['grid_price_export'].values[0]
        self.price_import = price_import # param['grid_price_import'].values[0]
        self.status = status
        self.co2 = co2


class Microgrid:

    def __init__(self, microgrid_spec, horizon=DEFAULT_HORIZON, timestep=DEFAULT_TIMESTEP):
        #list of parameters
        #this is a static dataframe: parameters of the microgrid that do not change with time
        self._param_check(microgrid_spec)
        self.parameters = microgrid_spec['parameters']
        self.architecture = microgrid_spec['architecture']
        self.size_load = microgrid_spec['parameters']['load_size']
        #different timeseries
        self._load_ts=microgrid_spec['load']
        self._pv_ts=microgrid_spec['pv']
        self.pv = self._pv_ts.iloc[0,0]
        self.load = self._load_ts.iloc[0, 0]
        self._next_load = self._load_ts.iloc[1,0]
        self._next_pv = self._pv_ts.iloc[1,0]
        if microgrid_spec['architecture']['grid']==1:
            self._grid_status_ts=microgrid_spec['grid_ts'] #time series of outages
            #self.grid_status = self._grid_status_ts.iloc[0, 0]
            self._grid_price_import=microgrid_spec['grid_price_import']
            self._grid_price_export=microgrid_spec['grid_price_export']
            self._grid_co2 = microgrid_spec['grid_co2']
            self._next_grid_status = self._grid_status_ts.iloc[0, 0]
            self._next_grid_price_export = self._grid_price_export.iloc[0, 0]
            self._next_grid_price_import = self._grid_price_import.iloc[0, 0]
            self._next_grid_co2 = self._grid_co2.iloc[0, 0]
        # those dataframe record what is happening at each time step
        # self.current_status = parameters['df_status'] # Used to create record of previous timestep
        self._df_record_control_dict=microgrid_spec['df_actions']
        self._df_record_state = microgrid_spec['df_status']
        self._df_record_actual_production = microgrid_spec['df_actual_generation']
        self._df_record_cost = microgrid_spec['df_cost']
        self._df_record_co2 = microgrid_spec['df_co2']
        self._df_cost_per_epochs = []
        self.horizon = horizon
        self._tracking_timestep = 0
        self._data_length = min(self._load_ts.shape[0], self._pv_ts.shape[0])
        self.done = False
        self._has_run_rule_based_baseline = False
        self._has_run_mpc_baseline = False
        self._has_train_test_split = False
        self._epoch=0
        self._zero = ZERO
        self.control_dict = microgrid_spec['control_dict']
        self._data_set_to_use_default = 'all'
        self._data_set_to_use = 'all'
        self.benchmarks = Benchmarks(self)
        self.ss = microgrid_spec['storage_suite'] # Load Storage class objects
        self.li_ion, self.flow_battery, self.flywheel = self.ss.unpack() # These are all objects
        if self.architecture['genset'] == 1:
            self.genset = Genset(self.parameters)
        if self.architecture['grid'] == 1:
            self.grid = Grid(self.parameters, self._grid_status_ts.iloc[0,0],
                             self._grid_price_import.iloc[0, 0],
                             self._grid_price_export.iloc[0, 0],
                             self._grid_co2.iloc[0, 0])

    def actions_agent(self, action) -> dict:
        '''Accepts action selection as an integer, Returns control dictionary'''
        pv =                            self.pv
        load =                          self.load
        net_load =                      load-pv
        status =                        self.grid.status

        li_ion_charge =                 max(0,min(-net_load,self.li_ion.capa_to_charge ,self.li_ion.power))
        li_ion_discharge =              max(0,min(net_load,self.li_ion.capa_to_discharge,self.li_ion.power))

        flow_charge =                   max(0,min(-net_load,self.flow_battery.capa_to_charge ,self.flow_battery.power))
        flow_discharge =                max(0,min(net_load,self.flow_battery.capa_to_discharge,self.flow_battery.power))

        flywheel_charge=                max(0,min(-net_load,self.flywheel.capa_to_charge ,self.flywheel.power))
        flywheel_discharge =            max(0,min(net_load,self.flywheel.capa_to_discharge,self.flywheel.power))
        
        li_ion_soc =                    abs(self.li_ion.soc)
        flow_soc =                      abs(self.flow_battery.soc)
        flywheel_soc =                  abs(self.flywheel.soc)

        capa_to_genset = self.genset.rated_power * self.genset.p_max
        p_genset = max(0, min(net_load, capa_to_genset))
        
        if action == 0:
            # CHARGE LI-ION
            control_dict = {    'pv_consummed': min(pv,load),
                                'li_charge': min(net_load,li_ion_charge),
                                'li_discharge': 0,
                                'flow_charge': 0,
                                'flow_discharge': 0,
                                'flywheel_charge': 0,
                                'flywheel_discharge': 0,
                                'grid_import': 0,
                                'grid_export': abs(net_load)*status,
                                'genset': 0
                            }
        if action == 1:
            # DISCHARGE LI-ION
            if li_ion_soc == self.li_ion.MIN_SOC:
                control_dict = {    'pv_consummed': min(pv,load),
                                    'li_charge': 0,
                                    'li_discharge': min(net_load,li_ion_discharge),
                                    'flow_charge': 0,
                                    'flow_discharge': 0,
                                    'flywheel_charge': 0,
                                    'flywheel_discharge': 0,
                                    'grid_import': 0,
                                    'grid_export': abs(net_load)*status,
                                    'genset': p_genset
                                }
            else:
                control_dict = {    'pv_consummed': min(pv,load),
                                    'li_charge': 0,
                                    'li_discharge': min(net_load,li_ion_discharge),
                                    'flow_charge': 0,
                                    'flow_discharge': 0,
                                    'flywheel_charge': 0,
                                    'flywheel_discharge': 0,
                                    'grid_import': 0,
                                    'grid_export': abs(net_load)*status,
                                    'genset': 0
                                }
    ######################
        if action == 2:
            # CHARGE FLOW
            control_dict = {    'pv_consummed': min(pv,load),
                                'li_charge': 0,
                                'li_discharge': 0,
                                'flow_charge': min(net_load,flow_charge),
                                'flow_discharge': 0,
                                'flywheel_charge': 0,
                                'flywheel_discharge': 0,
                                'grid_import': 0,
                                'grid_export': abs(net_load)*status,
                                'genset': 0
                            }
        if action == 3:
            # DISCHARGE FLOW
            if flow_soc == self.flow_battery.MIN_SOC:
                control_dict = {    'pv_consummed': min(pv,load),
                                    'li_charge': 0,
                                    'li_discharge': 0,
                                    'flow_charge': 0,
                                    'flow_discharge': min(net_load,flow_discharge),
                                    'flywheel_charge': 0,
                                    'flywheel_discharge': 0,
                                    'grid_import': 0,
                                    'grid_export': abs(net_load)*status,
                                    'genset': p_genset
                                }
            else:
                control_dict = {    'pv_consummed': min(pv,load),
                                    'li_charge': 0,
                                    'li_discharge': 0,
                                    'flow_charge': 0,
                                    'flow_discharge': min(net_load,flow_discharge),
                                    'flywheel_charge': 0,
                                    'flywheel_discharge': 0,
                                    'grid_import': 0,
                                    'grid_export': abs(net_load)*status,
                                    'genset': 0
                                }
    ######################
        if action == 4:
            # CHARGE FLYWHEEL
            control_dict = {    'pv_consummed': min(pv,load),
                                'li_charge': 0,
                                'li_discharge': 0,
                                'flow_charge': 0,
                                'flow_discharge': 0,
                                'flywheel_charge': min(net_load,flywheel_charge),
                                'flywheel_discharge': 0,
                                'grid_import': 0,
                                'grid_export': abs(net_load)*status,
                                'genset': 0
                            }
        if action == 5:
            # DISCHARGE FLYWHEEL
            if flywheel_soc == self.flywheel.MIN_SOC:
                control_dict = {    'pv_consummed': min(pv,load),
                                    'li_charge': 0,
                                    'li_discharge': 0,
                                    'flow_charge': 0,
                                    'flow_discharge': 0,
                                    'flywheel_charge': 0,
                                    'flywheel_discharge': min(net_load,flywheel_discharge),
                                    'grid_import': 0,
                                    'grid_export': abs(net_load)*status,
                                    'genset': p_genset
                                }
            else:
                control_dict = {    'pv_consummed': min(pv,load),
                                    'li_charge': 0,
                                    'li_discharge': 0,
                                    'flow_charge': 0,
                                    'flow_discharge': 0,
                                    'flywheel_charge': 0,
                                    'flywheel_discharge': min(net_load,flywheel_discharge),
                                    'grid_import': 0,
                                    'grid_export': abs(net_load)*status,
                                    'genset': 0
                                }
    ######################
        if action == 6:
            # IMPORT
            control_dict = {    'pv_consummed': min(pv,load),
                                'li_charge': 0,
                                'li_discharge': 0,
                                'flow_charge': 0,
                                'flow_discharge': 0,
                                'flywheel_charge': 0,
                                'flywheel_discharge': 0,
                                'grid_import': abs(net_load)*status,
                                'grid_export': 0,
                                'genset': 0
                            }
                            
        if action == 7:
            # EXPORT
            control_dict = {    'pv_consummed': min(pv,load),
                                'li_charge': 0,
                                'li_discharge': 0,
                                'flow_charge': 0,
                                'flow_discharge': 0,
                                'flywheel_charge': 0,
                                'flywheel_discharge': 0,
                                'grid_import': 0,
                                'grid_export': abs(net_load)*status,
                                'genset': 0
                            }

    ######################
        if action == 8:
            # COMBINED CHARGE IMPORT
            control_dict = {    'pv_consummed': min(pv,load),
                                'li_charge': min(net_load/3,li_ion_charge),
                                'li_discharge': 0,
                                'flow_charge': min(net_load/3,flow_charge),
                                'flow_discharge': 0,
                                'flywheel_charge': min(net_load/3,flywheel_charge),
                                'flywheel_discharge': 0,
                                'grid_import': abs(net_load)*status,
                                'grid_export': 0,
                                'genset': 0
                            }
                            
        if action == 9:
            # COMBINED DISCHARGE EXPORT
            control_dict = {    'pv_consummed': min(pv,load),
                                'li_charge': 0,
                                'li_discharge': min(net_load/3,li_ion_discharge),
                                'flow_charge': 0,
                                'flow_discharge': min(net_load/3.,flow_discharge),
                                'flywheel_charge': 0,
                                'flywheel_discharge': min(net_load/3,flywheel_discharge),
                                'grid_import': 0,
                                'grid_export': abs(net_load)*status,
                                'genset': 0
                            }
            
        return control_dict

    def _param_check(self, parameters):
        """Simple parameter checks"""

        # Check parameters
        if not isinstance(parameters, dict):
            raise TypeError('parameters must be of type dict, is ({})'.format(type(parameters)))


        # Check architecture
        try:
            architecture = parameters['architecture']
        except KeyError:
            print('Dict of parameters does not appear to contain architecture key')
            raise
        if not isinstance(architecture, dict):
            raise TypeError('parameters[\'architecture\'] must be of type dict, is ({})'.format(type(architecture)))

        for key, val in architecture.items():
            if isinstance(val,bool):
                continue
            elif isinstance(val,int) and (val == 0 or val == 1):
                continue
            else:
                raise TypeError('Value ({}) of key ({}) in architecture is of unrecognizable type, '
                                'must be bool or in {{0,1}}, is ({})'.format(val, key, type(val)))

        # Ensure various DataFrames exist and are in fact DataFrames

        keys = ('parameters', 'load', 'pv')

        for key in keys:
            try:
                df = parameters[key]
            except KeyError:
                print('Dict of parameters does not appear to contain {} key'.format(key))
                raise
            if not isinstance(df, pd.DataFrame):
                raise TypeError('parameters[\'{}\'] must be of type pd.DataFrame, is ({})'.format(key, type(df)))



    def set_horizon(self, horizon):
        """Function used to change the horizon of the simulation."""
        self.horizon = horizon

    def set_cost_co2(self, co2_cost):
        """Function used to change the horizon of the simulation."""
        self.parameters['cost_co2'] = co2_cost

    def get_data(self):
        """Function to return the time series used in the microgrid"""
        return self._load_ts, self._pv_ts

    def get_training_testing_data(self):

        if self._has_train_test_split == True:

            return self._limit_index, self._load_train, self._pv_train, self._load_test, self._pv_test

        else:
            print('You have not split the dataset into training and testing sets')

    def get_control_dict(self):
        """ Function that returns the control_dict. """
        return self.control_dict


    def get_parameters(self):
        """ Function that returns the parameters of the microgrid. """
        return self.parameters


    def get_cost(self):
        """ Function that returns the cost associated the operation of the last time step. """
        return self._df_record_cost['total_cost'][-1]

    def get_current_cost(self):
        """ Function that returns the cost associated the operation of the last time step. """
        return self._df_record_cost['total_cost'][0]

    def get_co2(self):
        """ Function that returns the co2 emissions associated to the operation of the last time step. """
        return self._df_record_co2['co2'][-1]

    def get_updated_values(self) -> dict:
        """
        Function that returns microgrid parameters that change with time. Depending on the architecture we have:
            - PV production
            - Load
            - Battery state of charge
            - Battery capacity to charge
            - Battery capacity to discharge
            - Whether the grid is connected or not
            - CO2 intensity of the grid
        """
        mg_data = {}

        for i in self._df_record_state:
            mg_data[i] = self._df_record_state[i][-1]

        return mg_data


    def forecast_all(self):
        """ Function that returns the PV, load and grid_status forecasted values for the next horizon. """
        forecast = {
            'pv': self.forecast_pv(),
            'load': self.forecast_load(),
        }
        if self.architecture['grid'] == 1:
            forecast['grid_status'] = self.forecast_grid_status()
            forecast['grid_import'], forecast['grid_export'] = self.forecast_grid_prices()
            forecast['grid_co2'] = self.forecast_grid_co2()

        return forecast


    def forecast_pv(self):
        """ Function that returns the PV forecasted values for the next horizon. """
        forecast = np.nan
        if self._data_set_to_use == 'training':
            forecast=self._pv_train.iloc[self._tracking_timestep:self._tracking_timestep + self.horizon].values.flatten()

        if self._data_set_to_use == 'testing':
            forecast = self._pv_test.iloc[
                       self._tracking_timestep:self._tracking_timestep + self.horizon].values.flatten()

        if self._data_set_to_use == 'all':
            forecast = self._pv_ts.iloc[self._tracking_timestep:self._tracking_timestep + self.horizon].values.flatten()

        return forecast


    def forecast_load(self):
        """ Function that returns the load forecasted values for the next horizon. """
        forecast = np.nan
        if self._data_set_to_use == 'training':
            forecast = self._load_train.iloc[self._tracking_timestep:self._tracking_timestep + self.horizon].values.flatten()

        if self._data_set_to_use == 'testing':
            forecast = self._load_test.iloc[self._tracking_timestep:self._tracking_timestep + self.horizon].values.flatten()

        if self._data_set_to_use == 'all':
            forecast = self._load_ts.iloc[self._tracking_timestep:self._tracking_timestep + self.horizon].values.flatten()

        return forecast

    def forecast_grid_status(self):
        """ Function that returns the grid_status forecasted values for the next horizon. """
        forecast = np.nan
        if self._data_set_to_use == 'training':
            forecast = self._grid_status_train.iloc[
               self._tracking_timestep:self._tracking_timestep + self.horizon].values.flatten()

        if self._data_set_to_use == 'testing':
            forecast = self._grid_status_test.iloc[
               self._tracking_timestep:self._tracking_timestep + self.horizon].values.flatten()

        if self._data_set_to_use == 'all':
            forecast = self._grid_status_ts.iloc[
               self._tracking_timestep:self._tracking_timestep + self.horizon].values.flatten()

        return forecast

    def forecast_grid_co2(self):
        """ Function that returns the grid_status forecasted values for the next horizon. """
        forecast = np.nan
        if self._data_set_to_use == 'training':
            forecast = self._grid_co2_train.iloc[
                       self._tracking_timestep:self._tracking_timestep + self.horizon].values.flatten()

        if self._data_set_to_use == 'testing':
            forecast = self._grid_co2_test.iloc[
                       self._tracking_timestep:self._tracking_timestep + self.horizon].values.flatten()

        if self._data_set_to_use == 'all':
            forecast = self._grid_co2.iloc[
                       self._tracking_timestep:self._tracking_timestep + self.horizon].values.flatten()

        return forecast

    def forecast_grid_prices(self):
        """ Function that returns the forecasted import and export prices for the next horizon. """
        forecast_import = np.nan
        forecast_export = np.nan
        if self._data_set_to_use == 'training':
            forecast_import = self._grid_price_import_train.iloc[
                       self._tracking_timestep:self._tracking_timestep + self.horizon].values.flatten()
            forecast_export = self._grid_price_export_train.iloc[
                              self._tracking_timestep:self._tracking_timestep + self.horizon].values.flatten()

        if self._data_set_to_use == 'testing':
            forecast_import = self._grid_price_import_test.iloc[
                       self._tracking_timestep:self._tracking_timestep + self.horizon].values.flatten()
            forecast_export = self._grid_price_export_test.iloc[
                       self._tracking_timestep:self._tracking_timestep + self.horizon].values.flatten()

        if self._data_set_to_use == 'all':
            forecast_import = self._grid_price_import.iloc[
                       self._tracking_timestep:self._tracking_timestep + self.horizon].values.flatten()
            forecast_export = self._grid_price_export.iloc[
                       self._tracking_timestep:self._tracking_timestep + self.horizon].values.flatten()

        return forecast_import, forecast_export



    #if return whole pv and load ts, the time can be counted in notebook
    def run(self, control_dict):

        control_dict['load'] = self.load
        control_dict['pv'] = self.pv

        self._df_record_control_dict = self._record_action(control_dict = control_dict, record_status = self._df_record_control_dict)

        self._df_record_actual_production = self._record_production(control_dict, self._df_record_actual_production,self._df_record_state)

        if self.architecture['grid'] == 1:
            self._df_record_co2 = self._record_co2({i:self._df_record_actual_production[i][-1] for i in self._df_record_actual_production},
                                                   self._df_record_co2, self.grid.co2)

            self._df_record_cost = self._record_cost({ i:self._df_record_actual_production[i][-1] for i in self._df_record_actual_production},
                                                               self._df_record_cost, self._df_record_co2, self.grid.price_import, self.grid.price_export)

            self._df_record_state = self._update_status(production_dict={key: value[-1] for key, value in self._df_record_actual_production.items()},
                                                        record_state = self._df_record_state,next_load= self._next_load,next_pv= self._next_pv,
                                                        next_grid = self._next_grid_status, next_price_import= self._next_grid_price_import,
                                                        next_price_export= self._next_grid_price_export, next_co2= self._next_grid_co2)


        else:
            self._df_record_co2 = self._record_co2({ i:self._df_record_actual_production[i][-1] for i in self._df_record_actual_production},
                                                   self._df_record_co2)

            self._df_record_cost = self._record_cost({ i:self._df_record_actual_production[i][-1] for i in self._df_record_actual_production},
                                                     self._df_record_cost, self._df_record_co2)
            self._df_record_state = self._update_status(control_dict,
                                                        self._df_record_state, self._next_load, self._next_pv)

        if self._tracking_timestep == self.horizon or self._tracking_timestep == self._data_length - 1:  
            self.done = True
            return list(self.get_updated_values().values()), self.get_cost()/4_000, self.done

        self._tracking_timestep += 1
        self.update_variables()

        return list(self.get_updated_values().values()), self.get_cost()/4_000, self.done

    def train_test_split(self, train_size=0.67, shuffle = False, cancel=False):
        """
        Function to split our data between a training and testing set.

        Parameters
        ----------
        train_size : float, optional
            Value between 0 and 1 reflecting the percentage of the dataset that should be in the training set.
        shuffle: boolean
            Variable to know if the training and testing sets should be shuffled or in the 'temporal' order
            Not implemented yet for shuffle = True
        cancel: boolean
            Variable indicating if the split needs to be reverted, and the data brought back into one dataset

        Attributes
        ----------
        _limit_index : int
            Index that delimit the training and testing sets in the time series
        load_train : dataframe
            Timeseries of load in training set
        pv_train: dataframe
            Timeseries of PV in training set
        load_test : dataframe
            Timeseries of load in testing set
        pv_test: dataframe
            Timeseries of PV in testing set
        grid_status_train: dataframe
            Timeseries of grid_status in training set
        grid_status_test: dataframe
            Timeseries of grid_status in testing set
        grid_price_import_train: dataframe
            Timeseries of price_import in training set
        grid_price_import_test: dataframe
            Timeseries of price_import in testing set
        grid_price_export_train: dataframe
            Timeseries of price_export in training set
        grid_price_export_test: dataframe
            Timeseries of price_export in testing set

        """

        if self._has_train_test_split ==  False:
            self._limit_index = int(np.ceil(self._data_length*train_size))
            self._load_train = self._load_ts.iloc[:self._limit_index]
            self._pv_train = self._pv_ts.iloc[:self._limit_index]

            self._load_test = self._load_ts.iloc[self._limit_index:]
            self._pv_test = self._pv_ts.iloc[self._limit_index:]

            if self.architecture['grid'] == 1:
                self._grid_status_train = self._grid_status_ts.iloc[:self._limit_index]
                self._grid_status_test = self._grid_status_ts.iloc[self._limit_index:]

                self._grid_price_import_train = self._grid_price_import.iloc[:self._limit_index]
                self._grid_price_import_test = self._grid_price_import.iloc[self._limit_index:]

                self._grid_price_export_train = self._grid_price_export.iloc[:self._limit_index]
                self._grid_price_export_test = self._grid_price_export.iloc[self._limit_index:]

                self._grid_co2_train = self._grid_co2.iloc[:self._limit_index]
                self._grid_co2_test = self._grid_co2.iloc[self._limit_index:]

            self._has_train_test_split = True
            self._data_set_to_use_default = 'training'
            self._data_set_to_use = 'training'

        elif self._has_train_test_split ==  True and cancel == True:
            self._has_train_test_split = False
            self._data_set_to_use_default = 'all'
            self._data_set_to_use = 'all'

        self.reset()

    def update_variables(self):
        """ Function that updates the variablers containing the parameters of the microgrid changing with time. """
        if self._data_set_to_use == 'training':
            self.pv = self._pv_train.iloc[self._tracking_timestep, 0]
            self.load = self._load_train.iloc[self._tracking_timestep, 0]

            self._next_pv = self._pv_train.iloc[self._tracking_timestep +1, 0]
            self._next_load = self._load_train.iloc[self._tracking_timestep+1, 0]


        if self._data_set_to_use == 'testing':
            self.pv = self._pv_test.iloc[self._tracking_timestep, 0]
            self.load = self._load_test.iloc[self._tracking_timestep, 0]

            self._next_pv = self._pv_test.iloc[self._tracking_timestep+1, 0]
            self._next_load = self._load_test.iloc[self._tracking_timestep+1, 0]

        if self._data_set_to_use == 'all':
            self.pv = self._pv_ts.iloc[self._tracking_timestep, 0]
            self.load = self._load_ts.iloc[self._tracking_timestep, 0]


            if self._tracking_timestep < self._data_length - 1:
                self._next_pv = self._pv_ts.iloc[self._tracking_timestep+1, 0]
                self._next_load = self._load_ts.iloc[self._tracking_timestep+1, 0]
            else:
                self._next_pv, self._next_load = None, None


        if self.architecture['grid']==1:
            if self._data_set_to_use == 'training':
                self.grid.status = self._grid_status_train.iloc[self._tracking_timestep, 0]
                self.grid.price_import = self._grid_price_import_train.iloc[self._tracking_timestep,0]
                self.grid.price_export = self._grid_price_export_train.iloc[self._tracking_timestep,0]
                self.grid.co2 = self._grid_co2_train.iloc[self._tracking_timestep, 0]

                self._next_grid_status = self._grid_status_train.iloc[self._tracking_timestep +1, 0]
                self._next_grid_price_import = self._grid_price_import_train.iloc[self._tracking_timestep +1, 0]
                self._next_grid_price_export = self._grid_price_export_train.iloc[self._tracking_timestep +1, 0]
                self._next_grid_co2 = self._grid_co2_train.iloc[self._tracking_timestep + 1, 0]

            if self._data_set_to_use == 'testing':
                self.grid.status = self._grid_status_test.iloc[self._tracking_timestep, 0]
                self.grid.price_import = self._grid_price_import_test.iloc[self._tracking_timestep, 0]
                self.grid.price_export = self._grid_price_export_test.iloc[self._tracking_timestep, 0]
                self.grid.co2 = self._grid_co2_test.iloc[self._tracking_timestep, 0]

                self._next_grid_status = self._grid_status_test.iloc[self._tracking_timestep + 1, 0]
                self._next_grid_price_import = self._grid_price_import_test.iloc[self._tracking_timestep + 1, 0]
                self._next_grid_price_export = self._grid_price_export_test.iloc[self._tracking_timestep + 1, 0]
                self._next_grid_co2 = self._grid_co2_test.iloc[self._tracking_timestep + 1, 0]


            if self._data_set_to_use == 'all':
                self.grid.status = self._grid_status_ts.iloc[self._tracking_timestep, 0]
                self.grid.price_import = self._grid_price_import.iloc[self._tracking_timestep, 0]
                self.grid.price_export = self._grid_price_export.iloc[self._tracking_timestep, 0]
                self.grid.co2 = self._grid_co2.iloc[self._tracking_timestep, 0]

                if self._tracking_timestep < self._data_length - 1:
                    self._next_grid_status = self._grid_status_ts.iloc[self._tracking_timestep + 1, 0]
                    self._next_grid_price_import = self._grid_price_import.iloc[self._tracking_timestep + 1, 0]
                    self._next_grid_price_export = self._grid_price_export.iloc[self._tracking_timestep + 1, 0]
                    self._next_grid_co2 = self._grid_co2.iloc[self._tracking_timestep + 1, 0]
                else:
                    self._next_grid_status, self._next_grid_price_import, self._next_grid_price_export, \
                    self._next_grid_co2 = None, None, None, None



    def reset(self, testing=False) -> list:
        """This function is used to reset the dataframes that track what is happening in simulation. Mainly used in RL."""
        if self._data_set_to_use == 'training':
            temp_cost = copy(self._df_record_cost)
            temp_cost['epoch'] = self._epoch
            self._df_cost_per_epochs.append(temp_cost)

        self._df_record_control_dict = {i:[] for i in self._df_record_control_dict}
        self._df_record_state = {i:[self._df_record_state[i][0]] for i in self._df_record_state}
        self._df_record_actual_production = {i:[] for i in self._df_record_actual_production}
        self._df_record_cost = {i:[] for i in self._df_record_cost}
        self._df_record_co2 = {i:[] for i in self._df_record_co2}

        self._tracking_timestep = 0

        if testing == True and self._data_set_to_use_default == 'training':
            self._data_set_to_use = 'testing'
            self._data_length = min(self._load_test.shape[0], self._pv_test.shape[0])
        else:
            self._data_set_to_use = self._data_set_to_use_default
            if self._data_set_to_use == 'training':
                self._data_length = min(self._load_train.shape[0], self._pv_train.shape[0])
            else:
                self._data_length = min(self._load_ts.shape[0], self._pv_ts.shape[0])
        self.li_ion.soc == self.li_ion.MAX_SOC
        self.flow_battery.soc == self.flow_battery.MAX_SOC
        self.flywheel.soc == self.flywheel.MAX_SOC
        self.update_variables()
        self.done = False
        self._epoch+=1
        return list(self.get_updated_values().values())

    ########################################################
    # FUNCTIONS TO UPDATE THE INTERNAL DICTIONARIES
    ########################################################


    def _record_action(self, control_dict, record_status):
        """ This function is used to record the actions taken, before being checked for feasability. """
        if not isinstance(record_status, dict):
            raise TypeError('We know this should be named differently but df needs to be dict, is {}'.format(type(record_status)))
        for j in record_status:
            if j in control_dict.keys():
                record_status[j].append(control_dict[j])
            else:
                record_status[j].append({j:0})
        #df = df.append(control_dict,ignore_index=True)

        return record_status


    def _update_status(self, production_dict, record_state: dict, next_load, next_pv, next_grid = 0, next_price_import =0, next_price_export = 0, next_co2 = 0):
        """ This function update the parameters of the microgrid that change with time. """
        #self.df_status = self.df_status.append(self.new_row, ignore_index=True)

        if not isinstance(record_state, dict):
            raise TypeError('We know this should be named differently but df needs to be dict, is {}'.format(type(record_state)))

        new_dict = {
            'load': next_load,
                    'pv': next_pv,
            'hour':self._tracking_timestep%4,
        }

        new_dict['li_ion_soc'] = self.li_ion.soc
        new_dict['li_ion_capa_to_charge'] = self.li_ion.capa_to_charge
        new_dict['li_ion_capa_to_discharge'] = self.li_ion.capa_to_discharge
        new_dict['flow_soc'] = self.flow_battery.soc
        new_dict['flow_capa_to_charge'] = self.flow_battery.capa_to_charge
        new_dict['flow_capa_to_discharge'] = self.flow_battery.capa_to_discharge
        new_dict['flywheel_soc'] = self.flywheel.soc
        new_dict['flywheel_capa_to_charge'] = self.flywheel.capa_to_charge
        new_dict['flywheel_capa_to_discharge'] = self.flywheel.capa_to_discharge

        if self.architecture['grid'] == 1 :
            new_dict['grid_status'] = next_grid
            new_dict['grid_price_import'] = (0.11/4_000)*production_dict['grid_import']
            new_dict['grid_price_export'] = (0.05/4_000)*production_dict['grid_export']
            new_dict['grid_co2'] = next_co2

        
        for j in record_state:
            if j in new_dict.keys():
                record_state[j].append(new_dict[j])

        return record_state


    #now we consider all the generators on all the time (mainly concern genset)

    def _check_constraints_genset(self, p_genset):
        """ This function checks that the constraints of the genset are respected."""
        if p_genset < 0:
            p_genset =0
            print('error, genset power cannot be lower than 0')

        if p_genset < self.parameters['genset_rated_power'].values[0] * self.parameters['genset_pmin'].values[0] and p_genset >1:
            p_genset = self.parameters['genset_rated_power'].values[0] * self.parameters['genset_pmin'].values[0]

        if p_genset > self.parameters['genset_rated_power'].values[0] * self.parameters['genset_pmax'].values[0]:
            p_genset = self.parameters['genset_rated_power'].values[0] * self.parameters['genset_pmax'].values[0]

        return p_genset

    def _check_constraints_grid(self, p_import, p_export):
        """ This function checks that the constraints of the grid are respected."""
        if p_import < 0:
            p_import = 0

        if p_export <0:
            p_export = 0

        if p_import > self._zero and p_export > self._zero:
            pass
        if p_import > self.parameters['grid_power_import'].values[0]:
            p_import = self.parameters['grid_power_import'].values[0]

        if p_export > self.parameters['grid_power_export'].values[0]:
            p_export = self.parameters['grid_power_export'].values[0]

        return p_import, p_export

    def _change_storage_charge(self, power_sent: float, power_requested: float, device: str) -> float:
        """ This function checks that the constraints of the battery are respected."""

        if power_sent < 0:
            power_sent = 0
            # print('wHAT')

        if power_requested < 0:
            power_requested = 0
        
        if power_requested > 0 and power_sent > 0: # Error Raising 
            raise ValueError("Cannot charge and discharge in the same timestep. Check your actions for conflicts")

        if power_sent > 0:
            power_sent, power_stored = self.ss.charge(stor_type = device ,power_used = power_sent)
            power_pulled, power_requested = (0,0)
        if power_requested > 0:
            power_requested, power_pulled = self.ss.discharge(stor_type = device, power_requested = power_requested)
            power_stored, power_sent = (0,0)
        if (power_requested, power_sent) == (0,0):
            return 0,0,0,0

        return  power_stored, power_pulled, power_sent, power_requested

        

    def _record_production(self, control_dict, production_dict, status):
        """
        This function records the actual production occuring in the microgrid. Based on the control actions and the
        parameters of the microgrid. This function will check that the control actions respect the constraints of
        the microgrid and then record what generators have produced energy.

        Parameters
        ----------
        control_dict : dictionnary
            Dictionnary representing the control actions taken by an algorithm (either benchmark or in the run function).
        df: dataframe
            Previous version of the record_production dataframe (coming from the run loop, or benchmarks).
        status: dataframe
            One line dataframe representing the changing parameters of the microgrid.

        Notes
        -----
        The mechanism to incure a penalty in case of over-generation is not yet in its final version.
        """
        assert isinstance(production_dict, dict)
        try:
            control_dict.pop('pv_consummed')
        except KeyError:
            pass


        has_grid = self.architecture['grid'] == 1
        has_genset = self.architecture['genset'] == 1

        sources = 0.0
        sinks = control_dict['load']

        li_charge, li_discharge, li_used, li_requested = self._change_storage_charge(power_sent = control_dict['li_charge'], 
                                                                                        power_requested = control_dict['li_discharge'],
                                                                                        device='li-ion')
        production_dict['li_ion_charge'].append(li_charge)
        production_dict['li_ion_discharge'].append(li_discharge)#+li_self_discharge)
        
        sources += li_requested
        sinks += li_used

        # flow battery
        flow_charge, flow_discharge, flow_used, flow_requested = self._change_storage_charge(power_sent = control_dict['flow_charge'], 
                                                                                                power_requested = control_dict['flow_discharge'], 
                                                                                                device='flow')
        production_dict['flow_charge'].append(flow_charge)
        production_dict['flow_discharge'].append(flow_discharge)#+flow_self_discharge)
        
        sources += flow_requested # Self discharge is not accounted for in sources
        sinks += flow_used

        # flywheel energy storage
        flywheel_charge, flywheel_discharge, flywheel_used, flywheel_requested = self._change_storage_charge(power_sent = control_dict['flywheel_charge'], 
                                                                                                                power_requested = control_dict['flywheel_discharge'], 
                                                                                                                device='flywheel')
        production_dict['flywheel_charge'].append(flywheel_charge)
        production_dict['flywheel_discharge'].append(flywheel_discharge)#+flywheel_self_discharge)
        
        sources += flywheel_requested 
        sinks += flywheel_used

        

        if has_grid:
            p_import, p_export = self._check_constraints_grid(control_dict['grid_import'],
                                                                    control_dict['grid_export'])
            production_dict['grid_import'].append(p_import)
            production_dict['grid_export'].append(p_export)

            sources += p_import
            sinks += p_export

        if has_genset:
            p_genset = self._check_constraints_genset(control_dict['genset'])
            production_dict['genset'].append(p_genset)
            sources += p_genset

        pv_required = sinks-sources
        pv_available = control_dict['pv']

        if np.abs(pv_required-pv_available) < 1e-3:         # meeting demand
            pv_consumed = pv_available
            loss_load = 0
            pv_curtailed = 0
            overgeneration = 0

        elif pv_required > pv_available:                    # loss load
            pv_consumed = pv_available
            loss_load = pv_required-pv_available
            pv_curtailed = 0
            overgeneration = 0

        elif 0 < pv_required < pv_available:                # curtail pv
            pv_consumed = pv_required
            loss_load = 0
            pv_curtailed = pv_available-pv_required
            overgeneration = 0

        else:                                               # overgeneration. Requires NO pv whatsoever
            assert pv_required < 0
            pv_consumed = 0
            loss_load = 0
            pv_curtailed = pv_available if pv_available > 0 else 0
            overgeneration = -pv_required

        production_dict['pv_consummed'].append(pv_consumed)
        production_dict['loss_load'].append(loss_load)
        production_dict['pv_curtailed'].append(pv_curtailed)
        production_dict['overgeneration'].append(overgeneration/4_000)
        

        return production_dict

    def _record_co2(self, control_dict, df, grid_co2=0):
        """ This function record the cost of operating the microgrid at each time step."""
        co2 = 0

        if self.architecture['genset'] == 1:
            co2 += control_dict['genset'] * self.parameters['genset_co2'].values[0]

        if self.architecture['grid'] == 1:
            co2 += grid_co2 * control_dict['grid_import']

        cost_dict = {'co2': co2}

        df['co2'].append( co2)

        return df

    def _record_cost(self, control_dict, cost_dict, df_co2, cost_import=0, cost_export=0):
        """ This function record the cost of operating the microgrid at each time step."""

        if not isinstance(cost_dict, dict):
            raise TypeError('We know this should be named differently but cost_dict needs to be dict, is {}'.format(type(cost_dict)))

        cost_loss_load = control_dict['loss_load'] * self.parameters['cost_loss_load'].values[0]
        cost_overgeneration = control_dict['overgeneration'] * self.parameters['cost_overgeneration'].values[0]

        cost_dict['loss_load'].append(cost_loss_load)
        cost_dict['overgeneration'].append(cost_overgeneration)

        # cost += control_dict['loss_load'] * self.parameters['cost_loss_load'].values[0]
        # cost += control_dict['overgeneration'] * self.parameters['cost_overgeneration'].values[0]

        if self.architecture['genset'] == 1:
            genset_cost = control_dict['genset'] * self.parameters['fuel_cost'].values[0]
            cost_dict['genset'].append(genset_cost)

        if self.architecture['grid'] ==1:
            grid_import_cost = cost_import * control_dict['grid_import']
            grid_export_cost = - cost_export * control_dict['grid_export']
            cost_dict['grid_import'].append(grid_import_cost)
            cost_dict['grid_export'].append(grid_export_cost)

        
        # li_cost = (control_dict['li_charge']+control_dict['li_discharge'])*self.parameters['battery_cost_cycle'].values[0]
        # cost_dict['battery'].append(li_cost)

        co2_cost = self.parameters['cost_co2'].values[0] * df_co2['co2'][-1]
        cost_dict['co2'].append(co2_cost)

        total_cost = np.sum([val[-1] for key, val in cost_dict.items() if key != 'total_cost'])
        cost_dict['total_cost'].append(total_cost)

        return cost_dict
        
    ########################################################
    # RL UTILITY FUNCTIONS
    ########################################################
    #todo add a forecasting function that add noise to the time series
    #todo forecasting function can be used for both mpc benchmart and rl loop


    #todo verbose
    def penalty(self, coef = 1):
        """Penalty that represents discrepancies between control dict and what really happens. """
        penalty = 0
        for i in self._df_record_control_dict:
            penalty += abs(self._df_record_control_dict[i][-1] - self._df_record_actual_production[i][-1])

        return penalty*coef
