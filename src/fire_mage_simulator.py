import os
import json
from copy import deepcopy
from mechanics import get_damage

VERSION = 3

def main(config, name):
    sim_size = 50000
    config["sim_size"] = sim_size
    print("running", name)
    values = get_damage(config)
    print(values)
    
    return values

def trinket(config):
    mqg_mark = []
    tear_mark = []
    trange = list(range(30, 185, 10))
    config["buffs"]["world"] = []
    for tindex in trange:
        configo = deepcopy(config)
        configo["timing"]["duration"]["mean"] = float(tindex)
        mqg_mark.append(main(configo, 'hi')[0])
        configo["stats"]["spell_power"][4] += 44 + 4
        configo["stats"]["hit_chance"][4] += 0.01
        configo["stats"]["crit_chance"][4] += 0.01
        configo["configuration"]["mqg"].remove(4)
        tear_mark.append(main(configo, 'hi')[0])
    for tt, d1, d2 in zip(trange, mqg_mark, tear_mark):
        print(tt, d1, d2)

def loatheb_stat_weights(config):
    configo = deepcopy(config)
    configo["timing"]["duration"]["mean"] = float(80)
    configo["buffs"]["boss"].append("loatheb")
    base = main(configo, 'base')[0]
    configo["stats"]["spell_power"][4] += 10.0
    ds = main(configo, 'base')[0]
    configo["stats"]["spell_power"][4] -= 10.0
    configo["stats"]["hit_chance"][4] += 0.01
    dh = main(configo, 'base')[0]
    configo["stats"]["hit_chance"][4] -= 0.01
    configo["stats"]["crit_chance"][4] += 0.01
    dc = main(configo, 'base')[0]
    print(10*(dh - base)/(ds - base))
    print(10*(dc - base)/(ds - base))
    #configo["configuration"]["mqg"].remove(4)

def thaddius_stat_weights(config):
    configo = deepcopy(config)
    #configo["timing"]["duration"]["mean"] = float(80)
    configo['buffs']['world'] = []
    #configo["buffs"]["boss"].append("thaddius")
    base = main(configo, 'base')[0]
    configo["stats"]["spell_power"][4] += 10.0
    ds = main(configo, 'base')[0]
    configo["stats"]["spell_power"][4] -= 10.0
    configo["stats"]["hit_chance"][4] += 0.01
    dh = main(configo, 'base')[0]
    configo["stats"]["hit_chance"][4] -= 0.01
    configo["stats"]["crit_chance"][4] += 0.01
    dc = main(configo, 'base')[0]
    print(10*(dh - base)/(ds - base))
    print(10*(dc - base)/(ds - base))


def switch_trinket(config):
    configo = deepcopy(config)
    configo["stats"]["spell_power"][4] += 44 + 4
    configo["stats"]["hit_chance"][4] += 0.01
    configo["stats"]["crit_chance"][4] += 0.01
    configo["configuration"]["mqg"].remove(4)

    return configo
        
def naxx_upgrade_comparison(config):
    # missing gothic, 4H, 2x spider, sapp
    weighting = [('wb', 0.75), ('no_wb', 0.25)]
    encounters = [
            {'name': 'patchwork',
             'duration': 160.0},
            {'name': 'grobbulus',
             'duration': 93.0},
            {'name': 'gluth',
             'duration': 80.0},
            {'name': 'thaddius',
             'duration': 80.0},
            {'name': 'noth',
             'duration': 72.0},
            {'name': 'heigan',
             'duration': 81.0},
            {'name': 'loatheb',
             'duration': 165.0},
            {'name': 'raz',
             'duration': 109.0},
            {'name': 'anub',
             'duration': 128.0},
            {'name': 'kt',
             'duration': 180.0}]
    
    gears = [
            {'name': 'current',
             'dsp': 0.0,
             'dhit': 0.0,
             'dcrit': 0.0},
            {'name': 'polarity',
             'dsp': -13.0,
             'dhit': 0.0,
             'dcrit': 0.02},
            {'name': 'power',
             'dsp': -3.0,
             'dhit': 0.0,
             'dcrit': 0.01},
            {'name': 't3_helm',
             'dsp': 2.0,
             'dhit': 0.0,
             'dcrit': 0.01},
            {'name': 'necro_cape',
             'dsp': 3.0,
             'dhit': 0.0,
             'dcrit': 0.01},
            {'name': 'inevitable',
             'dsp': 15.0,
             'dhit': 0.0,
             'dcrit': 0.0}]
    summary = []
    for gear in gears:
        sum_dps = 0.0
        pconfig = deepcopy(config)
        pconfig['buffs']['world'].remove('sayges_dark_fortune_of_damage')
        pconfig['stats']['spell_power'][4] += gear['dsp']
        pconfig['stats']['hit_chance'][4] += gear['dhit']
        pconfig['stats']['crit_chance'][4] += gear['dcrit']

        for encounter in encounters:
            tconfig = deepcopy(pconfig) if encounter['duration'] < 140.0 else switch_trinket(pconfig)
            tconfig['timing']['duration'] = encounter['duration']
            tconfig["buffs"]["boss"].append(encounter['name'])
            for name, weight in weighting:
                dconfig = deepcopy(tconfig)
                if name == 'no_wb':
                    dconfig['buffs']['world'] = []
                value = main(dconfig, encounter['name'])
                sum_dps += weight*value[0]
        summary.append((gear['name'], sum_dps/len(encounters)))
    for gear, value in summary:
        print(f"{gear:10s}: {value:6.1f}")
        
if __name__ == '__main__':
    config_file = "../config/sample1.json"
    with open(config_file, 'rt') as fid:
        config = json.load(fid)
    name = os.path.split(config_file)[-1].split('.')[0]
    print('starting', name)
    naxx_upgrade_comparison(config)
    #loatheb_stat_weights(config)
    #thaddius_stat_weights(config)