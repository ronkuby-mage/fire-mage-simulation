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
        
def time_comparison():
    is_break = False
    is_zoom = True
    num_mages = 3
    
    if is_zoom:
        if num_mages == 4:
            if is_break:
                rotation_names = ["mqg-mark_fireball_mts", "sapp-mqg_fireball_mts", "presapp-mqg_fireball_mts", "sapp-mark_fireball_mts"]
            else:
                rotation_names = ["mqg-mark_pyroblast_mts", "sapp-mqg_pyroblast_mts", "presapp-mqg_pyroblast_mts", "sapp-mark_pyroblast_cbi"]
        elif num_mages == 3:
            if is_break:
                rotation_names = ["sapp-mark_fireball_wep-cbi",  "sapp-mqg_fireball_cbi", "mqg-mark_fireball_mts", "presapp-mqg_fireball_mts"]
            else:
                rotation_names = ["sapp-mark_pyroblast_wep-cbi", "sapp-mark_pyroblast_wep-wep-cbi", "presapp-mqg_pyroblast_cbi", "mqg-mark_pyroblast_mts",
                                  "presapp-mqg_pyroblast_mts"]
    else:
        if num_mages == 4:
            rotation_names = ["mqg-mark_fireball_mts", "sapp-mqg_fireball_mts", "presapp-mqg_fireball_mts", "sapp-mark_fireball_mts",
                              "mqg-mark_pyroblast_mts", "sapp-mqg_pyroblast_mts", "presapp-mqg_pyroblast_mts", "sapp-mark_pyroblast_mts",
                              "mqg-mark_pyroblast_cbi", "presapp-mqg_pyroblast_cbi", "sapp-mark_pyroblast_cbi"]
        elif num_mages == 3:
            rotation_names = ["mqg-mark_fireball_wep-wep-cbi", "sapp-mqg_fireball_wep-wep-cbi", "presapp-mqg_fireball_wep-wep-cbi", "sapp-mark_fireball_wep-wep-cbi",
                              "mqg-mark_pyroblast_wep-wep-cbi", "sapp-mqg_pyroblast_wep-wep-cbi", "presapp-mqg_pyroblast_wep-wep-cbi", "sapp-mark_pyroblast_wep-wep-cbi"]           
    rotations = len(rotation_names)
    
    if not is_zoom:
        etimes = np.array(list(range(25, 90, 5)) + list(range(90, 181, 15)))
    else:
        if num_mages == 4:
            if is_break:
                etimes = np.array(list(range(36, 69, 3)))
            else:
                etimes = np.array(list(range(35, 80, 5)))
        elif num_mages == 3:
            if is_break:
                etimes = np.array(list(range(35, 85, 5)))
            else:
                etimes = np.array(list(range(30, 95, 5)))
    
    out2 = [np.array([0.0]) for dummy in range(rotations)]
    
    sim_sizes = [0, 1000, 707, 577, 500, 447, 408, 378]
    scorches = [0, 6, 3, 2, 2, 2, 1, 1]

    
    for rotation, rname in enumerate(rotation_names):
        encounter = "template_pi_buffer"
        config = load_config(encounter + ".json")
        config["timing"]["delay"] = 1.5

        trinket, buffer, scorch = rname.split("_")

        if "presapp" in trinket:
            config["rotation"]["initial"]["common"] = ["sapp"]
        else:
            config["rotation"]["initial"]["common"] = []
        config["rotation"]["initial"]["common"] += ["scorch"]*scorches[num_mages]
        if is_break:
            config["rotation"]["initial"]["common"] += ["gcd", "gcd"]
        
        config["stats"]["spell_power"] = np.array([689 for aa in range(num_mages)])
        if "sapp" in trinket:
            config["stats"]["spell_power"] += 40
        if "mark" in trinket:
            config["stats"]["spell_power"] += 85
        config["stats"]["spell_power"] = config["stats"]["spell_power"].tolist()
            
        config["stats"]["crit_chance"] = [0.21 for aa in range(num_mages)]
        config["stats"]["hit_chance"] = [0.1 for aa in range(num_mages)]
        config["stats"]["intellect"] = [318 for aa in range(num_mages)]
        config["buffs"]["raid"] = [
             "arcane_intellect",
             "improved_mark",
             "blessing_of_kings"]
        config["buffs"]["consumes"] = [
             "greater_arcane_elixir",
             "elixir_of_greater_firepower",
             "flask_of_supreme_power",
             "brilliant_wizard_oil",
             "very_berry_cream"]
        config["buffs"]["world"] = [
            "rallying_cry_of_the_dragonslayer",
            "spirit_of_zandalar",
            "dire_maul_tribute",
            "songflower_serenade",
            "sayges_dark_fortune_of_damage"]
        #config["buffs"]["world"] = []
        config["buffs"]["racial"] = ["human"]*num_mages
        config["configuration"]["num_mages"] = num_mages
        if "mqg" in trinket:
            config["configuration"]["mqg"] = list(range(num_mages))
        if "sapp" in trinket:
            config["configuration"]["sapp"] = list(range(num_mages))
        config["configuration"]["pi"] = list(range(num_mages))
        config["configuration"]["target"] = list(range(num_mages))
        
        #if num_mages > 4:
        #    config["configuration"]["sapp"] = list(range(num_mages))
        #else:
        #    config["configuration"]["mqg"] = list(range(num_mages))
        #config["configuration"]["mqg"] = list(range(num_mages))
        config["configuration"]["pi"] = list(range(num_mages))
        config["configuration"]["name"] = [f"mage{idx + 1:d}" for idx in range(num_mages)]

        if "pyroblast" in buffer or is_break:
            config["rotation"]["initial"]["have_pi"] = []
        else:
            config["rotation"]["initial"]["have_pi"] = ["gcd"]

        if trinket.split("-")[0] == "mqg":
            config["rotation"]["initial"]["have_pi"] += []
        else:
            config["rotation"]["initial"]["have_pi"] += ["sapp"]

        config["rotation"]["initial"]["have_pi"] += ["combustion"]

        if "pyroblast" in buffer:
            config["rotation"]["initial"]["have_pi"] += ["pyroblast"]
        else:
            config["rotation"]["initial"]["have_pi"] += ["fireball"]
        config["rotation"]["initial"]["have_pi"] += [
               "pi",
               "mqg",
               "fireball"]

        config["rotation"]["initial"]["have_pi"] += ["fireball"]*(7 - len(config["rotation"]["initial"]["have_pi"]))
        
        config["rotation"]["continuing"] = {"default": "fireball"}

        mapping = {
                "mts": "maintain_scorch",
                "wep": "scorch_wep",
                "cbi": "cobimf"}
        for idx, special in enumerate(scorch.split("-")):
            for key, values in config["rotation"]["continuing"].items():
                if "value" in values:
                    if values["value"] == mapping[special]:
                        config["rotation"]["continuing"][key]["slot"].append(idx)
                        break
            else:
                spec_val = len(config["rotation"]["continuing"])
                config["rotation"]["continuing"][f"special{spec_val:d}"] = {
                        "slot": [idx],
                        "value": mapping[special]}
                if special == "cbi":
                    config["rotation"]["continuing"][f"special{spec_val:d}"]["cast_point_remain"] = 0.5

        print(f'On {rname:s} {config["stats"]["spell_power"][0]:d}:')
        for idx, cline in enumerate(config["rotation"]["initial"]["common"]):
            print(f'  0{idx:d} {cline:s}')
        for idx, cline in enumerate(config["rotation"]["initial"]["have_pi"]):
            print(f'  1{idx:d} {cline:s}')
        print("  ", config["rotation"]["continuing"])

        osim_size = 30.0*sim_sizes[num_mages]

        var = 3.0
        sim_size = int(osim_size*10/min(etimes)**0.5)
        config['timing']['duration'] = {
                "mean": max(etimes) + 5.0*var,
                "var": var,
                "clip": [0.0, 10000.0]}
        #value_0 = main(config, f"{num_mages:d}  0", sim_size=sim_size)
        value_0 = main(config, f"{num_mages:d}  0", sim_size=sim_size, dur_dist=etimes)
        out2[rotation] = value_0
            
    plt.close('all')
    #plt.figure(figsize=(8.0, 5.5), dpi=200)
    plt.figure(figsize=(6.5, 4.0), dpi=200)
    #plt.title(f"CE Crit Values (Shorter Encounters, WBs, No PI, Ignite Hold, Phase 6 Gear)")
    for rotation, rot_name in enumerate(rotation_names):
        #plt.plot(etimes, np.array(ou), label=config["configuration"]["name"][index])
        plt.plot(etimes, np.array(out2[rotation])/num_mages, label=rot_name)
    plt.xlabel('Encounter Duration (seconds)')
    plt.ylabel('Damage per mage')
    plt.title(f"{num_mages:d} mages,{'' if is_break else ' no':s} break")
    plt.grid()
    if is_zoom:
        if num_mages == 4:
            if is_break:
                plt.xlim(40, 65)
                plt.ylim(1620, 1760)
            else:
                plt.xlim(35, 75)
                plt.ylim(1740, 1780)
        elif num_mages == 3:
            if is_break:
                plt.xlim(40, 80)
                plt.ylim(1800, 1950)
            else:            
                plt.ylim(1800, 2000)
                plt.xlim(30, 90)
    else:
        plt.xlim(30, 120)
            
    plt.legend(loc=4)
    plt.savefig(f"ce4_{encounter:s}.png")

if __name__ == '__main__':
    time_comparison()
    