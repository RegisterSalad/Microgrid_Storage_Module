import sys
from pymgrid import MicrogridGenerator as mg
import matplotlib.pyplot as plt
import numpy as np
import os
import time
from IPython.display import display,clear_output
import pandas as pd
from Storage import StorageSuite as st
from pathlib import Path
from math import e
from time import sleep
from DQNEnv import DQAgent
import pickle as pkl
import random

HOUR = 4 # 15 Min intervals in an hour
DAY = 96 # Number of 15 Min intervals in day
MONTH = 2_924 # Number of 15 Min intervals in month
YEAR =35_088 # Number of 15 Min intervals in year (non-leap)
ZERO = 10**-5