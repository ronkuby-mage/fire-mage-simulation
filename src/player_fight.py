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
    sim_size = 10000
    config["sim_size"] = sim_size
    values = get_damage(config, ret_dist=ret_dist)
    print(f"  {name}={values[0]:6.1f}")
    return values

def load_config(cfn):
    config_file = os.path.join("../config/", cfn)
    with open(config_file, 'rt') as fid:
        config = json.load(fid)
    #name = os.path.split(config_file)[-1].split('.')[0]
    #print('starting', name)

    return config
        
def time_comparison():
    encounter = "patchwork"
    config = load_config(encounter + ".json")
    config["timing"]["delay"] = 3.0

    if False:
        encounter += "_extra_buffs_2"
        ronkuby = config["configuration"]["name"].index("ronkuby")
        config["stats"]["spell_power"][ronkuby] += 24
        config["stats"]["crit_chance"][ronkuby] -= 0.01
        config["stats"]["spell_power"] = [a + 23 for a in config["stats"]["spell_power"]]
    if False:
        config["buffs"]["world"] = []

    out = [[] for dummy in range(config["configuration"]["num_mages"])]
    err = [[] for dummy in range(config["configuration"]["num_mages"])]
    etimes = np.array(list(range(25, 76, 3)) + list(range(80, 251, 10)))
    #etimes = np.array([100.0])
    for etime in etimes:
        for index in range(config["configuration"]["num_mages"]):
            tconfig = deepcopy(config)
            tconfig["configuration"]["target"] = [index]
            #tconfig['buffs']['world'] = []
            tconfig['timing']['duration'] = {
                    "mean": etime,
                    "var": 3.0,
                    "clip": [0.0, 10000.0]}
            value = main(tconfig, config["configuration"]["name"][index])
            out[index].append(value[0])
            err[index].append(value[1])
            
    plt.close('all')
    plt.figure(figsize=(8.0, 5.5), dpi=200)
    plt.title(f"{encounter:s}")
    for index, (ou, er) in enumerate(zip(out, err)):
        #plt.plot(etimes, np.array(ou), label=config["configuration"]["name"][index])
        plt.errorbar(etimes,
                     np.array(ou),
                     yerr=np.array(er),
                     fmt='o',
                     capsize=10,
                     label=config["configuration"]["name"][index])
    plt.xlabel('Encounter Duration (seconds)')
    plt.ylabel('Average DPS')
    plt.xlim(0, 250)
    plt.legend()
    plt.savefig(encounter + ".png")

def time_comparison_no_err():
    encounter = "patchwork"
    config = load_config(encounter + ".json")
    config["timing"]["delay"] = 3.0

    if False:
        encounter += "_extra_buffs_2"
        for idx, name in config["configuration"]["name"]:
            if "ronkuby" in name:
                config["stats"]["spell_power"] += 24
                config["stats"]["crit_chance"] -= 0.01
                config["stats"]["spell_power"] += 23
    if False:
        caption = "no world buffs"
        config["buffs"]["world"] = []
    else:
        caption = "world buffs"

    out = [[] for dummy in range(config["configuration"]["num_mages"])]
    etimes = np.array(list(range(25, 76, 3)) + list(range(80, 251, 10)))
    #etimes = np.array([100.0])
    for etime in etimes:
        for index in range(config["configuration"]["num_mages"]):
            tconfig = deepcopy(config)
            tconfig["configuration"]["target"] = [index]
            tconfig['timing']['duration'] = {
                    "mean": etime,
                    "var": 3.0,
                    "clip": [0.0, 10000.0]}
            value = main(tconfig, config["configuration"]["name"][index])
            out[index].append(value[0])
            
    plt.close('all')
    plt.figure(figsize=(8.0, 5.5), dpi=200)
    plt.title(f"{encounter:s} {caption:s}")
    for index, ou in enumerate(out):
        #plt.plot(etimes, np.array(ou), label=config["configuration"]["name"][index])
        plt.plot(etimes,
                 np.array(ou),
                 label=config["configuration"]["name"][index])
    plt.xlabel('Encounter Duration (seconds)')
    plt.ylabel('Average DPS')
    plt.xlim(0, 250)
    plt.legend()
    plt.savefig(f"{encounter:s}_{caption:s}.png")

if __name__ == '__main__':
    time_comparison_no_err()
    