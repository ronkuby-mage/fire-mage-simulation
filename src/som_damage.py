import os
import json
from copy import deepcopy
from mechanics import get_damage
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

VERSION = 3

def main(config, name, ret_dist=False, sim_size=250):
    config["sim_size"] = sim_size
    values = get_damage(config, ret_dist=ret_dist)
    print(f"  {name}={values[0]:6.1f}")
    return values

def load_config(cfn):
    config_file = os.path.join("./items/", cfn)
    with open(config_file, 'rt') as fid:
        config = json.load(fid)

    return config
        
def time_comparison():
    max_mages = 7
    etimes = np.array(list(range(25, 90, 5)) + list(range(90, 271, 15)) + list(range(300, 601, 30)))
    
    out = [[] for dummy in range(max_mages)]
    
    sim_sizes = [0, 1000, 707, 577, 500, 447, 408, 378]
    
    for num_mages in range(1, max_mages + 1):
        config = load_config(f"mages_{num_mages:d}.json")
        config["configuration"]["target"] = list(range(num_mages))
        config["timing"]["delay"] = 3.0
        osim_size = 50.0*sim_sizes[num_mages]

        #config['timing']['duration'] = {
        #        "mean": 300.0,
        #        "var": 3.0,
        #        "clip": [0.0, 10000.0]}
        #sim_size = int(osim_size*10/120**0.5)
        #main(config, f"{num_mages:d}", sim_size=sim_size)[0]
        #dksok()
        for etime in etimes:
            sim_size = int(osim_size*10/etime**0.5)
            tconfig = deepcopy(config)
            tconfig['timing']['duration'] = {
                    "mean": etime,
                    "var": 3.0,
                    "clip": [0.0, 10000.0]}
            value_0 = main(tconfig, f"{num_mages:d} {etime:3.0f}  fb ", sim_size=sim_size)[0]
            tconfig["rotation"]["continuing"]["special"] = {"slot": list(range(num_mages)), "value": "scorch"}
            value_1 = main(tconfig, f"{num_mages:d} {etime:3.0f}  sc ", sim_size=sim_size)[0]
            out[num_mages - 1].append((value_1 - value_0)/num_mages)
            
    plt.close('all')
    plt.figure(figsize=(8.0, 5.5), dpi=200)
    plt.title(f"SoM Damage (Longer Encounters, no WBs, Phase 4 BiS)")
    for num_mages, ou in enumerate(out):
        #plt.plot(etimes, np.array(ou), label=config["configuration"]["name"][index])
        label = f"{num_mages + 1:d} mages"
        if num_mages < 1:
            label = label[:-1]
        plt.plot(etimes,
                 np.array(ou),
                 label=label)
    plt.xlabel('Encounter Duration (seconds)')
    plt.ylabel('Scorch Rotation - Fireball Rotation Damage (Full Team)')
    plt.grid()
    plt.xlim(0, 600)
    plt.legend()
    plt.savefig("som_mages_damage4.png")

if __name__ == '__main__':
    time_comparison()
    