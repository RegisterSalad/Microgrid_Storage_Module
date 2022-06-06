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
            self.storage_suite[device] = Storage(type=device)

#string.replace(old, new) (immutable)

class Storage:
    def __init__(self, ss, type, cap, power, s_wind, e_wind):
        #fixed
        self.TYPE = type
        self.CAP = cap
        self.POWER = power
        self.s_wind = s_wind
        self.e_wind = e_wind
        if ss.device_data['cap_power_ind']:
            pass
        else:
            self.capital_cost = ss.device_data['capital_cost'] * self.power
        self.MAX_SOC = ss.device_data['max_charge']
        self.MIN_SOC = ss.device_data['min_charge']
        self.MAX_CHARGE_RATE = ss.device_data['max_charge_rate']
        self.MIN_CHARGE_RATE = ss.device_data['min_charge_rate']
        self.MAX_CONT_DISCHARGE = ss.device_data['max_cont_discharge']
        
        self.MIN_DISCHARGE = ss.device_data['min_discharge']

     
        #calculated
        self.peak_discharge = ss.device_data['max_peak_discharge'] * self.MAX_CONT_DISCHARGE
        self.FORMULA_EFF_CHARGE = ss.device_data['eff_charge'].replace("x", "self.soc")
        def eff_charge():
            return eval_expr(self.FORMULA_EFF_CHARGE.replace("self.soc", str(self.soc)))
        # may need to adjust formulae in current CSV to take proportional SOC rather than current_charge
        # would just have to divide each x in the formula by the capacity of the flywheel used for modelling, probably 29kWh
        self.FORMULA_EFF_DISCHARGE = ss.device_data['eff_discharge'].replace("x", "self.soc")
        def eff_discharge():
            return eval_expr(self.FORMULA_EFF_DISCHARGE.replace("self.soc", str(self.soc)))
        
        self.FORMULA_SELF_DISCHARGE = ss.device_data['self_discharge'].replace("x", "self.soc")
        def self_discharge():
            return eval_expr(self.FORMULA_SELF_DISCHARGE.replace("self.soc", str(self.soc)))

        self.FORMULA_CAPITAL_COST = ss.device_data['capital_cost']
        def capital_cost():
            return eval_expr(self.FORMULA_CAPITAL_COST.replace("X", str(self.CAP)).replace("Y", str(self.POWER))) * self.CAP

            
        self.marginal_cost = ss.device_data['marginal_cost']
        self.ramp_speed = ss.device_data['ramp_speed']
        self.resp_time = ss.device_data['resp_time']
        self.soc = 0
        self.current_charge = self.soc * self.CAP

        #user/AI-defined
        pass
    

if __name__ == "__main__":
    test_ss = StorageSuite('energy_storage_devices_v2.csv')
    print(test_ss.device_data['flywheel']['capital_cost'])



#do we need to include response time of aggregator?
#maybe we can have aggegator control as a boolean
#or even separate suites for each?

# NEXT STEPS:
# 1. Decide whether to convert each value to flat numbers or keep as proportions
# 2. Normalize formulae that were based on a specific unit (i.e. cap of 29kWh)
