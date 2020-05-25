import os
import sys
import numpy as np
import json
import itertools
from collections import OrderedDict
from sortedcontainers import SortedDict
from pathos.multiprocessing import Pool
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
from copy import deepcopy
import pickle
import time
from mechanics import get_damage

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

def all_values(obj):
    if isinstance(obj, dict):
        if 'mean' in obj:
            return all_values(obj['mean'])
        elif 'value' in obj:
            return all_values(obj['value'])
    elif isinstance(obj, list):
        return obj
    else:
        return [obj]

def num_elements(obj):
    return len(all_values(obj))

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
            return [config['rotation']['baseline']]
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

def do_plot(values, intra, inter, y_desc, plot_type, plot_name, sim_size, t0):
    sinter = SortedDict(inter)
    colors = ['purple', 'indigo', 'darkblue', 'royalblue', 'skyblue', 'green', 'lime', 'gold', 'orange', 'darkorange', 'red', 'firebrick', 'black']
    keys = []
    vals = []
    for k, vv in intra.items():
        v = all_values(vv)
        if k in ['crit_chance', 'hit_chance']:
            keys.append(k.split('_')[0])
            vals.append((100.0*np.array(v)).astype(np.int32))
        elif k == 'spell_power':
            keys.append('SP')
            vals.append(np.array(v))
        elif k == 'num_mages':
            keys.append('mages')
            vals.append(np.array([nv['num_mages'] for nv in v]))
        else:
            keys.append(k)
            vals.append(np.array(v))

    plt.close('all')
    plt.figure(figsize=(10.0, 7.0), dpi=200)
    title = ''
    fn = ''
    for k, v in sinter.items():
        if k == 'rotation':
            pass
        elif k in ['duration', 'delay']:
            title += ' {:s} = {:.1f}s'.format(k, v)
            fn += '_{:s}{:d}'.format(k[1], int(v))
        elif k in ['crit_chance', 'hit_chance']:
            title += ' {:s} = {:d}%'.format(k.split('_')[0], int(v*100))
            fn += '_{:s}{:d}'.format(k[0], int(v*100))
        elif k == 'spell_power':
            title += ' SP = {:d}'.format(int(v))
            fn += '_s{:d}'.format(int(v))
        elif k == 'single':
            title += ' single mage crit = {:d}%'.format(int(v*100))
            fn += '_m{:d}'.format(int(v*100))
        elif k == 'num_mages':
            title += ' # mages = {:d}, {:d} w/MQG, {:d} w/PI'.format(v['num_mages'], v['num_mqg'], v['num_pi'])
            fn += '_n{:d}'.format(v['num_mages'])
        
    fn += '_ss{:d}'.format(sim_size)
    plt.title(title)
    print('{:8.1f}: {:s}'.format(time.time() - t0, title))
    sys.stdout.flush()
    relabel = {
        'SP': 'Spell Power',
        'hit': 'Hit Chance (percent)',
        'crit': 'Crit Chance (percent)',
        'single': 'Single Mage Crit Chance (percent)',
        'duration': 'Duration (seconds)',
        'delay': 'Delay (seconds)',
        'mages': 'Number of Mages'}
    plt.xlabel(relabel[keys[1]])
    plt.ylabel(y_desc)
            
    for index, (lval, yval) in enumerate(zip(vals[0], values)):
        color = colors[index*len(colors)//values.shape[0]]
        plt.plot(vals[1], yval, label='{:} {:s}'.format(lval, keys[0]), color=color, marker='.')
                
    plt.legend()
    plt.grid()
    savefile = '../plots/{:s}/{:s}{:s}.png'.format(plot_type, plot_name, fn)
    os.makedirs('../plots/{:s}'.format(plot_type), exist_ok=True)
    plt.savefig(savefile)
    savefile = '../savestates/{:s}/{:s}{:s}.pck'.format(plot_type, plot_name, fn)
    os.makedirs('../savestates/{:s}'.format(plot_type), exist_ok=True)
    with open(savefile, 'wb') as fid:
        pickle.dump(values, fid)
        pickle.dump(intra, fid)
        pickle.dump(inter, fid)
        pickle.dump(sim_size, fid)
    
def main(config, name):
    ss_nm = 5 # standard number of mages for sim_size purposes
    sim_size = {
        'rotation': 50000,
        'crit_equiv': 50000,
        'hit_equiv': 100000,
        'dps': 10000,
        'test': 1000000}
    variables = {'spell_power',
                 'hit_chance',
                 'crit_chance',
                 'num_mages',
                 'duration',
                 'delay',
                 'rotation'}
    cs = config['stats']
    stats = [cs['spell_power'], cs['hit_chance'], cs['crit_chance']]
    if any(['single' in stat for stat in stats]):
        variables.add('single')
    intra_names = [config['plot']['lines'], config['plot']['x_axis']]
    inter_names = variables - set(intra_names)
    inter = OrderedDict([(iname, get_element(config, iname)) for iname in inter_names])
    intra = OrderedDict([(iname, get_element(config, iname)) for iname in intra_names])
    inter_idx = [np.arange(num_elements(element)) for element in inter.values()]
    t0 = time.time()
    for idxs in [*itertools.product(*inter_idx)]:
        inter_param = get_values(inter, idxs)
        intra_idx = [np.arange(num_elements(element)) for element in intra.values()]
        plot_type = config['plot']['y_axis']
        nom_ss = sim_size[plot_type]
        args = [{**config,
                 **inter_param,
                 **get_values(intra, jdxs)}
                for jdxs in [*itertools.product(*intra_idx)]]
        args = [{**arg, **{'sim_size': int(nom_ss*ss_nm/arg['num_mages']['num_mages'])}}
                for arg in args]

        if plot_type == "test":
            value = get_damage(args[0])
            return
        elif plot_type == "rotation":
            y_desc = 'Damage({:s})/Damage({:s})'.format(args[0]['rotation']['description'],
                                                        config['rotation']['baseline']['description'])
            with Pool() as p:
                out1 = np.array(p.map(get_damage, args))
            for index in range(len(args)):
                args[index]['rotation'] = config['rotation']['baseline']
            with Pool() as p:
                out2 = np.array(p.map(get_damage, args))
            value = out1/out2
        elif plot_type == "crit_equiv":
            y_desc = 'SP ratio'
            dcrit = 0.025
            dsp = 25.0
            factor = dsp/dcrit/100.0
            
            orig_args = deepcopy(args)
            outs = []
            for dc, ds in zip([0.0, 0.0, -dcrit, +dcrit], [-dsp, +dsp, 0.0, 0.0]):
                for index in range(len(args)):
                    args[index]['crit_chance'] = orig_args[index]['crit_chance'] + dc
                    args[index]['spell_power'] = orig_args[index]['spell_power'] + ds
                with Pool() as p:
                    out = np.array(p.map(get_damage, args))
                outs.append(out)
            value = factor*(outs[3] - outs[2])/(outs[1] - outs[0])

        value = value.reshape([len(idx) for idx in intra_idx])
        do_plot(value, intra, inter_param, y_desc, plot_type, name, nom_ss, t0)
    
if __name__ == '__main__':
    config_file = sys.argv[-1]
    with open(config_file, 'rt') as fid:
        config = json.load(fid)
    name = config_file.split('/')[-1].split('.')[0]
    main(config, name)
