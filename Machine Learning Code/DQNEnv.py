# Deep Q learning Environment


# -*- coding: utf-8 -*-
"""
Created on Fri Nov 27 12:23:25 2020

@author: vinmue
"""

import numpy as np
import torch
from torch.optim import Adam
from torch.nn import Linear, ReLU, Dropout, BatchNorm1d

class ReplayBuffer(object):
    def __init__(self, state_len, mem_size):
        self.state_len = state_len
        self.mem_size = mem_size
        self.mem_counter = 0
        self.states = np.zeros((mem_size, state_len), dtype=np.float32)
        self.actions = np.zeros(mem_size, dtype=np.int32)
        self.rewards = np.zeros(mem_size, dtype=np.float32)
        self.new_states = np.zeros((mem_size, state_len), dtype=np.float32)
        self.dones = np.zeros(mem_size, dtype=np.int32)


    def store_transition(self, state, action, reward, new_state, done):
        index = self.mem_counter%self.mem_size
        self.states[index, :] = state
        self.actions[index] = action
        self.rewards[index] = reward
        self.new_states[index, :] = new_state
        self.dones[index] = done
        self.mem_counter += 1

    def sample_memory(self, batch_size):
        max_memory = min(self.mem_size, self.mem_counter)
        batch = np.random.choice(np.arange(max_memory), batch_size, replace=False)
        states = self.states[batch, :]
        actions = self.actions[batch]
        rewards = self.rewards[batch]
        new_states = self.new_states[batch, :]
        dones = self.dones[batch]
        return states, actions, rewards, new_states, dones


class DQNetwork(torch.nn.Module):
    def __init__(self, state_len, n_actions,learning_rate):
        super(DQNetwork, self).__init__()
        self.device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
        self.learning_rate = learning_rate
        self.n_actions = n_actions
        self.network = torch.nn.Sequential(
            torch.nn.Linear(state_len, 512),
            torch.nn.Sigmoid(),
            torch.nn.Linear(512, 512),
            torch.nn.Sigmoid(),
            torch.nn.Linear(512, n_actions)
        )
        self.optimizer = Adam(self.parameters(), lr = learning_rate)
        self.loss = torch.nn.MSELoss(reduction='sum')
        self.to(self.device)


    def forward(self,state):
        return self.network(state)


class DQAgent(object):
    def __init__(self, learning_rate, gamma, batch_size, state_len, n_actions, min_memory_for_training,epsilon, epsilon_min, epsilon_dec,mem_size ):
        self.gamma = gamma             # gamma hyperparameter
        self.batch_size = batch_size   # batch size hyperparameter for neural network
        self.state_len = state_len     # how long the state vector is
        self.n_actions = n_actions     # number of actions the agent can take
        self.epsilon = epsilon         # epsilon start value (1=completly random)
        self.epsilon_min = epsilon_min # the minimum value
        self.epsilon_dec = epsilon_dec # the factor by which epsilon will be multiplied by at each timestep
        self.mem_size = mem_size       # the number of timesteps, memory will be allocated for. After that old memory will be overwritten
        #how many timestep the agent must have stored before it learns (to reduce overfitting)
        self.min_memory_for_training = min_memory_for_training 
        ##############
        self.q = DQNetwork(state_len, n_actions, learning_rate)      # the neural network
        self.replay_buffer = ReplayBuffer(self.state_len, mem_size)  # the replay buffer for experience replay
        
    def store_transition(self, state, action, reward, new_state, done):             # stores a timestep in memory
        self.replay_buffer.store_transition(state, action, reward, new_state, done)

    def choose_action(self, state):   #Epsilon greedy action selection
        if np.random.random() < self.epsilon:                                          
            action = np.random.choice(np.arange(self.n_actions))
        else:
            state = torch.tensor([state], dtype = torch.float32).to(self.q.device)        #make state a tensor and add batch dimension
            q= self.q.forward(state)                                                      #forward pass
            action = torch.argmax(q)                                                      #selection action with highest q value
        return int(action)

    def learn(self):
        if self.replay_buffer.mem_counter < self.min_memory_for_training:
            return
        states, actions, rewards, new_states, dones = self.replay_buffer.sample_memory(self.batch_size) #retrieve a batch from memory
        self.q.optimizer.zero_grad()                                                   # clear gradients before forward pass
        states_batch = torch.tensor(states, dtype = torch.float32).to(self.q.device)       # make states_batch to a tensor and send to device
        new_states_batch = torch.tensor(new_states,dtype = torch.float32).to(self.q.device)
        actions_batch = torch.tensor(actions, dtype = torch.long).to(self.q.device)
        rewards_batch = torch.tensor(rewards, dtype = torch.float32).to(self.q.device)
        dones_batch = torch.tensor(dones, dtype = torch.float32).to(self.q.device)

        target = rewards_batch + torch.mul(self.gamma* self.q(new_states_batch).max(axis = 1).values, (1 - dones_batch))  #target value
        prediction = self.q.forward(states_batch).gather(1,actions_batch.unsqueeze(1)).squeeze(1)                         #predicted value

        loss = self.q.loss(prediction, target)
        loss.backward()  # Compute gradients
        self.q.optimizer.step()  # Backpropagate error

        # decrease epsilon:
        self.epsilon = self.epsilon * self.epsilon_dec if self.epsilon *self.epsilon_dec \
                                                          > self.epsilon_min else self.epsilon_min
        return