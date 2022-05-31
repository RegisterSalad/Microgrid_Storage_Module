# Imports
from ctypes import sizeof
import re
import tensorflow as tf
import keras.api._v2.keras as keras
import numpy as np
import pandas as pd
import CustomMG as cmg

class neural_network:
    def __init__(self,X, y):    
        self.model = tf.keras.Sequential([keras.layers.Dense(units=3, input_shape=[1])])
        self.model.compile(optimizer='sgd', loss='mean_squared_error')
        self.model.fit(X, y, epochs=500)

    def predict(self, cost):
        self.data = pd.DataFrame(self.model.predict([cost]))
        for i in range(0,len(self.data.T)):
            self.data.rename(columns = {i:'action {}'.format(int(i+1))}, inplace = True)
        writer = pd.ExcelWriter('Pandas-Example2.xlsx')
        self.data.to_excel(writer, 'Sheet1', index= True)
        writer.save()
        print(self.data)
    #print(action_names)

