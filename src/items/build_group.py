import os
import json
import pickle
from items import CharInfo

__savefile = "items.dat"
        
if __name__ == "__main__":
    encounter = "loatheb"
    encounter = "pink-team"
    template = "template.json"

    if os.path.exists(__savefile):
        with open(__savefile, "rb") as fid:
            saved = pickle.load(fid)
    else:
        saved = {}

    chars = []    
    for filename in os.listdir(encounter):
        fullfile = os.path.join(encounter, filename)
        name = filename.split('-')[-1].split('.')[0]
        char_info = CharInfo(fullfile, name, saved)
        chars.append(char_info)
        print(name, char_info.spd, char_info.is_udc)

    with open(__savefile, "wb") as fid:
        pickle.dump(saved, fid)

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

    with open(encounter + ".json", "wt") as fid:
        json.dump(econf, fid, indent=3)
    