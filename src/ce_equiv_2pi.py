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
    print(f"  {name}={values[0]:6.1f}")
    return values

def load_config(cfn):
    config_file = os.path.join("../config/", cfn)
    with open(config_file, 'rt') as fid:
        config = json.load(fid)

    return config
        
def time_comparison():
    max_mages = 7
    do_ep = True
    
    etimes = np.array(list(range(25, 90, 5)) + list(range(90, 181, 15)))
    print(etimes)
    
    if do_ep:
        out_pyro = [np.array([0.0]) for dummy in range(max_mages)]
        out_fb = [np.array([0.0]) for dummy in range(max_mages)]
        out_scorch = [np.array([0.0]) for dummy in range(max_mages)]
    out2 = [np.array([0.0]) for dummy in range(max_mages)]
    
    sim_sizes = [0, 1000, 707, 577, 500, 447, 408, 378]
    scorches = [0, 6, 3, 2, 2, 2, 1, 1]
    
    for num_mages in range(3, max_mages + 1):
        encounter = "template_pi_buffer"
        config = load_config(encounter + ".json")
        config["timing"]["delay"] = 2.0
        config["rotation"]["initial"]["common"] = ["scorch"]*scorches[num_mages]
        config["rotation"]["continuing"]["special"] = {
                "slot": [num_mages - 1],
                "value": "scorch_wep"
                }
        
        config["stats"]["spell_power"] = [785, 785] + [745 for aa in range(2, num_mages)]
        config["stats"]["crit_chance"] = [0.15 for aa in range(num_mages)]
        config["stats"]["hit_chance"] = [0.1 for aa in range(num_mages)]
        config["stats"]["intellect"] = [302 for aa in range(num_mages)]
        
        config["stats"]["spell_power"][-1] = 748
        config["stats"]["crit_chance"][-1] = 0.18
        config["stats"]["intellect"][-1] = 335
        
        config["buffs"]["raid"] = [
             "arcane_intellect",
             "improved_mark",
             "blessing_of_kings"]
        config["buffs"]["consumes"] = [
             "greater_arcane_elixir",
             "elixir_of_greater_firepower",
             "flask_of_supreme_power",
             "blessed_wizard_oil"]
        config["buffs"]["world"] = [
            "rallying_cry_of_the_dragonslayer",
            "spirit_of_zandalar",
            "dire_maul_tribute",
            "songflower_serenade",
            "sayges_dark_fortune_of_damage"]
        config["buffs"]["racial"] = ["human"]*num_mages
        config["configuration"]["num_mages"] = num_mages
        config["configuration"]["target"] = list(range(num_mages))
        
        config["configuration"]["sapp"] = [0, 1, num_mages - 1]
        config["configuration"]["mqg"] = list(range(2, num_mages - 1))
        config["configuration"]["pi"] = [0, 1]

        config["configuration"]["name"] = [f"mage{idx + 1:d}" for idx in range(num_mages)]
        
        if do_ep:
            osim_size = 1000.0*sim_sizes[num_mages]
        else:
            osim_size = 30.0*sim_sizes[num_mages]

        var = 3.0
        sim_size = int(osim_size*10/min(etimes)**0.5)
        config['timing']['duration'] = {
                "mean": max(etimes) + 5.0*var,
                "var": var,
                "clip": [0.0, 10000.0]}
        value_0 = main(config, f" {num_mages:d}  0", sim_size=sim_size, dur_dist=etimes)
        out2[num_mages - 1] = value_0
        if do_ep:
            config["stats"]["spell_power"][0] += 30
            value_sp = main(config, f"p{num_mages:d} sp", sim_size=sim_size, dur_dist=etimes)
            config["stats"]["spell_power"][0] -= 30
            config["stats"]["crit_chance"][0] += 0.03
            value_cr = main(config, f"p{num_mages:d} cr", sim_size=sim_size, dur_dist=etimes)
            config["stats"]["spell_power"][0] += 30
            config["stats"]["crit_chance"][0] -= 0.03
            out_pyro[num_mages - 1] = 10.0*(value_cr - value_0)/(value_sp - value_0)

            if num_mages > 3:
                config["stats"]["spell_power"][2] += 30
                value_sp = main(config, f"f{num_mages:d} sp", sim_size=sim_size, dur_dist=etimes)
                config["stats"]["spell_power"][2] -= 30
                config["stats"]["crit_chance"][2] += 0.03
                value_cr = main(config, f"f{num_mages:d} cr", sim_size=sim_size, dur_dist=etimes)
                config["stats"]["spell_power"][2] += 30
                config["stats"]["crit_chance"][2] -= 0.03
                out_fb[num_mages - 1] = 10.0*(value_cr - value_0)/(value_sp - value_0)


            config["stats"]["spell_power"][-1] += 30
            value_sp = main(config, f"s{num_mages:d} sp", sim_size=sim_size, dur_dist=etimes)
            config["stats"]["spell_power"][-1] -= 30
            config["stats"]["crit_chance"][-1] += 0.03
            value_cr = main(config, f"s{num_mages:d} cr", sim_size=sim_size, dur_dist=etimes)
            out_scorch[num_mages - 1] = 10.0*(value_cr - value_0)/(value_sp - value_0)
        with open("savestate2.dat", "wb") as fid:
            pickle.dump(out2, fid)
            if do_ep:
                pickle.dump(out_pyro, fid)
                pickle.dump(out_fb, fid)
                pickle.dump(out_scorch, fid)

            
    if do_ep:
        for type_st, out in [("pyro", out_pyro), ("fb", out_fb), ("scorch", out_scorch)]:
            plt.close('all')
            plt.figure(figsize=(8.0, 5.5), dpi=200)
            #plt.title(f"CE Crit Values (Shorter Encounters, WBs, No PI, Ignite Hold, Phase 6 Gear)")
            for num_mages, ou in enumerate(out):
                if type_st == "fb" and num_mages + 1 <= 3:
                    continue
                if not(ou.any()):
                    continue
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
            plt.xlim(0, 180)
            plt.legend()
            plt.savefig(f"ce2_2pi_crit_{type_st:s}_{encounter:s}.png")

    plt.close('all')
    plt.figure(figsize=(8.0, 5.5), dpi=200)
    #plt.title(f"CE Crit Values (Shorter Encounters, WBs, No PI, Ignite Hold, Phase 6 Gear)")
    for num_mages, ou in enumerate(out2):
        if not(ou.any()):
            continue
        #plt.plot(etimes, np.array(ou), label=config["configuration"]["name"][index])
        label = f"{num_mages + 1:d} mages"
        if num_mages < 1:
            label = label[:-1]
        plt.plot(etimes,
                 np.array(ou)/(num_mages + 1),
                 label=label)
    plt.xlabel('Encounter Duration (seconds)')
    plt.ylabel('Damage per mage')
    plt.grid()
    plt.xlim(0, 180)
    plt.legend()
    plt.savefig(f"ce2_2pi_{encounter:s}.png")

if __name__ == '__main__':
    time_comparison()
    