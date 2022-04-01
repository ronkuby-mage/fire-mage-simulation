import os
import json
from copy import deepcopy
from mechanics import get_damage
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from scipy import optimize

VERSION = 3

def main(config, name, ret_dist=False):
    sim_size = 50000
    config["sim_size"] = sim_size
    values = get_damage(config, ret_dist=ret_dist)
    print(f"  {name}={values[0]:6.1f}")
    return values

def load_config(cfn):
    config_file = os.path.join("../config/", cfn)
    with open(config_file, 'rt') as fid:
        config = json.load(fid)
    name = os.path.split(config_file)[-1].split('.')[0]
    #print('starting', name)

    return config

def time_compare():
    confs = ["non_udc_bis_5mages_4pi.json", "udc_bis_5mages_4pi.json"]
    confs = ["non_udc_bis_4mages_4pi.json", "udc_bis_4mages_4pi.json"]
    #confs = ["udc_bis_4mages_4pi_target.json", "udc_bis_4mages_4pi_target_non.json"]
    #confs = ["udc_bis_5mages_4pi_sapp.json", "udc_bis_5mages_4pi.json"]
#    confs = ["udc_bis_5mages_4pi.json", "udc_bis_5mages_4pi_T3pants.json"]
        
    trange = list(range(30, 185, 10))
    #trange = [50]
    vals = []
    for tindex in trange:
        val = [tindex]
        for conf in confs:

            config = load_config(conf)
            #config["buffs"]["world"] = []
            config["timing"]["duration"]["mean"] = float(tindex)
            values = main(config, conf)
            val.append(values[0])
        vals.append(val)
            
    for t, a, b in vals:
        print(f"{t:3d}: {b - a:5.1f}")

def distribution():
    #confs = ["non_udc_bis_5mages_4pi.json", "udc_bis_5mages_4pi_othersnon.json"]
    confs = ["non_udc_bis_5mages_4pi.json", "udc_bis_5mages_4pi.json"]
    plt.close('all')
    plt.figure(figsize=(8.0, 5.5), dpi=200)
    plt.title('60s encounter, n=1000000, others non-udc')
    for conf in confs:
        config = load_config(conf)
        config["timing"]["duration"]["mean"] = 60.0
        #config["configuration"]["target"] = [1]
        config["buffs"]["world"] = []
        values = main(config, conf, ret_dist=True)
        print(f"  mean = {values.mean()}")
        h, x = np.histogram(values, bins=500, range=[0, 3000])
        x = (x[1:] + x[:-1])/2
        plt.plot(x, h, label=conf.split('.')[0])
    plt.xlabel('total mage dps')
    plt.ylabel('')
    plt.xlim(1300, 2000)
    plt.legend()
    plt.yticks([])
    plt.savefig("dist.png")

def simple_crit():
    config = load_config("wrap_scenario.json")
    configo = deepcopy(config)
    configo["stats"]["spell_power"][0] += 25.0
    dsp = main(configo, 'sp')[0]
    configo["stats"]["spell_power"][0] -= 50.0
    dsm = main(configo, 'sp')[0]
    configo["stats"]["spell_power"][0] += 25.0
    configo["stats"]["crit_chance"][0] += 0.01
    dcp = main(configo, 'crit')[0]
    configo["stats"]["crit_chance"][0] -= 0.02
    dcm = main(configo, 'crit')[0]
    ds = dsp - dsm
    dc = dcp - dcm
    print(f"crit(PI)={25*dc/ds:4.1f}")
    

def crit(config):
    #config["buffs"]["world"] = []
    trange = [20, 30, 40, 60, 90]
    #trange = [50]
    for tindex in trange:
        configo = deepcopy(config)
        configo["timing"]["duration"]["mean"] = float(tindex)
        configo["stats"]["spell_power"][0] += 25.0
        dsp = main(configo, 'sp')[0]
        configo["stats"]["spell_power"][0] -= 50.0
        dsm = main(configo, 'sp')[0]
        configo["stats"]["spell_power"][0] += 25.0
        configo["stats"]["crit_chance"][0] += 0.01
        dcp = main(configo, 'crit')[0]
        configo["stats"]["crit_chance"][0] -= 0.02
        dcm = main(configo, 'crit')[0]
        ds = dsp - dsm
        dc = dcp - dcm
        print(f"{tindex}s: crit(PI)={25*dc/ds:4.1f}")


def fivepi_stat_weights(config):
    #config["buffs"]["world"] = []
    trange = [30, 50, 80, 110, 150]
    #trange = [50]
    for tindex in trange:
        hit = []
        crit = []
        for pindex in [4, 5]:
            configo = deepcopy(config)
            configo["timing"]["duration"]["mean"] = float(tindex)
            configo["stats"]["spell_power"][pindex] += 25.0
            dsp = main(configo, 'sp')[0]
            configo["stats"]["spell_power"][pindex] -= 50.0
            dsm = main(configo, 'sp')[0]
            configo["stats"]["spell_power"][pindex] += 25.0
            configo["stats"]["hit_chance"][pindex] += 0.01
            dhp = main(configo, 'hit')[0]
            configo["stats"]["hit_chance"][pindex] -= 0.02
            dhm = main(configo, 'hit')[0]
            configo["stats"]["hit_chance"][pindex] += 0.01
            configo["stats"]["crit_chance"][pindex] += 0.01
            dcp = main(configo, 'crit')[0]
            configo["stats"]["crit_chance"][pindex] -= 0.02
            dcm = main(configo, 'crit')[0]
            ds = dsp - dsm
            dh = dhp - dhm
            dc = dcp - dcm
            hit.append(25*dh/ds)
            crit.append(25*dc/ds)
        print(f"{tindex}s: crit(PI)={crit[0]:4.1f} crit(no PI)={crit[1]:4.1f} hit(PI)={hit[0]:4.1f} hit(no PI)={hit[1]:4.1f}")

def twopi_stat_weights(config):
    config["buffs"]["world"] = []
    trange = [50]
    #trange = [50]
    for tindex in trange:
        hit = []
        crit = []
        for pindex in [0, 1]:
            configo = deepcopy(config)
            configo["timing"]["duration"]["mean"] = float(tindex)
            configo["stats"]["spell_power"][pindex] += 25.0
            dsp = main(configo, 'sp')[0]
            configo["stats"]["spell_power"][pindex] -= 50.0
            dsm = main(configo, 'sp')[0]
            configo["stats"]["spell_power"][pindex] += 25.0
            configo["stats"]["hit_chance"][pindex] += 0.01
            dhp = main(configo, 'hit')[0]
            configo["stats"]["hit_chance"][pindex] -= 0.02
            dhm = main(configo, 'hit')[0]
            configo["stats"]["hit_chance"][pindex] += 0.01
            configo["stats"]["crit_chance"][pindex] += 0.01
            dcp = main(configo, 'crit')[0]
            configo["stats"]["crit_chance"][pindex] -= 0.02
            dcm = main(configo, 'crit')[0]
            ds = dsp - dsm
            dh = dhp - dhm
            dc = dcp - dcm
            hit.append(25*dh/ds)
            crit.append(25*dc/ds)
        print(f"{tindex}s: crit(PI)={crit[0]:4.1f} crit(no PI)={crit[1]:4.1f} hit(PI)={hit[0]:4.1f} hit(no PI)={hit[1]:4.1f}")
    

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
    if configo["stats"]["hit_chance"][4] >= 0.09:
        configo["stats"]["spell_power"][4] += 44 + 4
        configo["stats"]["hit_chance"][4] += 0.01
        configo["stats"]["crit_chance"][4] += 0.01
    else:
        configo["stats"]["spell_power"][4] += 44
        configo["stats"]["hit_chance"][4] += 0.02
    if gear['name'] == 'eternal':
        configo["stats"]["spell_power"][4] += 9.0
    configo["configuration"]["mqg"].remove(4)

    return configo
        
def naxx_upgrade_comparison():
    config = load_config("frenzy_mqg.json")
    
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
            {'name': 'fourH', # about 3min 30sec --> get 2 combustion
             'duration': 90.0,
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
            {'name': 't3_robe',
             'dsp': 8.0,
             'dhit': 0.01,
             'dcrit': 0.0,
             'undead': False},
            {'name': 'eternal',
             'dsp': 4.0,
             'dhit': 0.0,
             'dcrit': 0.0,
             'undead': False},
            {'name': 'polarity',
             'dsp': -13.0,
             'dhit': 0.0,
             'dcrit': 0.02,
             'undead': True},
            {'name': 't3_helm',
             'dsp': 2.0,
             'dhit': 0.0,
             'dcrit': 0.01,
             'undead': True},
            {'name': 'necro_cape',
             'dsp': -4.0,
             'dhit': 0.0,
             'dcrit': 0.01,
             'undead': True},
            {'name': 'inevitable',
             'dsp': 15.0,
             'dhit': 0.0,
             'dcrit': 0.0,
             'undead': True},
            {'name': 'wraith',
             'dsp': 22.0,
             'dhit': -0.01,
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
                tconfig = deepcopy(pconfig) if encounter['duration'] < 150.0 else switch_trinket(pconfig, gear)
                if not gear['undead']:
                    tconfig['stats']['spell_power'][4] -= gear['dsp']
                    tconfig['stats']['hit_chance'][4] -= gear['dhit']
                    tconfig['stats']['crit_chance'][4] -= gear['dcrit']
            else:
                tconfig = deepcopy(pconfig)
                tconfig['configuration']['udc'] = []
                tconfig['stats']['spell_power'][4] = 694 + gear['dsp']
                tconfig['stats']['hit_chance'][4] = 0.10 + gear['dhit']
                tconfig['stats']['crit_chance'][4] = 0.09 + gear['dcrit'] # robe + ring
                if gear['name'] == 'inevitable':
                    tconfig['stats']['spell_power'][4] -= gear['dsp']   # no ring change
                if gear['name'] == 'wraith':
                    # put hit ring back on
                    tconfig['stats']['spell_power'][4] -= 9
                    tconfig['stats']['hit_chance'][4] += 0.01
                    tconfig['stats']['crit_chance'][4] -= 0.01
                    
                tconfig['stats']['spell_power'][1] = 700
                tconfig['stats']['hit_chance'][1] = 0.10
                tconfig['stats']['crit_chance'][1] = 0.08
            
            if encounter == "thaddius":
                tconfig["rotation"]["initial"]["common"] = ["scorch", "frostbolt", "combustion", "fireball", "mqg"]
                tconfig["rotation"]["continuing"]["special"]["value"] = "scorch"
                tconfig["rotation"]["continuing"]["special"]["slot"] = [0, 1, 2, 3, 4]

            
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

def naxx_stat_comparison():
    config = load_config("frenzy_ron_undead.json")
    
    
    # missing gothic, 4H, 2x spider, sapp
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
    stats = [{'dsp': 0.0,
              'dhit': 0.0,
              'dcrit': 0.0},
             {'dsp': 25.0,
              'dhit': 0.0,
              'dcrit': 0.0},
             {'dsp': 0.0,
              'dhit': 0.0,
              'dcrit': 0.025}]

    
    summary = []

    for eindex, encounter in enumerate(encounters):
        tconfig = deepcopy(config)
        #tconfig['buffs']['world'] = []
        if not encounter['undead']:
            tconfig['configuration']['udc'] = []
            tconfig['stats']['spell_power'][4] = 694
            tconfig['stats']['hit_chance'][4] = 0.10
            tconfig['stats']['crit_chance'][4] = 0.09
            tconfig['stats']['spell_power'][1] = 694
            tconfig['stats']['hit_chance'][1] = 0.10
            tconfig['stats']['crit_chance'][1] = 0.09
        
        if encounter == "thaddius":
            tconfig["rotation"]["initial"]["common"] = ["scorch", "frostbolt", "combustion", "fireball", "mqg"]
            tconfig["rotation"]["continuing"]["special"]["value"] = "scorch"
            tconfig["rotation"]["continuing"]["special"]["slot"] = [0, 1, 2, 3, 4]

        
        tconfig['timing']['duration'] = encounter['duration']
        tconfig["buffs"]["boss"].append(encounter['name'])
        
        vals = []
        for stat in stats:
            pconfig = deepcopy(tconfig)
            pconfig['buffs']['world'].remove('sayges_dark_fortune_of_damage')
            pconfig['stats']['spell_power'][4] += stat['dsp']
            pconfig['stats']['hit_chance'][4] += stat['dhit']
            pconfig['stats']['crit_chance'][4] += stat['dcrit']
            vals.append(main(pconfig, encounter['name'])[0])
        
        summary.append((encounter['name'], 10.0*(vals[2] - vals[0])/(vals[1] - vals[0])))
    for boss, value in summary:
        print(f"{boss:10s}: {value:4.1f}")


def naxx_upgrade_comparison2():
    
    # missing gothic, 4H, 2x spider, sapp
    #weighting = [('wb', 0.75), ('no_wb', 0.25)]
    weighting = [('wb', 1.00)]
    #weighting = [('no_wb', 1.00)]
    encounters = [
            {'name': 'patchwork',
             'duration': 180.0,
             'undead': True},
            {'name': 'grobbulus',
             'duration': 140.0,
             'undead': True},
            {'name': 'gluth',
             'duration': 125.0,
             'undead': True},
            {'name': 'thaddius',
             'duration': 180.0,
             'undead': True},
            {'name': 'noth',
             'duration': 180.0,
             'undead': True},
            {'name': 'heigan',
             'duration': 180.0,
             'undead': True},
            {'name': 'loatheb',
             'duration': 180.0,
             'undead': True},
            {'name': 'raz',
             'duration': 180.0,
             'undead': True},
            {'name': 'fourH', # about 3min 30sec --> get 2 combustion
             'duration': 180.0,
             'undead': True},
            {'name': 'anub',
             'duration': 160.0,
             'undead': True},
            {'name': 'kt',
             'duration': 180.0,
             'undead': True}]
    
    gears = [{'name': 'current', 'file': 'frenzy_ron_unundead.json'},
             {'name': 'inev', 'file': 'frenzy_ron_inev.json'},
             {'name': 'circ', 'file': 'frenzy_ron_circ.json'},
             {'name': 'necro', 'file': 'frenzy_ron_necro.json'},
             {'name': 'polarity', 'file': 'frenzy_ron_polarity.json'},
             {'name': 'eternal', 'file': 'frenzy_ron_eternal.json'}]
    gears = [{'name': 'soulseeker', 'file': 'frenzy_ron_soulseeker.json'},
             {'name': 'brimstone', 'file': 'frenzy_ron_brimstone.json'}]
    gears = [{'name': 'UDC', 'file': 'frenzy_ron_undead_t3pants.json'},
             {'name': 'UDC2', 'file': 'frenzy_ron_undead_t3pants_necro.json'}]
    #         {'name': 'no UDC', 'file': 'frenzy_ron_unundead_wraith.json'}]
    #gears = [{'name': 'current', 'file': 'frenzy_ron_unundead.json'},
    #         {'name': 'DSG', 'file': 'frenzy_ron_dsg.json'}]
    #gears = [{'name': 'no UDC', 'file': 'frenzy_ron_tear_unundead.json'},
    #         {'name': 'UDC', 'file': 'frenzy_ron_tear_undead.json'}]
    gears = [{'name': 'UDC bis', 'file': 'undead_bis.json'},
             {'name': 'no UDC bis', 'file': 'unundead_bis.json'}]
    gears = [{'name': 'UDC bis', 'file': 'ron_undead_bis.json'},
             {'name': 'no UDC bis', 'file': 'ron_unundead_bis.json'}]
    #gears = [{'name': 'no UDC', 'file': 'frenzy_ron_unundead.json'},
    #         {'name': 'undead wire', 'file': 'frenzy_ron_undead_wire.json'}]
    lose_songflower = [e['name'] for e in encounters].index('loatheb')
    summary = []
    for gear in gears:
        sum_dps = 0.0
        pconfig = load_config(gear['file'])

        for eindex, encounter in enumerate(encounters):
            
            #if encounter == "thaddius":
            #    tconfig["rotation"]["initial"]["common"] = ["scorch", "frostbolt", "combustion", "fireball", "mqg"]
            #    tconfig["rotation"]["continuing"]["special"]["value"] = "scorch"
            #    tconfig["rotation"]["continuing"]["special"]["slot"] = [0, 1, 2, 3, 4]
            tconfig = deepcopy(pconfig)
            
            tconfig['timing']['duration'] = encounter['duration']
            tconfig["buffs"]["boss"].append(encounter['name'])
            #if eindex >= lose_songflower:
            #    tconfig['buffs']['world'].remove('songflower_serenade')
            for name, weight in weighting:
                dconfig = deepcopy(tconfig)
                if name == 'no_wb':
                    dconfig['buffs']['world'] = []
                value = main(dconfig, encounter['name'])
                sum_dps += weight*value[0]
        summary.append((gear['name'], sum_dps/len(encounters)))
    for gear, value in summary:
        print(f"{gear:16s}: {value - summary[0][1]:6.1f}")
        #print(f"{gear:16s}: {value:6.1f}")



def naxx_player_comparison():
    config = load_config("frenzy_mqg.json")
    
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
            {'name': 'fourH', # about 3min 30sec --> get 2 combustion
             'duration': 90.0,
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
    lose_songflower = [e['name'] for e in encounters].index('loatheb')
    summary = [0.0 for index in range(config["configuration"]["num_mages"])]
    pconfig = deepcopy(config)
    pconfig['buffs']['world'].remove('sayges_dark_fortune_of_damage')

    gear = {'name': 'current',
             'dsp': 0.0,
             'dhit': 0.0,
             'dcrit': 0.0,
             'undead': True}
    for eindex, encounter in enumerate(encounters):
        if encounter['undead']:
            tconfig = deepcopy(pconfig) if encounter['duration'] < 150.0 else switch_trinket(pconfig, gear)
        else:
            tconfig = deepcopy(pconfig)
            tconfig['configuration']['udc'] = []
            tconfig['stats']['spell_power'][4] = 694
            tconfig['stats']['hit_chance'][4] = 0.10
            tconfig['stats']['crit_chance'][4] = 0.09
                
            tconfig['stats']['spell_power'][1] = 700
            tconfig['stats']['hit_chance'][1] = 0.10
            tconfig['stats']['crit_chance'][1] = 0.08

        if encounter == "thaddius":
            tconfig["rotation"]["initial"]["common"] = ["scorch", "frostbolt", "combustion", "fireball", "mqg"]
            tconfig["rotation"]["continuing"]["special"]["value"] = "scorch"
            tconfig["rotation"]["continuing"]["special"]["slot"] = [0, 1, 2, 3, 4]

                
        tconfig['timing']['duration'] = encounter['duration']
        tconfig["buffs"]["boss"].append(encounter['name'])
        if eindex >= lose_songflower:
            tconfig['buffs']['world'].remove('songflower_serenade')

        for index in range(config["configuration"]["num_mages"]):
            for name, weight in weighting:
                dconfig = deepcopy(tconfig)
                dconfig['configuration']['target'] = [index]
                if name == 'no_wb':
                    dconfig['buffs']['world'] = []
                value = main(dconfig, encounter['name'])
                summary[index] += weight*value[1]/len(encounters)
    for index, value in enumerate(summary):
        print(f"{index:d}: {value:6.1f}")

def naxx_player_comparison2():
    config = load_config("frenzy_ron_unundead.json")
    
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
            {'name': 'fourH', # about 3min 30sec --> get 2 combustion
             'duration': 90.0,
             'undead': True},
            {'name': 'anub',
             'duration': 128.0,
             'undead': True},
            {'name': 'kt',
             'duration': 180.0,
             'undead': True}]
    lose_songflower = [e['name'] for e in encounters].index('loatheb')
    summary = [0.0 for index in range(config["configuration"]["num_mages"])]
    pconfig = deepcopy(config)
    pconfig['buffs']['world'].remove('sayges_dark_fortune_of_damage')

    for eindex, encounter in enumerate(encounters):
        tconfig = deepcopy(pconfig)
                
        tconfig['timing']['duration'] = encounter['duration']
        tconfig["buffs"]["boss"].append(encounter['name'])
        if eindex >= lose_songflower:
            tconfig['buffs']['world'].remove('songflower_serenade')

        for index in range(config["configuration"]["num_mages"]):
            for name, weight in weighting:
                dconfig = deepcopy(tconfig)
                dconfig['configuration']['target'] = [index]
                if name == 'no_wb':
                    dconfig['buffs']['world'] = []
                value = main(dconfig, encounter['name'])
                summary[index] += weight*value[1]/len(encounters)
    for index, value in enumerate(summary):
        print(f"{index:d}: {value:6.1f}")
        
def naxx_simple_comparison():
    
    # missing gothic, 4H, 2x spider, sapp
    weighting = [('wb', 0.75), ('no_wb', 0.25)]
    weighting = [('wb', 1.00)]
    #weighting = [('no_wb', 1.00)]
    encounters = [
            {'name': 'patchwork',
             'duration': 80.0,
             'undead': True}]
    
    gears = [{'name': 'current', 'file': 'frenzy_ron_unundead.json'},
             {'name': 'inev', 'file': 'frenzy_ron_inev.json'},
             {'name': 'circ', 'file': 'frenzy_ron_circ.json'},
             {'name': 'necro', 'file': 'frenzy_ron_necro.json'},
             {'name': 'polarity', 'file': 'frenzy_ron_polarity.json'},
             {'name': 'eternal', 'file': 'frenzy_ron_eternal.json'}]
    gears = [{'name': 'soulseeker', 'file': 'frenzy_ron_soulseeker.json'},
             {'name': 'brimstone', 'file': 'frenzy_ron_brimstone.json'}]
    gears = [{'name': 'UDC', 'file': 'frenzy_ron_undead_t3pants.json'},
             {'name': 'UDC2', 'file': 'frenzy_ron_undead_t3pants_necro.json'}]
    #         {'name': 'no UDC', 'file': 'frenzy_ron_unundead_wraith.json'}]
    #gears = [{'name': 'current', 'file': 'frenzy_ron_unundead.json'},
    #         {'name': 'DSG', 'file': 'frenzy_ron_dsg.json'}]
    #gears = [{'name': 'no UDC', 'file': 'frenzy_ron_tear_unundead.json'},
    #         {'name': 'UDC', 'file': 'frenzy_ron_tear_undead.json'}]
    #gears = [{'name': 'UDC bis', 'file': 'undead_bis.json'},
    #         {'name': 'no UDC bis', 'file': 'unundead_bis.json'}]
    #gears = [{'name': 'UDC bis', 'file': 'ron_undead_bis.json'},
    #         {'name': 'no UDC bis', 'file': 'ron_unundead_bis.json'}]
    #gears = [{'name': 'no UDC', 'file': 'frenzy_ron_unundead.json'},y
    #         {'name': 'undead wire', 'file': 'frenzy_ron_undead_wire.json'}]
    gears = [{'name': 'simple', 'file': 'scorchfireball_all.json'},
             #{'name': 'simple2', 'file': 'scorchfireball_all2.json'},
             #{'name': 'simple3', 'file': 'scorchfireball_all3.json'},
             #{'name': 'simple4', 'file': 'scor chfireball_all4.json'},
             #{'name': 'simple nopi', 'file': 'scorchfireball_all_nopi.json'},
             #{'name': 'scorch duty', 'file': 'scorchduty_fireball.json'},
             {'name': 'frostbolt duty', 'file': 'scorchduty_frostbolt.json'},
             {'name': 'pyro', 'file': 'scorchduty_pyro.json'}]
             #{'name': 'pyro fb', 'file': 'scorchduty_pyro_fireball.json'},
             #{'name': 'pyro gcd', 'file': 'scorchduty_pyro_gcd.json'},
             #{'name': 'ff', 'file': 'fireball_frostbolt.json'}]
             #{'name': 'pyro nopi', 'file': 'scorchduty_pyro_nopi.json'},
             #{'name': 'same simple', 'file': 'same_scorchfireball_all.json'},
             #{'name': 'same simple2', 'file': 'same_scorchfireball_all2.json'},
             #{'name': 'same pyro', 'file': 'same_scorchduty_pyro.json'}]
    gears = [{'name': 'udc frostfire', 'file': 'encore_undead_fflegs.json'},
             {'name': 'udc polarity + wraith', 'file': 'encore_undead_polarity_wraith.json'},
             {'name': 'udc polarity + wraith + eye', 'file': 'encore_undead_polarity_wraith_eye.json'}]
    #gears = [{'name': 'soulseeker', 'file': 'encore_normal_ss.json'},
    #         {'name': 'wraith', 'file': 'encore_normal_wraith.json'},
    #         {'name': 'wraith + polarity', 'file': 'encore_normal_wraith_polarity.json'},
    #         {'name': 'wraith + polarity + dsg + sh', 'file': 'encore_normal_wraith_polarity_dsg_sh.json'},
    #         {'name': 'wraith + polarity + dsg + sh + eye', 'file': 'encore_normal_wraith_polarity_dsg_sh_eye.json'}]
    gears = [{'name': 'udc mqg', 'file': 'encore_undead_mqg.json'},
             {'name': 'udc mqg + polarity + wraith + eye + fates', 'file': 'encore_undead_mqg_polarity_wraith_eye_fates.json'}]
    gears = [{'name': 'nowb soulseeker', 'file': 'encore_undead_nowb_1.json'},
             {'name': 'nowb brimstone', 'file': 'encore_undead_nowb_2.json'}]
    gears = [{'name': 'no T3', 'file': 'encore_no_T3.json'},
             {'name': '8/8 T3', 'file': 'encore_8_T3.json'}]
    gears = [{'name': 'no buffer', 'file': 'encore_buffer_no.json'},
             {'name': 'buffer', 'file': 'encore_buffer_yes.json'}]
    gears = [{'name': 'no udc', 'file': 'encore_pi_noudc.json'},
             {'name': 'udc', 'file': 'encore_pi_udc.json'}]
    #gears = [{'name': 'no udc', 'file': 'encore_noudc.json'},
    #         {'name': 'udc', 'file': 'encore_udc.json'}]
    gears = [{'name': 'udc_T3', 'file': 'encore_udc_T3.json'},
             {'name': 'udc_polarity', 'file': 'encore_udc_polarity.json'}]
    gears = [{'name': 'udc_polarity', 'file': 'encore_udc_polarity.json'},
             {'name': 'udc_polarity_sapp', 'file': 'encore_udc_polarity_sapp.json'}]
    #gears = [{'name': 'udc_polarity_sapp', 'file': 'encore_udc_polarity_sapp.json'}]
    gears = [{'name': 'som_toep', 'file': 'som_TOEP.json'},
             {'name': 'som_zhc', 'file': 'som_ZHC.json'},]
    #gears = [{'name': 'udc_polarity', 'file': 'encore_udc_polarity.json'},
    #         {'name': 'udc_98hit', 'file': 'encore_udc_98hit.json'}]
    #gears = [{'name': 'wb soulseeker', 'file': 'encore_undead_slowwb_1.json'},
    #         {'name': 'wb brimstone', 'file': 'encore_undead_slowwb_2.json'}]
             
             
    summary = []
    for gear in gears:
        sum_dps = 0.0
        pconfig = load_config(gear['file'])

        for eindex, encounter in enumerate(encounters):
            
            #if encounter == "thaddius":
            #    tconfig["rotation"]["initial"]["common"] = ["scorch", "frostbolt", "combustion", "fireball", "mqg"]
            #    tconfig["rotation"]["continuing"]["special"]["value"] = "scorch"
            #    tconfig["rotation"]["continuing"]["special"]["slot"] = [0, 1, 2, 3, 4]
            tconfig = deepcopy(pconfig)
            
            tconfig['timing']['duration'] = encounter['duration']
            tconfig["buffs"]["boss"].append(encounter['name'])
            #if eindex >= lose_songflower:
            #    tconfig['buffs']['world'].remove('songflower_serenade')
            for name, weight in weighting:
                dconfig = deepcopy(tconfig)
                if name == 'no_wb':
                    dconfig['buffs']['world'] = []
                value = main(dconfig, encounter['name'])
                sum_dps += weight*value[0]
        summary.append((gear['name'], sum_dps/len(encounters)))
    for gear, value in summary:
        print(f"{gear:16s}: {value - summary[0][1]:6.1f}")
        #print(f"{gear:16s}: {value:6.1f}")

class mage_state():
    
    def __init__(self, num_mages, num_pi, wb=True):
    
        if wb:
            self._weighting = [('wb', 1.00)]
        else:
            self._weighting = [('no_wb', 1.00)]

        self._gears = [{'name': 'simple', 'file': 'scorchfireball_all_12.json'},
                       {'name': 'frostbolt', 'file': 'scorchduty_frostbolt_12.json'}]
        self._num_mages = num_mages
        self._num_pi = num_pi

    def rot_diff(self, etime):
        num_mages = self._num_mages
        num_pi = self._num_pi
        weighting = self._weighting
        encounters = [
                {'name': 'patchwork',
                 'duration': etime,
                 'undead': True}]

        truncate = [("stats", "spell_power"),
                    ("stats", "hit_chance"),
                    ("stats", "crit_chance"),
                    ("stats", "intellect"),
                    ("buffs", "racial")]
        cull = [("configuration", "target"),
                ("configuration", "mqg"),
                ("configuration", "sapp"),
                ("configuration", "udc")]

        dps = []
        for gear in self._gears:
            pconfig = load_config(gear['file'])
            sum_dps = 0.0
            for eindex, encounter in enumerate(encounters):
                #if encounter == "thaddius":
                #    tconfig["rotation"]["initial"]["common"] = ["scorch", "frostbolt", "combustion", "fireball", "mqg"]
                #    tconfig["rotation"]["continuing"]["special"]["value"] = "scorch"
                #    tconfig["rotation"]["continuing"]["special"]["slot"] = [0, 1, 2, 3, 4]
                tconfig = deepcopy(pconfig)
                tconfig['configuration']['num_mages'] = num_mages
                for t1, t2 in truncate:
                    tconfig[t1][t2] = tconfig[t1][t2][:num_mages]
                for c1, c2 in cull:
                    tconfig[c1][c2] = [val for val in tconfig[c1][c2] if val < num_mages]
                tconfig["configuration"]["pi"] = list(range(num_mages - num_pi, num_mages))
                
                tconfig['timing']['duration'] = encounter['duration']
                tconfig["buffs"]["boss"].append(encounter['name'])
                #if eindex >= lose_songflower:
                #    tconfig['buffs']['world'].remove('songflower_serenade')
                for name, weight in weighting:
                    dconfig = deepcopy(tconfig)
                    if name == 'no_wb':
                        dconfig['buffs']['world'] = []
                    value = main(dconfig, encounter['name'])
                    sum_dps += weight*value[0]
            dps.append(sum_dps/len(encounters))
        
        return (dps[1] - dps[0])/dps[0]


def time_clown():
    bounds = [20.0, 150.0]

    fid = open("at90_nwb.csv", "wt")
    for num_mages in range(3, 11):
        for num_pi in range(0, 6):
            print("    starting", num_mages, num_pi)
            if num_pi > num_mages:
                continue
            state = mage_state(num_mages, num_pi, wb=False)
            dif90 = state.rot_diff(90.0)
            print(f"    {num_mages:d} {num_pi:d} {100*dif90:5.2f}")
            fid.write(f"{num_mages:d},{num_pi:d},{200*dif90:5.2f}\n")
            #if state.rot_diff(bounds[0] - 10.0) >= 0.0:
            #    eq_tim = 0.0
            #elif state.rot_diff(bounds[1] + 50.0) <= 5.0:w
            #    eq_tim = 600.0
            #else:
            #    rr = optimize.root_scalar(state.rot_diff, bracket=bounds, xtol=1.0)
            #    eq_tim = rr.root
            #print(f"    {num_mages:d} {num_pi:d} {eq_tim:5.1f}")
            #fid.write(f"{num_mages:d},{num_pi:d},{eq_tim:5.1f}\n")
    fid.close()


def naxx_new_buff():
    
    # missing gothic, 4H, 2x spider, sapp
    #weighting = [('wb', 0.75), ('no_wb', 0.25)]
    weighting = [('wb', 1.00)]
    #weighting = [('no_wb', 1.00)]
    encounters = [
            {'name': 'patchwork',
             'duration': 150.0,
             'undead': True}]
    
    gears = [{'name': 'simple', 'file': 'scorchfireball_all_12.json'},
             {'name': 'frostbolt', 'file': 'scorchduty_frostbolt_12.json'},
             {'name': 'pyro', 'file': 'scorchduty_pyro_12.json'}]
             #{'name': 'pyro nopi', 'file': 'scorchduty_pyro_nopi.json'},
             #{'name': 'same simple', 'file': 'same_scorchfireball_all.json'},
             #{'name': 'same simple2', 'file': 'same_scorchfireball_all2.json'},
             #{'name': 'same pyro', 'file': 'same_scorchduty_pyro.json'}]
             
    truncate = [("stats", "spell_power"),
               ("stats", "hit_chance"),
               ("stats", "crit_chance"),
               ("stats", "intellect"),
               ("buffs", "racial")]
    cull = [("configuration", "target"),
            ("configuration", "mqg"),
            ("configuration", "sapp"),
            ("configuration", "udc")]

    fid = open("big_out.csv", "wt")


    for num_mages in range(4, 11):
        for num_pi in range(1, 6):               
            summary = []
            for gear in gears:
                sum_dps = 0.0
                pconfig = load_config(gear['file'])
        
                for eindex, encounter in enumerate(encounters):
                    
                    #if encounter == "thaddius":
                    #    tconfig["rotation"]["initial"]["common"] = ["scorch", "frostbolt", "combustion", "fireball", "mqg"]
                    #    tconfig["rotation"]["continuing"]["special"]["value"] = "scorch"
                    #    tconfig["rotation"]["continuing"]["special"]["slot"] = [0, 1, 2, 3, 4]
                    tconfig = deepcopy(pconfig)
                    tconfig['configuration']['num_mages'] = num_mages
                    for t1, t2 in truncate:
                        tconfig[t1][t2] = tconfig[t1][t2][:num_mages]
                    for c1, c2 in cull:
                        tconfig[c1][c2] = [val for val in tconfig[c1][c2] if val < num_mages]
                    tconfig["configuration"]["pi"] = list(range(num_mages - num_pi, num_mages))
                    
                    tconfig['timing']['duration'] = encounter['duration']
                    tconfig["buffs"]["boss"].append(encounter['name'])
                    #if eindex >= lose_songflower:
                    #    tconfig['buffs']['world'].remove('songflower_serenade')
                    for name, weight in weighting:
                        dconfig = deepcopy(tconfig)
                        if name == 'no_wb':
                            dconfig['buffs']['world'] = []
                        value = main(dconfig, encounter['name'])
                        sum_dps += weight*value[0]
                    fid.write(f"{num_mages:d},{num_pi:d},{gear['name']:s},{sum_dps/len(encounters):6.1f}\r\n")
                summary.append((gear['name'], sum_dps/len(encounters)))
            for gear, value in summary:
                print(f"{num_mages:d} mages {gear:16s} {value:6.1f}")
                #print(f"{gear:16s}: {value:6.1f}")
    fid.close()

def time_comparison():
    
    gears = [{'name': 'Tear + Sapp', 'file': 'encore_undead_tear.json'},
             {'name': 'MQG + Sapp', 'file': 'encore_undead_twoactive.json'},
             {'name': 'MQG + Mark', 'file': 'encore_undead_mqgmark.json'},
             {'name': 'Sapp + Mark', 'file': 'encore_undead_sappmark.json'},
             {'name': 'Tear + Mark', 'file': 'encore_undead_tearmark.json'},
             {'name': 'MQG + Tear', 'file': 'encore_undead_mqgtear.json'}]
    #gears = [{'name': 'Sapp + Mark', 'file': 'encore_undead_sappmark.json'}]

    configs = [(gear['name'], load_config(gear['file'])) for gear in gears]
    out = [[] for dummy in range(len(configs))]

    etimes = np.array(list(range(25, 76, 3)) + list(range(80, 251, 10)))
    #etimes = np.array([100.0])
    for etime in etimes:
        for index, config in enumerate(configs):
            tconfig = deepcopy(config[1])
            #tconfig['buffs']['world'] = []
            tconfig['timing']['duration'] = {
                    "mean": etime,
                    "var": 3.0,
                    "clip": [0.0, 10000.0]}
            value = main(tconfig, config[0])
            out[index].append(value[0])
            
    plt.close('all')
    plt.figure(figsize=(8.0, 5.5), dpi=200)
    plt.title('{# mages = 5, world buffs, no PI}')
    for conf, ou in zip(configs, out):
        plt.plot(etimes, np.array(ou), label=conf[0])
    plt.xlabel('Encounter Duration (seconds)')
    plt.ylabel('Average DPS')
    plt.xlim(0, 250)
    plt.legend()
    plt.savefig("Trinkets_undead.png")


if __name__ == '__main__':
    #simple_crit()
    #time_compare()
    #distribution()
    #config_file = "../config/solo_group_lim_wb.json"
    #with open(config_file, 'rt') as fid:
    #    config = json.load(fid)
    #name = os.path.split(config_file)[-1].split('.')[0]
    #print('starting', name)
    #naxx_upgrade_comparison2()
    #naxx_stat_comparison()
    #naxx_player_comparison2()
    #loatheb_stat_weights(config)
    #thaddius_stat_weights(config)
    #fivepi_stat_weights(config)
    #twopi_stat_weights(config)
    #crit(config)
    #naxx_simple_comparison()
    #naxx_new_buff()
    time_comparison()
    