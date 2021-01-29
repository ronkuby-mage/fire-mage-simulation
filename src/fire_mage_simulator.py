import os
import json
from copy import deepcopy
from mechanics import get_damage

VERSION = 3

def main(config, name):
    sim_size = 250000
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
    configo['buffs']['boss'] = ["thaddius"]
    configo['buffs']['world'] = []
    base = main(configo, 'base')[0]
    configo["stats"]["spell_power"][4] += 10.0
    ds = main(configo, 'sp')[0]
    configo["stats"]["spell_power"][4] -= 10.0
    configo["stats"]["hit_chance"][4] += 0.01
    dh = main(configo, 'hit')[0]
    configo["stats"]["hit_chance"][4] -= 0.01
    configo["stats"]["crit_chance"][4] += 0.01
    dc = main(configo, 'crit')[0]
    hit_eq = 10*(dh - base)/(ds - base)
    crit_eq = 10*(dc - base)/(ds - base)
    print(f"hit equiv  = {hit_eq:4.1f}")
    print(f"crit equiv = {crit_eq:4.1f}")

def switch_trinket(config, gear):
    configo = deepcopy(config)
    configo["stats"]["spell_power"][4] += 44 + 4
    configo["stats"]["hit_chance"][4] += 0.01
    configo["stats"]["crit_chance"][4] += 0.01
    if gear['name'] == 'eternal':
        configo["stats"]["spell_power"][4] += 9.0
    configo["configuration"]["mqg"].remove(4)

    return configo
        
def naxx_upgrade_comparison(config):
    # missing gothic, 4H, 2x spider, sapp
    weighting = [('wb', 0.75), ('no_wb', 0.25)]
    encounters = [
            {'name': 'patchwork',
             'duration': 160.0,
             'undead': True},
            {'name': 'grobbulus',
             'duration': 93.0,
             'undead': True},
            {'name': 'gluth',
             'duration': 80.0,
             'undead': True},
            {'name': 'thaddius',
             'duration': 80.0,
             'undead': True},
            {'name': 'noth',
             'duration': 72.0,
             'undead': True},
            {'name': 'heigan',
             'duration': 81.0,
             'undead': True},
            {'name': 'loatheb',
             'duration': 165.0,
             'undead': True},
            {'name': 'raz',
             'duration': 109.0,
             'undead': True},
            {'name': 'anub',
             'duration': 128.0,
             'undead': True},
            {'name': 'faerlina',
             'duration': 80.0,
             'undead': False},
            {'name': 'maexxna',
             'duration': 90.0,
             'undead': False},
            {'name': 'kt',
             'duration': 180.0,
             'undead': True}]
    
    gears = [
            {'name': 'current',
             'dsp': 0.0,
             'dhit': 0.0,
             'dcrit': 0.0,
             'undead': True},
            {'name': 't3_boots',
             'dsp': -6.0,
             'dhit': 0.0,
             'dcrit': 0.01,
             'undead': False},
            {'name': 't3_robe',
             'dsp': 8.0,
             'dhit': 0.01,
             'dcrit': 0.0,
             'undead': False},
            {'name': 'eternal',
             'dsp': 9.0,
             'dhit': 0.0,
             'dcrit': 0.0,
             'undead': False},
            {'name': 'polarity',
             'dsp': -13.0,
             'dhit': 0.0,
             'dcrit': 0.02,
             'undead': True},
            {'name': 'power',
             'dsp': -3.0,
             'dhit': 0.0,
             'dcrit': 0.01,
             'undead': True},
            {'name': 't3_helm',
             'dsp': 2.0,
             'dhit': 0.0,
             'dcrit': 0.01,
             'undead': True},
            {'name': 'necro_cape',
             'dsp': 3.0,
             'dhit': 0.0,
             'dcrit': 0.01,
             'undead': True},
            {'name': 'inevitable',
             'dsp': 15.0,
             'dhit': 0.0,
             'dcrit': 0.0,
             'undead': True}]
    lose_songflower = [e['name'] for e in encounters].index('loatheb')
    summary = []
    for gear in gears:
        sum_dps = 0.0
        pconfig = deepcopy(config)
        pconfig['buffs']['world'].remove('sayges_dark_fortune_of_damage')
        pconfig['stats']['spell_power'][4] += gear['dsp']
        pconfig['stats']['hit_chance'][4] += gear['dhit']
        pconfig['stats']['crit_chance'][4] += gear['dcrit']

        for eindex, encounter in enumerate(encounters):
            if encounter['undead']:
                tconfig = deepcopy(pconfig) if encounter['duration'] < 140.0 else switch_trinket(pconfig, gear)
                if not gear['undead']:
                    tconfig['stats']['spell_power'][4] -= gear['dsp']
                    tconfig['stats']['hit_chance'][4] -= gear['dhit']
                    tconfig['stats']['crit_chance'][4] -= gear['dcrit']
            else:
                tconfig = deepcopy(pconfig)
                tconfig['configuration']['udc'] = []
                tconfig['stats']['spell_power'][4] = 691 + gear['dsp']
                tconfig['stats']['hit_chance'][4] = 0.10 + gear['dhit']
                tconfig['stats']['crit_chance'][4] = 0.08 + gear['dcrit'] # robe + ring
                if gear['name'] == 'inevitable':
                    tconfig['stats']['spell_power'][4] -= gear['dsp']   # no ring change
                tconfig['stats']['spell_power'][1] = 700
                tconfig['stats']['hit_chance'][1] = 0.10
                tconfig['stats']['crit_chance'][1] = 0.08
                    
            tconfig['timing']['duration'] = encounter['duration']
            tconfig["buffs"]["boss"].append(encounter['name'])
            if eindex >= lose_songflower:
                tconfig['buffs']['world'].remove('songflower_serenade')
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
    config_file = "../config/sample2.json"
    with open(config_file, 'rt') as fid:
        config = json.load(fid)
    name = os.path.split(config_file)[-1].split('.')[0]
    print('starting', name)
    #naxx_upgrade_comparison(config)
    #loatheb_stat_weights(config)
    thaddius_stat_weights(config)