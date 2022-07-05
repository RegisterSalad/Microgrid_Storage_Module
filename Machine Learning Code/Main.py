from sys import stdout
from pymgrid import MicrogridGenerator as mg
import numpy as np
from time import sleep
from Storage import StorageSuite
from DQNEnv import DQAgent # Neural Net implimentation module
import pickle as pkl # Neural Network storage and loading
from scipy.optimize import minimize
from scipy.optimize import LinearConstraint

HOUR = 4 # 15 Min intervals in an hour
DAY = 96 # Number of 15 Min intervals in day
MONTH = 2_924 # Number of 15 Min intervals in month
YEAR =35_088 # Number of 15 Min intervals in year (non-leap)
ZERO = 10**-5 # Low value for zeroes

class GridOptimizer:
    ''' This will create the microgrids, train and test a neural network and optimize the scale of the network'''
    def __init__(self, data_path: str, constraint: float):
        self.st_data_path = data_path
        self.constraint = constraint
        # self.grids = self.create_grids(nb_grid=np.random.randint(1,5))
        self.ss = StorageSuite(filename=self.st_data_path, load = 350_000) # Create baseline storage suite
        self.grid_0_env = mg.MicrogridGenerator(storage_suite_list = [self.ss]) # Base grid that all runs will start with
        self.current_cost = self.ss.get_capital_cost()
        self.score_list = []
        
    # def create_grids(self, nb_grid: int,):
    #     ''' Grid size will range from 100kW to 600kW'''
    #     grid_list = []
    #     for i in range(nb_grid):
    #         grid_list.append(StorageSuite(self.st_data_path, load=np.random.randint(1E5,6E5)))
    #     mg_env = mg.MicrogridGenerator(storage_suite_list=grid_list)
    #     mg_env.generate_microgrid(verbose= False, interpolate= True)
    #     return grid_list
    
    # Run Microgrid through network
    def start(self) -> None:
        statement_0 = "\r Starting function optimization"
        stdout.write(statement_0)
        stdout.flush()     
        self.grid_0_env.generate_microgrid(verbose= False, interpolate= True)
        self.grid = self.grid_0_env.microgrids[0]
        self.li_battery, self.flow_battery, self.flywheel = self.ss.unpack()
        sleep(3)
        print(f"Grid storage capacities are: Litium Ion Storage : {round(self.li_battery.cap,2)} kWh, Ion Flow Battery: {round(self.flow_battery.cap,2)} kWh, Flywheel Storage: {round(self.flywheel.cap,2)} kWh, load is {round(self.ss.load,2)} kW.")
        print(f"Grid total cost: ${round(self.current_cost,2)}, constraint is {round(self.constraint,2)}. Delta is {round(self.current_cost-self.constraint,2)}")
        sleep(3)
        stdout.flush()
        print("Starting score testing\n")
        self.network_path = r"C:\Users\thesu\Desktop\Trained Agent Object.pkl" # Default path for trained network
        self.score_list.append(self.test_network(env = self.grid, horizon=YEAR, load_path = self.network_path)) # Tests the grid using agent at path
        return None



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
                value_print=f"\rEpisode: {episode} Progress " + str(round(((env._tracking_timestep)*100)/(env.horizon),2))
                stdout.write(value_print)
                stdout.flush()
        env.reset()

        if store_path == None:
            print("Network Trained. Use store_network to store the network object at a desired path.")
            return agent

        elif type(store_path) == "<class 'str'>":
            with open(store_path, 'wb') as f:  
                pkl.dump(obj=agent, file=f)
            print(f"Agent Trained and Stored at {store_path}")
            return



    def test_network(self, env: object, horizon: int, load_path: str) -> float:
        ''' Manages the grid based on a trained neural net model '''
        env.set_horizon(horizon = horizon) # Sets the Horizon

        with open(load_path, 'rb') as f:  # Loads agent from desired path
            agent = pkl.load(f)

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
            value_print="\rProgress " + str(round(((env._tracking_timestep)*100)/(env.horizon),2)) +" %"
            stdout.write(value_print)
            stdout.flush()                                                       
        env.reset()                                                                    
        return score


