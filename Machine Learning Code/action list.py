import numpy as np
import math
import random as r
import pandas as pd
from NN import neural_network
# filepath = 
x = np.array([-1.0, 0.0, 1.0, 2.0, 3.0, 4.0], dtype=float)
Y = np.array([-10.0, -7.0, -4.0, -1.0, 2.0, 5.0], dtype=float)
NN_1 = neural_network(X = x, y = Y)
NN_1.predict(cost = 25)

#NN_1.predict(NN_1,cost = 25, X = x, y = Y)

def action_1():
    #Change the production capacity of genset
    
    pass

def action_2():
    #Change the production capacity of PV

    pass

def action_3():
    #Change the storage capacity of Flow
    pass

def action_4():
    #Change the storage capacity of Lithium Ion batteries
    pass

def action_5():
    #Change storage capacity of flywheel storage
    pass

