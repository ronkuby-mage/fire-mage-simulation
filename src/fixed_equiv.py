import os
import json
from copy import deepcopy
from mechanics import get_damage
import matplotlib as mpl
mpl.use('Agg')

VERSION = 3
_TYPE = 0

def output_info(values, nm):
    print(f"mean: {values[0]/nm:.0f}  std: {values[1]/nm:.1f}  low 2sig: {values[8]/nm:.0f}  high 2sig: {values[2]/nm:.0f}")

def main(config, name, ret_dist=False):
    sim_size = 100000
    config["sim_size"] = sim_size
    values = get_damage(config, ret_dist=ret_dist)
    print(f"  {name}={values[_TYPE]:7.2f}")
    return values

def load_config(cfn):
    config_file = os.path.join("../config/", cfn)
    with open(config_file, 'rt') as fid:
        config = json.load(fid)
    #name = os.path.split(config_file)[-1].split('.')[0]
    #print('starting', name)

    return config

def last_player():
    #encounter = "two_new_rotation"
    #encounter = "trem_eye"
    #encounter = "six_rnh"
    #encounter = "loatheb_udc1"
    #encounter = "3_buffer"
    #encounter = "two_thaddius"
    #encounter = "record_run_fb"
    #encounter = "three_thaddius"
    #encounter = "2pi_no_UDC"
    #encounter = "2_mages_dragon_nightfall"
    encounter = "2_mages_dragon_nightfall_go_for_it"

    # changes 4 mage pi no UDC
    

    config = load_config(encounter + ".json")
    to_mod = config["configuration"]["target"]
    to_mod = [1]
    #config["timing"]["delay"] = 3.0
    config["timing"]["delay"] = 2.0
    #config["buffs"]["boss"] = "loatheb"
    #config["configuration"]["target"] = [config["configuration"]["num_mages"] - 1]
    config = deepcopy(config)
    config['timing']['duration'] = {
            "mean": 110.0,
            "var": 10.0,
            "clip": [3.0, 10000.0]}
    print(config)
    value = main(config, "v0")
    if True:
        output_info(value, len(config["configuration"]["target"]))
    else:
        output_info(value, len(config["configuration"]["target"]))
        value_0 = value[_TYPE]
        for tt in to_mod:
            config["stats"]["spell_power"][tt] += 15
        value_sp = main(config, "v_sp")[_TYPE]
        for tt in to_mod:
            config["stats"]["spell_power"][tt] -= 15
            config["stats"]["crit_chance"][tt] += 0.015
        value_cr = main(config, "v_cr")[_TYPE]
        print(10.0*(value_cr - value_0)/(value_sp - value_0))
            

if __name__ == '__main__':
    last_player()
    