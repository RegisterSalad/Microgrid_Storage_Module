import csv
import ast
from logging import captureWarnings #Library for parsing formula syntax
import operator as op
from math import e
import re
from unittest.mock import NonCallableMagicMock
import gc
import ctypes
import numpy as np
from IPython import display
############
''' the following is a string -> evaluation parser '''
operators = {ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul,
             ast.Div: op.truediv, ast.Pow: op.pow, ast.BitXor: op.xor,
             ast.USub: op.neg}

def eval_expr(expr):
    if expr != '':
        return eval_(ast.parse(expr, mode='eval').body)
    else:
        return None

def eval_(node):
    if isinstance(node, ast.Num): # <number>
        return node.n
    elif isinstance(node, ast.BinOp): # <left> <operator> <right>
        return operators[type(node.op)](float(eval_(node.left)), float(eval_(node.right)))
    elif isinstance(node, ast.UnaryOp): # <operator> <operand> e.g., -1
        return operators[type(node.op)](eval_(node.operand))
    else:
        raise TypeError(node)

############


class StorageSuite:
    ''' StorageSuite aggregates all Storage objects so that they can be interacted in a straightforward manner
        Each microgrid contains 3 storage objects:
            - Litium Ion Storage (includes vehicle to grid)
            - Vanadium Flow Storage
            - Flywheel Energy Storage
        Each storage object contains the values:
            - type
            - cap
            - max_cont_power
            - max_soc
            - min_soc
            - max_energy
            - min_energy
            - max_peak_power
            - capital_cost
            - marginal_cost
            - resp_time
            - max_peak_time 
    '''
    def __init__(self, filename,load):
        self.device_data = {} # the string data from the CSV file
        self.storage_suite = {} # where the Storage objects are stored (str(name) -> Storage)
        self.tracking_timestep = 0
        with open(filename, newline='', encoding='utf-8-sig') as devices_file: # opens storage data file
            reader = csv.DictReader(devices_file)
            for row in reader:
                self.device_data[row['type']] = row
        # print(self.device_data)
        baseline_capacity_dict ={  'li-ion': round(load/3,2), 
                                    'flywheel': round(load/3,2),
                                    # 'v2g': round(0.25*load,2),
                                    'flow': round(load/3,2) 
                                }
        for device in self.device_data:
            self.storage_suite[device] = Storage(data=self.device_data[device], type=device, cap = float(baseline_capacity_dict[device]))
            self.load = load
        print(self.storage_suite)
        

    def modify_ss(self, param: dict): # 
        ''' Takes in a dict containing new power and capacity values, re-initializes all Storage objects '''
        #print(gc.isenabled())
        for device in param:
            #self.storage_suite[device].modify(param[device])
            del self.storage_suite[device]
            try:
                self.storage_suite[device] = Storage(data=self.device_data[device], type=device, cap=param[device]['cap'], power=param[device]['power'])
            except KeyError:
                self.storage_suite[device] = Storage(data=self.device_data[device], type=device, cap=param[device]['cap'])

        gc.collect()

    def get_capital_cost(self):
        ''' Returns the total capital cost of all storage devices based on capacity'''
        capital_cost : int = 0
        for device in self.storage_suite:
            capital_cost += self.storage_suite[device].capital_cost

        return capital_cost

    def user_modify_storage(self, device, cap) -> None: # 
        ''' Manual way of modifying the ratios of a single storage object '''
        self.storage_suite[device].modify({'cap':cap}) 

    def print_variables(self) -> None: # 
        ''' Prints variables of each Storage object '''
        for device in self.storage_suite:
            self.storage_suite[device].print_variables()

    def print_properties(self) -> None: # 
        ''' Prints static properties of each Storage object '''
        for device in self.storage_suite:
            self.storage_suite[device].print_properties()

    def discharge(self, stor_type, econ_cost = None, energy_requested=None, energy_spent=None):
        ''' attempts to discharge a given device based on the usable amount wanted or the amount to remove from the device '''
        device = self.storage_suite[stor_type]
        device.discharge(econ_cost, energy_requested, energy_spent)
        return energy_requested

    def charge(self, stor_type, econ_cost=None, energy_used=None, energy_stored=None):
        ''' attempts to charge a given device based on the usable amount wanted or the amount to supply to the device '''
        device = self.storage_suite[stor_type]
        device.charge(econ_cost, energy_used, energy_stored)
        return energy_used


    def self_discharge_all(self) -> None:
        ''' self-discharges all devices '''
        for device in self.storage_suite:
            self.storage_suite[device].self_discharge()

    def get_status_variables(self) -> dict:
        ''' Returns values that change within one microgrid ''' 
        variables = {  'li-ion': {}, 
                        'flywheel': {},
                        # 'v2g': {},
                        'flow': {}
                        }
        for device in self.storage_suite:
            self.storage_suite[device].get_state(variables)

        return variables

    def get_properties(self):
        ''' Returns values that stay the same within one microgrid ''' 
        properties = {  'li-ion': {}, 
                        'flywheel': {},
                        # 'v2g': {},
                        'flow': {}
                        }
        for device in self.storage_suite:
            self.storage_suite[device].get_properties(properties)
        return properties

    def get_total_capital_cost(self) -> float:
        cost: float = 0
        properties = self.get_properties()
        for device in self.storage_suite:
            cost = cost + properties[device]['capital_cost']
        return cost

    def unpack(self):
        """ Returns the objects of the different storage types. """
        mg_stats = self.get_properties()
        mg_variables = self.get_status_variables()
        for key in mg_stats:                                    # 
            if key in mg_variables:                             # Merges dicts together for grid ceation
                mg_stats[key].update(mg_variables[key])         #
        
        li_battery = self.storage_suite['li-ion']
        flow_battery = self.storage_suite['flow']
        flywheel = self.storage_suite['flywheel']

        return li_battery, flow_battery, flywheel
        









# StorageSuite
# Inputs:
#   param: a dict(device->dict(parameter->value)) where
#       - the parent dict's keys are each device (str) in data, the value of each is a
#       - dict of parameter (i.e. cap, or power if applicable) to its value

# Wondering if a StorageSuite class is needed or if this can just be implemented within the code.
# I'll have to think about this.
# To avoid excessive RAM usage, might reuse Storage classes between microgrids and just overwrite them
# - could just write their data/parameters to a text file before moving on to the next microgrid

#string.replace(old, new) (immutable) [replace() syntax]

# need to account for some types 

# v2g is going to have to have unit capacity multiplied by number of houses
# probably similar to how PV generation is determined



class Storage:
    def __init__(self, data: dict, type: str, cap=1, power=0): # 100 and 10 placeholder for testing
        
        #fixed
        self.DATA = data # CSV data dictionary
        self.TYPE = type # string representing the type of device
        self.cap = cap # capacity, in kWh
        self.power = power # power
        if self.power == 0:
            self.power = self.cap * eval_expr(str(data['max_cont_discharge'].replace("x", str(self.cap)))) # uses default power to capacity ratio for given type
        """
        self.START_WINDOW = data['start_window'] # start time that device can be used (V2G), in seconds of the day out of 86,400
        self.END_WINDOW = data['end'] # end time that device can be used (V2G), in seconds of the day out of 86,400
        """
        self.MAX_SOC = float(data['max_charge']) # maximum charge as a proportion of capacity
        self.MIN_SOC = float(data['min_charge']) # minimum charge as a proportion of capacity
        self.max_energy = self.cap  # * data['max_charge']  #maximum charge in kWh
        self.min_energy = 0         # * data['min_charge']  #minimum charge in kWh
        #self.MAX_CHARGE_RATE = ss.device_data['max_charge_rate'] * 
        #self.MIN_CHARGE_RATE = ss.device_data['min_charge_rate']
        #self.MAX_CONT_DISCHARGE = ss.device_data['max_cont_discharge'] 
        
        #self.MIN_DISCHARGE = ss.device_data['min_discharge'] * cap

     
        #calculated
        self.FORMULA_PEAK_DISCHARGE = data['max_peak_discharge'].replace("x", "self.cap").replace("y", "self.power")
        self.FORMULA_EFF_CHARGE = data['eff_charge'].replace("x", "self.soc")
        
        # may need to adjust formulae in current CSV to take proportional SOC rather than current_charge
        # would just have to divide each x in the formula by the capacity of the flywheel used for modelling, probably 29kWh
        self.FORMULA_EFF_DISCHARGE = data['eff_discharge'].replace("x", "self.soc").replace("'", "")
        self.FORMULA_SELF_DISCHARGE = data['self_discharge'].replace("x", "self.soc").replace("'", "") # where x is SoC
        self.FORMULA_CAPITAL_COST = data['capital_cost']
        def peak_discharge(self):
            return eval_expr(self.FORMULA_PEAK_DISCHARGE.replace("self.cap", str(self.cap)).replace("self.power", str(self.power))) # assumed 10s peak capability, in kW
        def capital_cost(self): # independent capacity and power capital cost formula
            return eval_expr(self.FORMULA_CAPITAL_COST.replace("x", str(self.cap)).replace("y", str(self.power)).replace("'", ""))
        self.capital_cost = capital_cost(self)
        self.peak_discharge = peak_discharge(self)
        
        self.MARGINAL_COST = data['marginal_cost'] # cost to use device per kWh in/out, in USD
        # self.ramp_speed = ss.device_data['ramp_speed']
        self.resp_time = data['resp_time'] # time it takes for device to realize command, in seconds
        self.soc = 1 # state of charge as a proportion of capacity
        self.soc_cap = self.soc * self.cap # state of charge in kWh
        self.INIT_PEAK_TIME = data['peak_time']
        self.peak_time = self.INIT_PEAK_TIME #how many consecutive seconds the device can still peak for
        self.capa_to_charge = self.cap / self.soc
        self.capa_to_discharge = self.cap * self.soc
        #user/AI-defined
        pass

    def get_self_discharge_rate(self): # self-discharge rate, in SOC/s
        return float(eval_expr(self.FORMULA_SELF_DISCHARGE.replace("self.soc", str(self.soc)).replace("e", str(e))))
        # parsed_expr = ast.parse(self.FORMULA_SELF_DISCHARGE.replace("self.soc", str(self.soc)).replace("e", str(e)))
        # return ast.literal_eval(parsed_expr)
    def eff_charge(self): # charge effiency function
        return eval_expr(self.FORMULA_EFF_CHARGE.replace("self.soc", str(self.soc)).replace("'", ""))

    def eff_discharge(self): # discharge effiency function
        return eval_expr(self.FORMULA_EFF_DISCHARGE.replace("self.soc", str(self.soc)))

    def current_charge(self):
        return self.soc * self.cap
    
    def self_discharge(self):
        delta_soc = self.get_self_discharge_rate()
        if (self.soc - delta_soc) < self.MIN_SOC:
            self.soc = self.MIN_SOC
            delta_soc = 0
            self.soc_cap = self.min_energy
        else:
            self.soc -= delta_soc
            self.soc_cap = self.max_energy * self.soc

        return delta_soc * self.cap #Retunrs the ammount of energy lost to self discharge
    """
    def modify(self, param: dict):
        self.cap = param['cap']
        if 'power' in param:
            self.power = param['power']
        else:
            self.power = self.cap * eval_expr(self.DATA['max_cont_discharge'].replace("x", str(self.cap)))
        self.peak_discharge = eval_expr(self.DATA['max_peak_discharge'].replace("x", str(self.power))) * self.power
        self.max_energy = self.DATA['max_charge'] * self.cap
        self.min_energy = self.DATA['min_charge'] * self.cap
        self.capital_cost = capital_cost()
    """

    def print_properties(self):
        print("**************************\n")
        print("Device: " + self.TYPE)
        for prop in self.DATA:
            print(prop + ": " + self.DATA[prop] + "\n")

    def get_properties(self, properties:dict):
        properties[self.TYPE]['type'] = self.TYPE
        properties[self.TYPE]['capacity'] = self.cap
        properties[self.TYPE]['max_cont_power'] = self.power
        properties[self.TYPE]['max_soc'] = self.MAX_SOC
        properties[self.TYPE]['min_soc'] = self.MIN_SOC
        properties[self.TYPE]['max_energy'] = self.max_energy
        properties[self.TYPE]['min_energy'] = self.min_energy
        properties[self.TYPE]['max_peak_power'] = self.peak_discharge
        properties[self.TYPE]['capital_cost'] = self.capital_cost
        properties[self.TYPE]['marginal_cost'] = self.MARGINAL_COST
        properties[self.TYPE]['resp_time'] = self.resp_time
        properties[self.TYPE]['max_peak_time'] = self.INIT_PEAK_TIME

    def print_variables(self):
        print("**************************\n")
        print("Device: " + self.TYPE + "\n")
        print("Capacity: " + self.cap + "kWh\n")
        print("Power: " + self.power + "kW\n")

    def get_state(self, variables:dict):
        variables[self.TYPE]['soc'] = self.soc
        variables[self.TYPE]['stored_energy'] = self.current_charge()
        variables[self.TYPE]['eff_charge'] = self.eff_charge()
        variables[self.TYPE]['eff_discharge'] = self.eff_discharge()
        variables[self.TYPE]['self_discharge'] = self.get_self_discharge_rate()
        variables[self.TYPE]['peak_time_left'] = self.peak_time

    def charge(self, econ_cost = None, energy_used: float = None, energy_stored: float = None) -> float:
        """ Returns both the energy used by the grid to charge the battery and the amount of energy actually stored by the battery.
            energy_used < energy_stored """
        if energy_stored == None:
            energy_stored = self.eff_charge() * energy_used
        elif energy_used == None:
            energy_used = energy_stored / self.eff_charge()

        #### Error Checking #### 
        if (energy_stored * 3600) > self.power:
            raise ValueError("Tried to charge " + self.TYPE + str(energy_stored) + " kWh at " + str(energy_stored*3600) + " kW when the maximum able to be charged in a second is " + str(self.power/3600) + " kWh at " + str(self.power) + " kW.")
        if (self.soc_cap + energy_stored) > self.cap:
            self.soc = self.MAX_SOC # Charge to full
            energy_used = self.max_energy - self.cap
            energy_stored = energy_used
            # raise ValueError("Tried to charge " + self.TYPE + str(energy_stored) + " kWh when there is already " + str(self.soc_cap - self.min_energy) + " kWh of capacity stored.")
        ########################

        self.soc_cap += energy_stored
        self.soc = self.soc_cap / self.cap
        
        if econ_cost != None:
            econ_cost.cost += self.MARGINAL_COST * energy_used

        return energy_used, energy_stored
       
    def discharge(self, econ_cost = None, energy_requested: float = None, energy_spent: float = None) -> float:
        """ Returns both the energy requested by the grid  and the actual amount pulled by the battery.
            energy_requested < energy_spent """
        if energy_requested == None:
            energy_requested = self.eff_discharge() * energy_spent
        elif energy_spent == None:
            energy_spent = energy_requested / self.eff_discharge()

        ###### Error Checking ######
        if (energy_requested * 3600) > self.power:
            if (energy_requested * 3600) < self.peak_discharge and self.peak_time == 0:
                raise ValueError("Peak time exhausted: Tried to get " + self.TYPE + str(energy_requested) + "kWh at " + str(energy_requested*3600) + "kW when the maximum available this second is continuous power at " + str(self.power/3600) + "kWh at " + str(self.power) + "kW.")
            if (energy_requested * 3600) > self.peak_discharge:
                raise ValueError("Tried to get " + self.TYPE + str(' '+energy_requested) + "kWh at " + str(' '+energy_requested*3600) + "kW when the maximum peak available in a second is " + str(self.power/3600) + "kWh at " + str(self.power) + "kW.")
        if (self.soc_cap - energy_spent) < self.min_energy:
            self.soc = self.MIN_SOC
            energy_spent = self.cap - self.min_energy 
            energy_requested = energy_spent
            # raise ValueError("Tried to discharge " + self.TYPE + str(energy_spent) + "kWh when there was only " + str(self.soc_cap - self.min_energy) + "kWh left.")
        ###########################

        self.soc_cap -= energy_spent
        self.soc = self.soc_cap / self.cap
        if energy_requested > self.power:
            self.peak_time -= 1
        elif self.peak_time != self.INIT_PEAK_TIME:
            self.peak_time += 1
        #should consider making some of this stuff part of Storage - I accidentally started using self instead of device, after all
        if econ_cost != None:
            econ_cost.cost += self.MARGINAL_COST * energy_requested

        return energy_requested, energy_spent


    #print(0x0000024ABF413DC0)
    #print(test_ss.storage_suite['li-ion'])


    #print(test_ss.device_data)
    #print(test_ss.storage_suite['flywheel'].CAPITAL_COST)
    #print(test_ss.device_data['flywheel']['capital_cost'])




#do we need to include response time of aggregator?
#maybe we can have aggegator control as a boolean
#or even separate suites for each?

# NEXT STEPS:
# 1. Check that formulae are normalized rather than correpsonding to specific caps, powers, or other attributes
# 2. Research aggregator response time