import os
import json
import pickle
from copy import deepcopy
from mechanics import get_damage
from items.items import CharInfo

__savefile = "items/items.dat"

def main_dam(config, name, duration=80.0, buffs=False, ret_dist=False, sim_size=250):
    tconfig = deepcopy(config)
    tconfig['timing']['duration'] = {"mean": duration, "var": 3.0, "clip": [0.0, 10000.0]}
    if not buffs:
        tconfig["buffs"]["world"] = []
    tconfig["sim_size"] = sim_size
    values = get_damage(tconfig, ret_dist=ret_dist)
    #print(f"  {name}={values[0]:6.1f}")
    return values

def compute(config, name, durations, buffs, sim_size):
    return sum([main_dam(config, name, sim_size=sim_size, buffs=wb, duration=dur)[0] for wb, dur in zip(buffs, durations)])/len(buffs)

def get_chars(encounter, saved):
    chars = []    
    for filename in os.listdir(encounter):
        fullfile = os.path.join(encounter, filename)
        name = filename.split('-')[-1].split('.')[0]
        char_info = CharInfo(fullfile, name, saved)
        chars.append(char_info)

    return chars    

def get_conf(chars, target=None):
    template = "items/template.json"
    
    with open(template, "rt") as fid:
        econf = json.load(fid)
    
    econf["stats"] = {
            "spell_power": [],
            "hit_chance": [],
            "crit_chance": [],
            "intellect": []
            }
    econf["buffs"]["racial"] = []
    econf["configuration"] = {
            "num_mages": len(chars),
            "target": [],
            "sapp": [],
            "toep": [],
            "zhc": [],
            "mqg": [],
            "pi": [],
            "udc": [],
            "name": []}

    for cindex, char in enumerate(chars):
        econf["stats"]["spell_power"].append(char.spd)
        econf["stats"]["hit_chance"].append(char.hit/100.0)
        crit = char.crt
        for char2 in chars:
            if char2.name != char.name and char2.atiesh:
                crit += 2

        econf["stats"]["crit_chance"].append(crit/100.0)
        econf["stats"]["intellect"].append(char.intellect)
        econf["buffs"]["racial"].append(char.race)

        for active in ["sapp", "toep", "zhc", "mqg"]:
            if active in char.act:
                econf["configuration"][active].append(cindex)
        if char.is_udc:
            econf["configuration"]["udc"].append(cindex)
        econf["configuration"]["name"].append(char.name)
    if target is not None:
        econf["configuration"]["target"] = [target]

    return econf
    
def main():
    #encounter = os.path.join("items", "pinkteam")
    encounter = os.path.join("items", "patchwork")

    with open(__savefile, "rb") as fid:
        saved = pickle.load(fid)

    chars = get_chars(encounter, saved)

    #wbs = [True, False, True, False]
    #ttime = [120.0, 120.0, 200.0, 200.0]
    wbs = [True]
    ttime = [150.0]

    # UDC and atiesh
    #blacklist = [23091, 23084, 23085, 22589]
    #blacklist = [23091, 23084, 23085]
    #blacklist = list(saved.keys())
    #blacklist.remove(22589)
    blacklist = []
    grouplist = [[(23091, False), (23084, False), (23085, False), (21344, False),
                  (21709, False), (23031, True), (19339, False), (23207, True),
                  (22497, False)], # UDC + eniga_b + hit rings + mark/mqg + T3 pants
                 [(23091, False), (23084, False), (23085, False), (21344, False),
                  (21709, False), (23031, True), (19339, False), (23207, True)], # UDC + eniga_b + hit rings + mark/mqg
                 [(23070, False), (22820, False)], # polarity + hit wand
                 [(22807, False), (23049, False)]] # wraith + sapps eye
    #grouplist = [[(22500, False), (19339, True), (22807, False), (23049, False), (21585, False), (22821, False)], # non udc
    #             [(23091, False), (23084, False), (23085, False), (21344, False),
    #              (21709, False), (23031, True), (19339, False), (23207, True),
    #              (22807, False), (23049, False), (22820, False)]] # wraith + sapps eye
    
    dupes = [11, 12]
    sim_size = 10000
    threshold = -2.0

    #for idx in range(len(chars)):
    for idx in [range(len(chars))[3]]:
        chars = get_chars(encounter, saved)
        config = get_conf(chars, target=idx)

        baseline = compute(config, config["configuration"]["name"][idx], ttime, wbs, sim_size)
        test_line = compute(config, config["configuration"]["name"][idx], [ttime[0]], [wbs[0]], sim_size)
        print(config["configuration"]["name"][idx], baseline)

        best_list = []
        for item in saved:
            
            if saved[item]["slt"] is None:
                continue
            if item in [itm.item for itm in chars[idx]._items]:
                continue
            if item in blacklist:
                continue
            
            tchars = get_chars(encounter, saved)
            tchars[idx].replace(item, saved)
            
            config = get_conf(tchars, target=idx)
            rname = config["configuration"]["name"][idx] + "_" + saved[item]["name"]
            check = compute(config, rname, [ttime[0]], [wbs[0]], sim_size//10)
            print("  ", rname, check)
            if check > test_line + threshold:
                value = compute(config, rname, ttime, wbs, sim_size)
                best_list.append(((value - baseline)/baseline, saved[item]["name"], False))
            
            if saved[item]["slt"] in dupes:
                tchars = get_chars(encounter, saved)
                tchars[idx].replace(item, saved, second=True)
                config = get_conf(tchars, target=idx)
                rname = config["configuration"]["name"][idx] + "_" + saved[item]["name"]
                check = compute(config, rname, [ttime[0]], [wbs[0]], sim_size//10)
                print("  ", rname, check)
                if check > test_line + threshold:
                    value = compute(config, rname, ttime, wbs, sim_size)
                    best_list.append(((value - baseline)/baseline, saved[item]["name"], True))


        for group in grouplist:
            tchars = get_chars(encounter, saved)
            for item, second in group:
                tchars[idx].replace(item, saved, second=second)
            config = get_conf(tchars, target=idx)
            rname = config["configuration"]["name"][idx] + "_" + ''.join([saved[item]["name"][:3] for item, ss in group])
            check = compute(config, rname, [ttime[0]], [wbs[0]], sim_size//10)
            print("  ", rname, check)
            if check > test_line + threshold:
                value = compute(config, rname, ttime, wbs, sim_size)
                best_list.append(((value - baseline)/baseline, ''.join([saved[item]["name"][:3] for item, ss in group]), False))
            

        best_list.sort(reverse=True)
        print(config["configuration"]["name"][idx])
        for value, name, sec in best_list:
            print(f"  {name:36s} {100.0*value:5.3f} {'2nd slot' if sec else '':s}")
    


if __name__ == "__main__":
    main()    