import os
import numpy as np
import json
import itertools
from collections import OrderedDict
from pathos.multiprocessing import Pool
from copy import deepcopy
import time
from mechanics import Encounter
import plots
import constants


def get_values(objs, idxs):
    ret = {}
    for idx, (name, obj) in zip(idxs, objs.items()):
        if isinstance(obj, dict):
            if 'mean' in obj:
                ret[name] = get_values({name: obj['mean']}, [idx])[name]
            elif 'value' in obj:
                ret[name] = get_values({name: obj['value']}, [idx])[name]
        elif isinstance(obj, list):
            ret[name] = obj[idx]
        else:
            ret[name] = obj

    return ret

def num_elements(obj):
    if isinstance(obj, dict):
        if 'mean' in obj:
            return num_elements(obj['mean'])
        elif 'value' in obj:
            return num_elements(obj['value'])
    elif isinstance(obj, list):
        return len(obj)
    else:
        return 1

def get_element(config, var):
    if var == 'spell_power':
        return config['stats']['spell_power']
    elif var == 'hit_chance':
        return config['stats']['hit_chance']
    elif var == 'crit_chance':
        return config['stats']['crit_chance']
    elif var == 'num_mages':
        return config['configuration']
    elif var == 'rotation':
        if 'compare' in config['rotation']:
            return config['rotation']['compare']
        else:
            return config['rotation']['baseline']
    elif var == 'duration':
        return config['timing']['duration']
    elif var == 'delay':
        return config['timing']['delay']
    elif var == 'single':
        cs = config['stats']
        stats = [cs['spell_power'], cs['hit_chance'], cs['crit_chance']]
        for stat in stats:
            if 'single' in stat:
                return stat['single']
    else:
        raise ValueError("Unknown variable.")

def main(config):
    variables = {'spell_power',
                 'hit_chance',
                 'crit_chance',
                 'num_mages',
                 'duration',
                 'delay'}
    cs = config['stats']
    stats = [cs['spell_power'], cs['hit_chance'], cs['crit_chance']]
    if any(['single' in stat for stat in stats]):
        variables.add('single')
    intra_names = set(config['plot'].values())
    inter_names = variables - intra_names
    #intra_names.discard('rotation')
    #inter_names.add('rotation')
    inter = OrderedDict([(iname, get_element(config, iname)) for iname in inter_names])
    intra = OrderedDict([(iname, get_element(config, iname)) for iname in intra_names])
    inter_idx = [np.arange(num_elements(element)) for element in inter.values()]
    for idxs in [*itertools.product(*inter_idx)]:
        inter_param = get_values(inter, idxs)
        intra_idx = [np.arange(num_elements(element)) for element in intra.values()]
        args = [{**config, **inter_param, **get_values(intra, jdxs)} for jdxs in [*itertools.product(*intra_idx)]]

        if config['plot']['x_axis'] == "rotation":
            pass
            
        for key, val in args[0].items():
            print(key)
        #print(args[0])
        
        #print(intra_param)
    #print(intra)

    sajiodjj()
    
    
    print(get_damage(700.0, 0.970, 0.150, 6, 1.0, 100000))
    t0 = time.time()
    C = constants.Constant()
    
    spell_damage = np.arange(C._SP_START, C._SP_END + C._SP_STEP/2.0, C._SP_STEP)
    crit_chance = np.arange(C._CRIT_START, C._CRIT_END + C._CRIT_STEP/2.0, C._CRIT_STEP)
    hit = 0.95
    num_mages = 6
    
    hits = np.array([hit])
    mages = np.array([num_mages])
    sim_size = C._CRIT_SIMSIZE*5/num_mages
    sim_size = np.array([sim_size]).astype(np.int32)
    responses = np.array([C._INITIAL_SIGMA])

    args = itertools.product(spell_damage, hits, crit_chance, mages, responses, sim_size)
    largs = [*args]

    print('Hit = {:2.0f} # mages = {:d}'.format(100.0*hit, num_mages))
    with Pool() as p:
        out = np.array(p.starmap(get_crit_damage_diff, largs)).reshape((len(spell_damage), len(hits), len(crit_chance), len(mages), len(responses), len(sim_size)))
    conversions = np.squeeze(out)

    plots.plot_equiv(spell_damage, crit_chance, conversions, hit, num_mages, sim_size[0], C._DURATION_AVERAGE, 'crit')

    print(time.time() - t0)
    
if __name__ == '__main__':
    config_file = 'config/scorch.json'
    with open(config_file, 'rt') as fid:
        config = json.load(fid)
    main(config)
