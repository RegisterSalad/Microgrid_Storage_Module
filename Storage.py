import csv
import ast #Library for syntax parsing
import operator as op

# supported operators
operators = {ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul,
             ast.Div: op.truediv, ast.Pow: op.pow, ast.BitXor: op.xor,
             ast.USub: op.neg}

def eval_expr(expr):
    """
    eval_expr('2^6')
    4
    eval_expr('2**6')
    64
    eval_expr('1 + 2*3**(4^5) / (6 + -7)')
    -5.0
    """
    return eval_(ast.parse(expr, mode='eval').body)

def eval_(node):
    if isinstance(node, ast.Num): # <number>
        return node.n
    elif isinstance(node, ast.BinOp): # <left> <operator> <right>
        return operators[type(node.op)](eval_(node.left), eval_(node.right))
    elif isinstance(node, ast.UnaryOp): # <operator> <operand> e.g., -1
        return operators[type(node.op)](eval_(node.operand))
    else:
        raise TypeError(node)

class StorageSuite:
    def __init__(self, filename):
        self.storage_suite = []
        self.device_data = {}
        with open(filename, newline='', encoding='utf-8-sig') as devices_file:
            reader = csv.DictReader(devices_file)
            for row in reader:
                self.device_data[row['type']] = row
        for device in self.device_data:
            self.storage_suite[device] = Storage(ss=self, type=device)

#string.replace(old, new) (immutable) [replace() syntax]

# need to account for some types 

# v2g is going to have to have unit capacity multiplied by number of houses
# probably similar to how PV generation is determined



class Storage:
    def __init__(self, ss: StorageSuite, type: str, cap: float, power: float, start_window: int, end_window: int):
        #fixed
        self.TYPE = type
        self.CAP = cap # in kWh
        self.POWER = power # in kW
        if self.POWER == None:
            self.POWER = cap * ss.device_data['max_cont_discharge'] # uses default power to capacity ratio for given type
        self.START_WINDOW = start_window # start time that device can be used (V2G), in seconds of the day out of 86,400
        self.END_WINDOW = end_window # end time that device can be used (V2G), in seconds of the day out of 86,400
        if bool(ss.device_data['cap_power_ind']):
            self.CAPITAL_COST = capital_cost() # if capital cost is a function of both power and capacity, in USD
        else:
            self.CAPITAL_COST = ss.device_data['capital_cost'] * cap # if capital cost is primarily a function of capacity only, in USD
        self.MAX_SOC = ss.device_data['max_charge'] # maximum charge as a proportion of capacity
        self.MIN_SOC = ss.device_data['min_charge'] # minimum charge as a proportion of capacity
        self.MAX_SOC_CAP = ss.device_data['max_charge'] * cap # maximum charge in kWh
        self.MIN_SOC_CAP = ss.device_data['min_charge'] * cap # minimum charge in kWh
        #self.MAX_CHARGE_RATE = ss.device_data['max_charge_rate'] * 
        #self.MIN_CHARGE_RATE = ss.device_data['min_charge_rate']
        #self.MAX_CONT_DISCHARGE = ss.device_data['max_cont_discharge'] 
        
        #self.MIN_DISCHARGE = ss.device_data['min_discharge'] * cap

     
        #calculated
        self.PEAK_DISCHARGE = ss.device_data['max_peak_discharge'] * self.POWER # assumed 10s peak capability, in kW
        self.FORMULA_EFF_CHARGE = ss.device_data['eff_charge'].replace("x", "self.soc")
        def eff_charge(): # charge effiency function
            return eval_expr(self.FORMULA_EFF_CHARGE.replace("self.soc", str(self.soc))).replace("'", "")
        # may need to adjust formulae in current CSV to take proportional SOC rather than current_charge
        # would just have to divide each x in the formula by the capacity of the flywheel used for modelling, probably 29kWh
        self.FORMULA_EFF_DISCHARGE = ss.device_data['eff_discharge'].replace("x", "self.soc").replace("'", "")
        def eff_discharge(): # discharge effiency function
            return eval_expr(self.FORMULA_EFF_DISCHARGE.replace("self.soc", str(self.soc)))
        
        self.FORMULA_SELF_DISCHARGE = ss.device_data['self_discharge'].replace("x", "self.soc").replace("'", "")
        def self_discharge(): # self-discharge rate, in kW
            return eval_expr(self.FORMULA_SELF_DISCHARGE.replace("self.soc", str(self.soc)))

        self.FORMULA_CAPITAL_COST = ss.device_data['capital_cost']
        def capital_cost(): # independent capacity and power capital cost formula
            return eval_expr(self.FORMULA_CAPITAL_COST.replace("X", str(self.CAP)).replace("Y", str(self.POWER)).replace("'", "")) * self.CAP

            
        self.MARGINAL_COST = ss.device_data['marginal_cost'] # cost to use device per kW in/out, in USD
        #self.ramp_speed = ss.device_data['ramp_speed']
        self.resp_time = ss.device_data['resp_time'] # time it takes for device to realize command, in seconds
        self.soc = 0 # state of charge as a proportion of capacity
        self.soc_cap = 0 # state of charge in kWh
        def current_charge():
            return self.soc * self.CAP

        #user/AI-defined
        pass
    

if __name__ == "__main__":
    test_ss = StorageSuite('energy_storage_devices_v2.csv')
    print(test_ss.device_data['flywheel']['capital_cost'])



#do we need to include response time of aggregator?
#maybe we can have aggegator control as a boolean
#or even separate suites for each?

# NEXT STEPS:
# 1. Normalize formulae that were based on a specific unit (i.e. cap of 29kWh)
# 2. Research aggregator response time
# 3. Test formulae
# 4. Test initialization of StorageSuite
