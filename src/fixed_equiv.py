import os
import json
from copy import deepcopy
from mechanics import get_damage
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

VERSION = 3

def main(config, name, ret_dist=False):
    sim_size = 25000
    config["sim_size"] = sim_size
    values = get_damage(config, ret_dist=ret_dist)
    print(f"  {name}={values[0]:7.2f}")
    return values

def load_config(cfn):
    config_file = os.path.join("../config/", cfn)
    with open(config_file, 'rt') as fid:
        config = json.load(fid)
    #name = os.path.split(config_file)[-1].split('.')[0]
    #print('starting', name)

    return config
        
def last_player():
    encounter = "loatheb"
    config = load_config(encounter + ".json")
    config["timing"]["delay"] = 3.0
    config["buffs"]["boss"] = "loatheb"
    config["configuration"]["target"] = [config["configuration"]["num_mages"] - 1]
    config = deepcopy(config)
    config['timing']['duration'] = {
            "mean": 160.0,
            "var": 3.0,
            "clip": [0.0, 10000.0]}
    print(config)
    value_0 = main(config, "v0")[0]
    config["stats"]["spell_power"][-1] += 30
    value_sp = main(config, "v_sp")[0]
    config["stats"]["spell_power"][-1] -= 30
    config["stats"]["crit_chance"][-1] += 0.03
    value_cr = main(config, "v_cr")[0]
    print(10.0*(value_cr - value_0)/(value_sp - value_0))
            

if __name__ == '__main__':
    last_player()
    