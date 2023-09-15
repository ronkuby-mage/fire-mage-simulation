import os
import json
from copy import deepcopy
from mechanics import get_damage
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pickle

VERSION = 3
_TYPE = 0

def main(config, name, ret_dist=False, sim_size=250, dur_dist=None):
    config["sim_size"] = sim_size
    values = get_damage(config, ret_dist=ret_dist, dur_dist=dur_dist)
    return values

def load_config(cfn):
    config_file = os.path.join("../config/", cfn)
    with open(config_file, 'rt') as fid:
        config = json.load(fid)

    return config

def regress(encounter):
    config = load_config(encounter + ".json")

    sim_size = 10000
    values = main(config, encounter, sim_size=sim_size)
    print(encounter, values)

if __name__ == '__main__':
    for rdx in range(4):
       regress(f"regression{rdx + 1:d}")
    
