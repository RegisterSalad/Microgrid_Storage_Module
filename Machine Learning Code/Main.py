import sys
from pymgrid import MicrogridGenerator as mg
import numpy as np
from Storage import StorageSuite
from DQNEnv import DQAgent # Neural Net implimentation module
import pickle as pkl # Neural Network storage and loading
from scipy.optimize import minimize
from scipy.optimize import LinearConstraint
import ast
import operator as op
from IPython.display import display, clear_output
from time import sleep

HOUR = 4 # 15 Min intervals in an hour
DAY = 96 # Number of 15 Min intervals in day
MONTH = 2_924 # Number of 15 Min intervals in month
YEAR =35_088 # Number of 15 Min intervals in year (non-leap)
ZERO = 10**-5 # Low value for zeroes

############
''' the following is a string -> evaluation parser '''
operators = {ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul,
             ast.Div: op.truediv, ast.Pow: op.pow, ast.BitXor: op.xor,
             ast.USub: op.neg}

def eval_expr(expr) -> float :
    if expr != '':
        return eval_(ast.parse(expr, mode='eval').body)
    else:
        return None

def eval_(node) -> float:
    if isinstance(node, ast.Num): # <number>
        return node.n
    elif isinstance(node, ast.BinOp): # <left> <operator> <right>
        return operators[type(node.op)](float(eval_(node.left)), float(eval_(node.right)))
    elif isinstance(node, ast.UnaryOp): # <operator> <operand> e.g., -1
        return operators[type(node.op)](eval_(node.operand))
    else:
        raise TypeError(node)
############

class GridOptimizer:
    ''' This will create the microgrids, train and test a neural network and optimize the scale of the network
        Parameters
        ----------
            - data_path: str, contains path to the storage deivce behavioral data
            - cost_limit: float, desired grid storage device capital cost
            
        Attributes
        ----------
            - self.data_path: str, container for path to the storage deivce behavioral data
            - self.cost_limit: float, container for desired grid storage device capital cost
            - self.ss: StorageSuite object, contains all storage device parameters
            - self.device_cost_list: list, contains list of all device capital costs
            - self.constratint: Scipy LinearContraint object, used for function minimization
            '''
    def __init__(self, data_path: str, cost_limit: float):
        self.data_path = data_path
        self.cost_limit = cost_limit
        self.ss = StorageSuite(filename=self.data_path, load = 600_000) # Create baseline storage suite
        self.li_battery, self.flow_battery, self.flywheel = self.ss.unpack()
        self.device_cost_list = [self.li_battery.capital_cost, self.flow_battery.capital_cost, self.flywheel.capital_cost]
        ### Create initial grid
        self.mg_gen = mg.MicrogridGenerator(storage_suite_list=[self.ss])
        self.mg_gen.generate_microgrid(verbose=False, interpolate=True)
        self.initial_grid_env = self.mg_gen.microgrids[0]

    def inequality_constraint1(self, params):
        L = params[0]
        F = params[1]
        W = params[2]        
        cap_cost_formula = self.ss.get_total_capital_cost_formula().replace("L", str(L/1000)).replace("F", str(F/1000)).replace("W", str(W/1000))
        return self.cost_limit - eval_expr(cap_cost_formula) 
    
    def inequality_constraint2(self, params):
        L = params[0]
        F = params[1]
        W = params[2]        
        cap_cost_formula = self.ss.get_total_capital_cost_formula().replace("L", str(L/1000)).replace("F", str(F/1000)).replace("W", str(W/1000))
        return eval_expr(cap_cost_formula) - (self.cost_limit - 700_000)


    def score_contraint(self, params):
        # L = params[0]
        # F = params[1]
        # W = params[2]
        # cap_cost_formula = self.ss.get_total_capital_cost_formula().replace("L", str(L/1000)).replace("F", str(F/1000)).replace("W", str(W/1000))
        # Create New grid with new values to test #
        self.ss.modify_ss(params)
        new_grid_gen = mg.MicrogridGenerator(storage_suite_list=[self.ss])
        new_grid_gen.generate_microgrid(verbose=False, interpolate=True)
        new_grid_env = new_grid_gen.microgrids[0]
        self.new_score = self.test_grid(env = new_grid_env, horizon=YEAR, load_path=r"C:\Users\thesu\Desktop\Design\Agents\Trained Agent Object.pkl")
        # sys.stdout.write(f'\rNew score: {new_score}, Score percentage: {(new_score/self.initial_score)*100}%\n')#, Score is: {final}')
        # sys.stdout.flush()         
        return self.new_score - (0.95*self.initial_score) # Score must be no less than 95% of initial score
        

    def cap_function(self, params: list):
        L = params[0]
        F = params[1]
        W = params[2]        
        cap_cost_formula = self.ss.get_total_capital_cost_formula().replace("L", str(L/1000)).replace("F", str(F/1000)).replace("W", str(W/1000))
        final = (eval_expr(cap_cost_formula))
        sys.stdout.write(f'\rScore percentage: {(self.new_score/self.initial_score)*100}%, params: {params}')
        sys.stdout.flush()     
        # sys.stdout.write(f'\r{params}')#, Score is: {final}')
        # sys.stdout.flush()                                  
        return final

    def test_func(self):
        return self.ss.get_total_capital_cost_formula()

    def start_minimize(self):
        cons1 = ({"type":"ineq","fun": self.inequality_constraint1})
        cons2 = ({"type":"ineq","fun": self.inequality_constraint2})
        cons3 = ({"type":"ineq","fun": self.score_contraint})
        constraints = [cons1, cons2, cons3]
        self.new_score = 0
        bnds = (0,None)
        with open(r"C:\Users\thesu\Desktop\Design\Agents\Trained Agent Object.pkl", 'rb') as f:  # Loads agent from desired path
            trained_agent = pkl.load(f)
        self.initial_score = self.test_grid(env = self.initial_grid_env, horizon=YEAR, agent = trained_agent)
        print(self.initial_score)
        initial_guess = [self.li_battery.cap, self.flow_battery.cap, self.flywheel.cap]               
        optimized_function = minimize(fun = self.cap_function, x0 = initial_guess, method='trust-constr', constraints=constraints, bounds = (bnds, bnds, bnds))
        return optimized_function

    def train_new_network(self, env: object, n_episodes: int, nb_actions: int, horizon: int, store_path: None) -> object:
        '''Used to train the deep Q-learning model and store a deep Q model
            For path use \\ or r'' to avoid UNICODE errors '''
        env.set_horizon(horizon = horizon) # Sets the Horizon
        agent = DQAgent(learning_rate=0.05, gamma=0.90, batch_size=32, 
                        state_len=len(env.reset()), 
                        n_actions = nb_actions,
                        mem_size = 1000000,
                        min_memory_for_training=1000, epsilon=1, epsilon_dec=0.99,
                        epsilon_min = 0.02)
        #main training loop
        for episode in range(n_episodes):
            state = env.reset()                              
            score = 0                                                                   
            done = 0                                                             
            while not done:                                                                                         
                action_select = agent.choose_action(state)
                action = env.actions_agent(action = action_select) 
                new_state,reward, done, = env.run(action)                             
                score+=reward                                                           
                agent.store_transition(state, action_select, reward, new_state, done)         
                agent.learn()                                                           
                state = new_state                                                       
                value_print=f"\rEpisode: {episode} Progress " + str(round(((env._tracking_timestep)*100)/(env.horizon),1))
                sys.stdout.write(value_print)
                sys.stdout.flush()
        env.reset()

        if store_path == None:
            print("Network Trained. Use store_network to store the network object at a desired path.")
            return agent

        elif type(store_path) == "<class 'str'>":
            with open(store_path, 'wb') as f:  
                pkl.dump(obj=agent, file=f)
            print(f"Agent Trained and Stored at {store_path}")
            return



    def test_grid(self, env: object, horizon: int, agent: object) -> float:
        ''' Manages the grid based on a trained neural net model '''
        env.set_horizon(horizon = horizon) # Sets the Horizon

        # with open(load_path, 'rb') as f:  # Loads agent from desired path
        #     agent = pkl.load(f)

        state = env.reset()                                                       
        score = 0                                                                   
        done = 0

        #main testing loop                                                            
        while not done:                                                                                         
            action_select = agent.choose_action(state)
            action = env.actions_agent(action = action_select) 
            new_state,reward, done, = env.run(action)                             
            score+=reward                                                                                                                   
            state = new_state
            # value_print="\rProgress " + str(round(((env._tracking_timestep)*100)/(env.horizon),1)) +" %"
            # sys.stdout.write(value_print)
            # sys.stdout.flush()                                                       
        env.reset()                                                                    
        return score


