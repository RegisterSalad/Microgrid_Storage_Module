import sys
from Storage import StorageSuite
import numpy as np
from scipy.optimize import minimize
from scipy.optimize import LinearConstraint
import MicrogridGenerator as mg
import Microgrid


storage_data_argument = sys.argv[1]
capital_cost_limit_argument = sys.argv[2]
master_storage_suite = Storage.StorageSuite(storage_data_argument)
device_capital_costs = master_storage_suite.get_device_capital_costs()
dcc = device_capital_costs
linear_constraint = LinearConstraint(dcc, 0, capital_cost_limit_argument)

def microgrid_start(storage_suite_param):
    master_storage_suite.modify_ss(storage_suite_param)
    m_gen = mg.MicrogridGenerator(master_storage_suite)
    m_gen.generate_microgrid()
    m_gen.microgrids[0].train_test_split()
    return m_gen.microgrids[0].econ_cost



x0 = numpy.zeros((len(dcc), len(dcc)))
res = minimize(microgrid_start, x0, 'trust-constr', constraints=linear_constraint)

"""
Framework:
1. user command (data filepaths + capital limit)
2. initialize StorageSuite
3. get device capital costs and initialize capital constraint
4. define microgrid run function that returns economic cost
5. initialize input variables as zero array
6. run optimization function
7. format and print results (the optimized inputs representing power and capacity for each storage device)
"""
