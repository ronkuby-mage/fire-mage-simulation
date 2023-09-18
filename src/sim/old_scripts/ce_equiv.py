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
    etimes = np.array(list(range(25, 90, 5)) + list(range(90, 241, 15)) + list(range(300, 601, 30)))
    
    out = [[] for dummy in range(max_mages)]
    
    sim_sizes = [0, 1000, 707, 577, 500, 447, 408, 378]
    
    for num_mages in range(1, max_mages + 1):
        config = load_config(f"mages_{num_mages:d}.json")
        config["timing"]["delay"] = 3.0
        config["rotation"]["continuing"]["special"] = {"slot": list(range(num_mages)), "value": "scorch"}
        config["stats"]["spell_power"] = [745 for aa in range(num_mages)]
        config["stats"]["crit_chance"] = [0.15 for aa in range(num_mages)]
        config["stats"]["intellect"] = [302 for aa in range(num_mages)]
        config["buffs"]["raid"].append("blessing_of_kings")
        config["buffs"]["consumes"] = {
             "greater_arcane_elixir",
             "elixir_of_greater_firepower",
             "flask_of_supreme_power",
             "blessed_wizard_oil"}
        config["buffs"]["world"] = {
            "rallying_cry_of_the_dragonslayer",
            "spirit_of_zandalar",
            "dire_maul_tribute",
            "songflower_serenade",
            "sayges_dark_fortune_of_damage"}
        config["configuration"]["mqg"] = list(range(num_mages))
        config["configuration"]["pi"] = list(range(num_mages))
        osim_size = 150.0*sim_sizes[num_mages]

        for etime in etimes:
            sim_size = int(osim_size*10/etime**0.5)
            tconfig = deepcopy(config)
            tconfig['timing']['duration'] = {
                    "mean": etime,
                    "var": 3.0,
                    "clip": [0.0, 10000.0]}
            value_0 = main(tconfig, f"{num_mages:d} {etime:3.0f}  0", sim_size=sim_size)[0]
            tconfig["stats"]["spell_power"][-1] += 30
            value_sp = main(tconfig, f"{num_mages:d} {etime:3.0f} sp", sim_size=sim_size)[0]
            tconfig["stats"]["spell_power"][-1] -= 30
            tconfig["stats"]["crit_chance"][-1] += 0.03
            value_cr = main(tconfig, f"{num_mages:d} {etime:3.0f} cr", sim_size=sim_size)[0]
            out[num_mages - 1].append(10.0*(value_cr - value_0)/(value_sp - value_0))
            
    plt.close('all')
    plt.figure(figsize=(8.0, 5.5), dpi=200)
    plt.title(f"CE Crit Values (Shorter Encounters, WBs, Always Fireball, Phase 6 Gear)")
    for num_mages, ou in enumerate(out):
        #plt.plot(etimes, np.array(ou), label=config["configuration"]["name"][index])
        label = f"{num_mages + 1:d} mages"
        if num_mages < 1:
            label = label[:-1]
        plt.plot(etimes,
                 np.array(ou),
                 label=label)
    plt.xlabel('Encounter Duration (seconds)')
    plt.ylabel('SP per 1% Crit')
    plt.grid()
    plt.xlim(0, 600)
    plt.legend()
    plt.savefig("ce_crit_phase6_scorch.png")

if __name__ == '__main__':
    time_comparison()
    